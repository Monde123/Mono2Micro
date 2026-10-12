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
