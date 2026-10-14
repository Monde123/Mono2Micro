"""Milestone 2 (M2) Tests: AST Dependency Graph & Data Boundary Analysis.

Acceptance criteria:
- Graph exported (JSON + readable schema)
- Proposed partitions with modularity, coupling ratio, shared tables count
- Pure offline operation (works without LLM)
- Supports Python, JS/TS, Java MyBatis XML, JPA, and SQL migrations
"""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from mono2micro.cli import app
from mono2micro.analysis.ast_analyzer import ASTAnalyzer
from mono2micro.analysis.data_analyzer import DataAnalyzer
from mono2micro.analysis.graph_engine import GraphEngine
from mono2micro.core.orchestrator import MigrationOrchestrator


runner = CliRunner()


def _setup_multi_domain_repo(tmp_path: Path):
    # Domain 1: Billing
    billing_dir = tmp_path / "billing"
    billing_dir.mkdir(parents=True, exist_ok=True)
    (billing_dir / "invoice.py").write_text(
        "class Invoice:\n"
        "    def calculate_total(self):\n"
        "        return 100\n"
        "def bill_customer():\n"
        "    query = 'SELECT * FROM invoices JOIN accounts ON invoices.acc_id = accounts.id'\n"
        "    return Invoice().calculate_total()\n"
    )

    # Domain 2: Auth / Accounts
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir(parents=True, exist_ok=True)
    (auth_dir / "account.py").write_text(
        "class Account:\n"
        "    pass\n"
        "def verify_login():\n"
        "    query = 'SELECT id, password FROM accounts WHERE active = 1'\n"
        "    return True\n"
    )

    # Cross-domain call from Orders to Billing and Auth
    orders_dir = tmp_path / "orders"
    orders_dir.mkdir(parents=True, exist_ok=True)
    (orders_dir / "order_service.py").write_text(
        "from billing.invoice import bill_customer\n"
        "from auth.account import verify_login\n"
        "def place_order():\n"
        "    verify_login()\n"
        "    bill_customer()\n"
        "    sql = 'INSERT INTO orders (id) VALUES (1)'\n"
    )

    # MyBatis XML mapper in resource
    res_dir = tmp_path / "resources"
    res_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / "OrderMapper.xml").write_text(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<mapper namespace=\"com.example.OrderMapper\">\n"
        "  <select id=\"selectOrder\" resultType=\"Order\">\n"
        "    SELECT * FROM orders WHERE id = #{id}\n"
        "  </select>\n"
        "</mapper>\n"
    )

    # SQL schema file
    sql_dir = tmp_path / "db"
    sql_dir.mkdir(parents=True, exist_ok=True)
    (sql_dir / "schema.sql").write_text(
        "CREATE TABLE invoices (id INT PRIMARY KEY, acc_id INT);\n"
        "CREATE TABLE accounts (id INT PRIMARY KEY, email VARCHAR(255));\n"
        "CREATE TABLE orders (id INT PRIMARY KEY, customer_id INT);\n"
        "ALTER TABLE invoices ADD CONSTRAINT fk_acc FOREIGN KEY (acc_id) REFERENCES accounts(id);\n"
    )


def test_m2_ast_analyzer_extracts_nodes_and_edges(tmp_path):
    _setup_multi_domain_repo(tmp_path)
    analyzer = ASTAnalyzer(str(tmp_path))
    nodes, edges = analyzer.analyze_file("billing/invoice.py")

    assert any(n.name == "Invoice" for n in nodes)
    assert any(n.name == "invoice.py" for n in nodes)


def test_m2_data_analyzer_extracts_sql_and_mybatis(tmp_path):
    _setup_multi_domain_repo(tmp_path)
    analyzer = DataAnalyzer(str(tmp_path))
    report = analyzer.analyze()

    assert "invoices" in report.tables_detected
    assert "accounts" in report.tables_detected
    assert "orders" in report.tables_detected
    assert report.mybatis_mappers_count >= 1
    assert any(fk.target_table == "accounts" for fk in report.foreign_keys)


def test_m2_graph_engine_exports_json_and_computes_modularity(tmp_path):
    _setup_multi_domain_repo(tmp_path)
    engine = GraphEngine(str(tmp_path))
    graph = engine.build_graph()

    assert graph.node_count >= 5
    assert graph.edge_count >= 3

    # Export graph
    export_path = tmp_path / ".mono2micro" / "dependency_graph.json"
    engine.export_graph_json(graph, str(export_path))
    assert export_path.exists()

    with open(export_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["$schema"] == "https://mono2micro.dev/schemas/dependency-graph.v1.json"
    assert "nodes" in data
    assert "edges" in data

    # Louvain clustering & evaluation
    eval_result = engine.cluster_louvain(graph)
    assert len(eval_result.partitions) >= 2
    # Accounts table is accessed by billing and auth -> shared table
    assert "accounts" in eval_result.shared_tables_detail
    assert eval_result.shared_tables_count >= 1


def test_m2_cli_graph_command(tmp_path):
    _setup_multi_domain_repo(tmp_path)
    res = runner.invoke(app, ["graph", "--path", str(tmp_path)])
    assert res.exit_code == 0
    assert "Offline Structural Partitions & Modularity" in res.stdout
    assert "Modularity Q:" in res.stdout
    assert "Shared Tables Count:" in res.stdout
    assert (tmp_path / ".mono2micro" / "dependency_graph.json").exists()
    assert (tmp_path / ".mono2micro" / "partitions.json").exists()
