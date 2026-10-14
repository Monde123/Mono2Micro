"""Database, SQL, MyBatis, and transaction boundary analysis contracts.

Analyzes persistence layers offline (M2):
- SQL table references (SELECT, INSERT, UPDATE, DELETE, JOIN)
- MyBatis XML mapper tags (<select>, <insert>, <resultMap>)
- JPA/Hibernate annotations (@Entity, @Table, @ManyToOne)
- Foreign keys and cross-domain references
- Transaction boundaries (@Transactional, COMMIT, BEGIN)
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class PersistenceMechanism(str, Enum):
    RAW_SQL = "RAW_SQL"
    MYBATIS_XML = "MYBATIS_XML"
    JPA_HIBERNATE = "JPA_HIBERNATE"
    SQLALCHEMY = "SQLALCHEMY"
    PRISMA_OR_TYPEORM = "PRISMA_OR_TYPEORM"
    DJANGO_ORM = "DJANGO_ORM"
    UNKNOWN = "UNKNOWN"


class TableAccessOperation(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    JOIN = "JOIN"
    SCHEMA_DEFINITION = "SCHEMA_DEFINITION"


class TableAccessRecord(BaseModel):
    table_name: str
    operation: TableAccessOperation
    file_path: str
    line_number: Optional[int] = None
    query_fragment: Optional[str] = None
    in_transaction: bool = False


class ForeignKeyRelation(BaseModel):
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class TransactionScope(BaseModel):
    scope_id: str
    file_path: str
    function_or_method: str
    line_number: Optional[int] = None
    tables_accessed: List[str] = Field(default_factory=list)
    spans_multiple_domains: bool = False
    domains_involved: List[str] = Field(default_factory=list)


class DataLayerAnalysis(BaseModel):
    """Aggregate data analysis report."""
    tables_detected: List[str] = Field(default_factory=list)
    table_accesses: List[TableAccessRecord] = Field(default_factory=list)
    foreign_keys: List[ForeignKeyRelation] = Field(default_factory=list)
    transactions: List[TransactionScope] = Field(default_factory=list)
    mybatis_mappers_count: int = 0
    jpa_entities_count: int = 0
    raw_sql_queries_count: int = 0
    shared_tables_between_domains: Dict[str, List[str]] = Field(default_factory=dict)
    cross_domain_transactions: List[TransactionScope] = Field(default_factory=list)
