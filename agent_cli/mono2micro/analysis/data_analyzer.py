"""Data layer, SQL, MyBatis, JPA, and transaction boundary analyzer."""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from mono2micro.models.data_analysis import (
    DataLayerAnalysis,
    ForeignKeyRelation,
    PersistenceMechanism,
    TableAccessOperation,
    TableAccessRecord,
    TransactionScope,
)


class DataAnalyzer:
    """Extracts tables, SQL queries, MyBatis mappers, JPA entities, and transaction scopes."""

    def __init__(self, root_dir: str):
        self.root_dir = str(Path(root_dir).resolve())

    def analyze(self) -> DataLayerAnalysis:
        tables_detected: Set[str] = set()
        table_accesses: List[TableAccessRecord] = []
        foreign_keys: List[ForeignKeyRelation] = []
        transactions: List[TransactionScope] = []
        mybatis_count = 0
        jpa_count = 0
        raw_sql_count = 0

        # Scan files
        for root, _, files in os.walk(self.root_dir):
            if any(p in root.split(os.sep) for p in (".git", "node_modules", "dist", "build", "venv", ".mono2micro")):
                continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.root_dir).replace("\\", "/")
                full_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                # 1. XML MyBatis mappers
                if ext == ".xml":
                    mb_tables, mb_acc = self._parse_mybatis_xml(full_path, rel_path)
                    if mb_tables:
                        mybatis_count += 1
                        tables_detected.update(mb_tables)
                        table_accesses.extend(mb_acc)

                # 2. Java JPA Entities and transactions
                elif ext == ".java":
                    jpa_tbls, jpa_acc, jpa_fks = self._parse_jpa_file(full_path, rel_path)
                    if jpa_tbls:
                        jpa_count += len(jpa_tbls)
                        tables_detected.update(jpa_tbls)
                        table_accesses.extend(jpa_acc)
                        foreign_keys.extend(jpa_fks)

                    txs = self._detect_java_transactions(full_path, rel_path)
                    transactions.extend(txs)

                # 3. Python files (SQLAlchemy, Django, raw SQL)
                elif ext == ".py":
                    py_tbls, py_acc, py_fks, py_sql_cnt = self._parse_python_sql(full_path, rel_path)
                    raw_sql_count += py_sql_cnt
                    tables_detected.update(py_tbls)
                    table_accesses.extend(py_acc)
                    foreign_keys.extend(py_fks)

                    txs = self._detect_python_transactions(full_path, rel_path)
                    transactions.extend(txs)

                # 4. SQL migration and DDL files
                elif ext == ".sql":
                    sql_tbls, sql_acc, sql_fks = self._parse_raw_sql_file(full_path, rel_path)
                    raw_sql_count += 1
                    tables_detected.update(sql_tbls)
                    table_accesses.extend(sql_acc)
                    foreign_keys.extend(sql_fks)

        return DataLayerAnalysis(
            tables_detected=sorted(tables_detected),
            table_accesses=table_accesses,
            foreign_keys=foreign_keys,
            transactions=transactions,
            mybatis_mappers_count=mybatis_count,
            jpa_entities_count=jpa_count,
            raw_sql_queries_count=raw_sql_count,
        )

    def _parse_mybatis_xml(self, abs_path: str, rel_path: str) -> Tuple[Set[str], List[TableAccessRecord]]:
        tables: Set[str] = set()
        accesses: List[TableAccessRecord] = []
        try:
            tree = ET.parse(abs_path)
            root = tree.getroot()
            if root.tag != "mapper":
                return tables, accesses

            for elem in root:
                text = (elem.text or "") + "".join(elem.itertext())
                found_tables, found_acc = self._extract_sql_tables(text, rel_path)
                tables.update(found_tables)
                accesses.extend(found_acc)
        except Exception:
            pass
        return tables, accesses

    def _parse_jpa_file(self, abs_path: str, rel_path: str) -> Tuple[Set[str], List[TableAccessRecord], List[ForeignKeyRelation]]:
        tables: Set[str] = set()
        accesses: List[TableAccessRecord] = []
        fks: List[ForeignKeyRelation] = []

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if "@Entity" in content:
                tbl_match = re.search(r'@Table\s*\(\s*name\s*=\s*["\']([a-zA-Z0-9_]+)["\']', content)
                table_name = tbl_match.group(1) if tbl_match else ""
                if not table_name:
                    cls_match = re.search(r'class\s+([A-Za-z0-9_]+)', content)
                    if cls_match:
                        table_name = cls_match.group(1).lower()

                if table_name:
                    tables.add(table_name)
                    accesses.append(TableAccessRecord(
                        table_name=table_name,
                        operation=TableAccessOperation.SCHEMA_DEFINITION,
                        file_path=rel_path,
                    ))

                # Foreign keys via @JoinColumn
                for fk_match in re.finditer(r'@JoinColumn\s*\(\s*name\s*=\s*["\']([a-zA-Z0-9_]+)["\']', content):
                    fks.append(ForeignKeyRelation(
                        source_table=table_name or "unknown",
                        source_column=fk_match.group(1),
                        target_table="",
                        target_column="id",
                        file_path=rel_path,
                    ))

        except Exception:
            pass
        return tables, accesses, fks

    def _parse_python_sql(self, abs_path: str, rel_path: str) -> Tuple[Set[str], List[TableAccessRecord], List[ForeignKeyRelation], int]:
        tables: Set[str] = set()
        accesses: List[TableAccessRecord] = []
        fks: List[ForeignKeyRelation] = []
        raw_sql_cnt = 0

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # SQLAlchemy / Django __tablename__
            for match in re.finditer(r'__tablename__\s*=\s*["\']([a-zA-Z0-9_]+)["\']', content):
                tbl = match.group(1)
                tables.add(tbl)
                accesses.append(TableAccessRecord(
                    table_name=tbl,
                    operation=TableAccessOperation.SCHEMA_DEFINITION,
                    file_path=rel_path,
                ))

            # Raw SQL queries
            raw_tables, raw_acc = self._extract_sql_tables(content, rel_path)
            if raw_tables:
                raw_sql_cnt += len(raw_tables)
                tables.update(raw_tables)
                accesses.extend(raw_acc)

        except Exception:
            pass
        return tables, accesses, fks, raw_sql_cnt

    def _parse_raw_sql_file(self, abs_path: str, rel_path: str) -> Tuple[Set[str], List[TableAccessRecord], List[ForeignKeyRelation]]:
        tables: Set[str] = set()
        accesses: List[TableAccessRecord] = []
        fks: List[ForeignKeyRelation] = []

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # CREATE TABLE
            for match in re.finditer(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[`"\[]?([a-zA-Z0-9_]+)[`"\]]?\.)?[`"\[]?([a-zA-Z0-9_]+)[`"\]]?', content, re.IGNORECASE):
                tbl = match.group(2) or match.group(1)
                if tbl:
                    tables.add(tbl.lower())
                    accesses.append(TableAccessRecord(
                        table_name=tbl.lower(),
                        operation=TableAccessOperation.SCHEMA_DEFINITION,
                        file_path=rel_path,
                    ))

            # Foreign keys: FOREIGN KEY (col) REFERENCES target_table(col)
            for fk_match in re.finditer(r'FOREIGN\s+KEY\s*\([`"\[]?([a-zA-Z0-9_]+)[`"\]]?\)\s*REFERENCES\s*[`"\[]?([a-zA-Z0-9_]+)[`"\]]?', content, re.IGNORECASE):
                fks.append(ForeignKeyRelation(
                    source_table="",
                    source_column=fk_match.group(1),
                    target_table=fk_match.group(2).lower(),
                    target_column="id",
                    file_path=rel_path,
                ))

            extra_tables, extra_acc = self._extract_sql_tables(content, rel_path)
            tables.update(extra_tables)
            accesses.extend(extra_acc)
        except Exception:
            pass

        return tables, accesses, fks

    def _extract_sql_tables(self, text: str, rel_path: str) -> Tuple[Set[str], List[TableAccessRecord]]:
        tables: Set[str] = set()
        accesses: List[TableAccessRecord] = []

        patterns = [
            (r'\bFROM\s+([a-zA-Z0-9_]+)', TableAccessOperation.READ),
            (r'\bJOIN\s+([a-zA-Z0-9_]+)', TableAccessOperation.JOIN),
            (r'\bINSERT\s+INTO\s+([a-zA-Z0-9_]+)', TableAccessOperation.WRITE),
            (r'\bUPDATE\s+([a-zA-Z0-9_]+)', TableAccessOperation.WRITE),
            (r'\bDELETE\s+FROM\s+([a-zA-Z0-9_]+)', TableAccessOperation.WRITE),
        ]

        for pat, op in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                candidate = match.group(1).lower()
                if candidate not in ("where", "select", "set", "inner", "left", "right", "outer", "group", "order", "values"):
                    tables.add(candidate)
                    accesses.append(TableAccessRecord(
                        table_name=candidate,
                        operation=op,
                        file_path=rel_path,
                        query_fragment=match.group(0),
                    ))

        return tables, accesses

    def _detect_java_transactions(self, abs_path: str, rel_path: str) -> List[TransactionScope]:
        scopes: List[TransactionScope] = []
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for idx, line in enumerate(lines, 1):
                if "@Transactional" in line:
                    method_name = "annotated_method"
                    if idx < len(lines):
                        m_match = re.search(r'(?:public|protected|private)\s+.*?\s+([A-Za-z0-9_]+)\s*\(', lines[idx])
                        if m_match:
                            method_name = m_match.group(1)
                    scopes.append(TransactionScope(
                        scope_id=f"tx:{rel_path}:{idx}",
                        file_path=rel_path,
                        function_or_method=method_name,
                        line_number=idx,
                    ))
        except Exception:
            pass
        return scopes

    def _detect_python_transactions(self, abs_path: str, rel_path: str) -> List[TransactionScope]:
        scopes: List[TransactionScope] = []
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for idx, line in enumerate(lines, 1):
                if "transaction.atomic()" in line or "@transaction.atomic" in line:
                    scopes.append(TransactionScope(
                        scope_id=f"tx:{rel_path}:{idx}",
                        file_path=rel_path,
                        function_or_method="atomic_block",
                        line_number=idx,
                    ))
        except Exception:
            pass
        return scopes
