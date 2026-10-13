"""Tests for SafeRepoScanner in read-only mode."""

import tempfile
import os
from pathlib import Path
from mono2micro.tools.repo_scanner import SafeRepoScanner
from mono2micro.models.discovery import ComponentType, FactEvidenceType


def test_scanner_on_empty_directory():
    with tempfile.TemporaryDirectory() as tmp:
        scanner = SafeRepoScanner(tmp)
        report = scanner.scan()
        assert report.total_files_scanned == 0
        assert len(report.verified_facts) == 0
        assert len(report.analysis_limitations) > 0


def test_scanner_detects_package_manifest_and_routes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Create a sample package.json
        (root / "package.json").write_text('{"dependencies": {"express": "^4.18.2", "prisma": "^5.0.0"}}', encoding="utf-8")
        
        # Create an Express router file
        src = root / "src"
        src.mkdir()
        (src / "users.ts").write_text('import express from "express";\nconst router = express.Router();\nrouter.get("/", (req, res) => res.json([]));', encoding="utf-8")

        scanner = SafeRepoScanner(tmp)
        report = scanner.scan()

        assert "JavaScript/TypeScript" in report.languages_detected[0] or "TypeScript" in report.languages_detected
        assert "Express.js" in report.frameworks_detected
        assert "Prisma ORM" in report.frameworks_detected
        assert report.total_files_scanned == 2

        # Check verified facts
        fact_types = [f.evidence_type for f in report.verified_facts]
        assert FactEvidenceType.PACKAGE_DEPENDENCY in fact_types
        assert FactEvidenceType.ROUTE_DEFINITION in fact_types

        # Check detected router component
        assert len(report.components) == 1
        assert report.components[0].component_type == ComponentType.API_ROUTER
        assert report.components[0].name == "users"


def test_scanner_ignores_blacklisted_directories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        node_modules = root / "node_modules" / "some-lib"
        node_modules.mkdir(parents=True)
        (node_modules / "index.js").write_text("console.log('ignored')", encoding="utf-8")

        scanner = SafeRepoScanner(tmp)
        report = scanner.scan()
        assert report.total_files_scanned == 0


def test_scanner_detects_flask_blueprint_routes_and_unittest():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "requirements.txt").write_text("flask\nsqlalchemy\n", encoding="utf-8")
        (root / "api.py").write_text(
            "from flask import Blueprint\nbp = Blueprint('x', __name__)\n\n@bp.route('/users')\ndef users():\n    return []\n",
            encoding="utf-8",
        )
        (root / "tests.py").write_text(
            "import unittest\n\nclass T(unittest.TestCase):\n    def test_a(self):\n        pass\n",
            encoding="utf-8",
        )
        report = SafeRepoScanner(tmp).scan()
        assert any(c.component_type == ComponentType.API_ROUTER for c in report.components)
        assert "unittest" in report.test_frameworks_detected
        # unittest methods must not be mistaken for pytest-style functions
        assert "pytest" not in report.test_frameworks_detected


def test_scanner_detects_java_stack_entities_mappers_and_junit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "pom.xml").write_text(
            "<project><dependencies><artifactId>mybatis</artifactId><artifactId>junit-jupiter</artifactId></dependencies></project>",
            encoding="utf-8",
        )
        java = root / "src" / "main" / "java"
        java.mkdir(parents=True)
        (java / "Order.java").write_text("@Entity\npublic class Order {}\n", encoding="utf-8")
        (java / "ItemMapper.java").write_text("@Mapper\npublic interface ItemMapper {}\n", encoding="utf-8")
        (java / "CartController.java").write_text("@Controller\npublic class CartController {}\n", encoding="utf-8")
        tests = root / "src" / "test" / "java"
        tests.mkdir(parents=True)
        (tests / "OrderTest.java").write_text("import org.junit.jupiter.api.Test;\nclass OrderTest {}\n", encoding="utf-8")

        report = SafeRepoScanner(tmp).scan()
        assert "MyBatis" in report.frameworks_detected
        assert "junit" in report.test_frameworks_detected
        models = report.database_coupling.detected_models_or_tables
        assert "Order" in models and "Item" in models
        assert any(c.component_type == ComponentType.API_ROUTER for c in report.components)
