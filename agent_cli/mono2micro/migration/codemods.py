"""Deterministic codemods for safe code extraction, facade injection, and routing generation."""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from mono2micro.models.migration import (
    CodemodKind,
    CodemodResult,
    FeatureFlagConfig,
    GatewayRouteConfig,
)


class DeterministicCodemods:
    """Performs deterministic code transformations without requiring an LLM."""

    @staticmethod
    def extract_python_function(
        source_code: str,
        target_func_name: str,
        target_module_rel_path: str,
    ) -> Tuple[str, str]:
        """Extract a function from source code and replace it with a backward-compatible facade forwarder.

        Returns (updated_source_code, new_target_module_code).
        """
        tree = ast.parse(source_code)
        target_node = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == target_func_name:
                target_node = node
                break

        if not target_node:
            raise ValueError(f"Function '{target_func_name}' not found in source code.")

        lines = source_code.splitlines(keepends=True)
        start_line = target_node.lineno - 1
        end_line = getattr(target_node, "end_lineno", target_node.lineno)

        func_lines = lines[start_line:end_line]
        func_body = "".join(func_lines)

        # Build target module code
        target_code = (
            f'"""Extracted domain service function."""\n\n'
            f"{func_body.strip()}\n"
        )

        # Replace in original source with facade import
        module_import_path = target_module_rel_path.replace("/", ".").replace(".py", "")
        facade_replacement = (
            f"# Facade forwarder for extracted {target_func_name}\n"
            f"from {module_import_path} import {target_func_name}\n"
        )

        updated_source = "".join(lines[:start_line]) + facade_replacement + "".join(lines[end_line:])
        return updated_source, target_code

    @staticmethod
    def generate_api_gateway_routes(routes: List[GatewayRouteConfig], framework: str = "fastapi") -> str:
        """Generate API gateway / Strangler Fig routing facade code."""
        if framework.lower() == "fastapi":
            lines = [
                '"""Auto-generated API Gateway Strangler Facade."""',
                "from fastapi import APIRouter, Request, Response",
                "import httpx",
                "",
                "gateway_router = APIRouter(prefix='/api')",
                "",
            ]
            for r in routes:
                func_name = re.sub(r'[^a-zA-Z0-9_]', '_', r.service_name.lower())
                flag_check = f"    # Feature flag check: {r.feature_flag_key}\n" if r.feature_flag_key else ""
                lines.extend([
                    f"@gateway_router.api_route('{r.route_prefix}/{{path:path}}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])",
                    f"async def route_to_{func_name}(path: str, request: Request):",
                    flag_check +
                    f"    target_url = f'{r.upstream_url}/{r.route_prefix}/{{path}}'",
                    f"    async with httpx.AsyncClient(timeout={r.timeout_ms / 1000.0}) as client:",
                    f"        resp = await client.request(request.method, target_url, content=await request.body())",
                    f"    return Response(content=resp.content, status_code=resp.status_code)",
                    "",
                ])
            return "\n".join(lines)
        else:
            # Express / Node gateway proxy
            lines = [
                "// Auto-generated Express Gateway Proxy",
                "const express = require('express');",
                "const { createProxyMiddleware } = require('http-proxy-middleware');",
                "const router = express.Router();",
                "",
            ]
            for r in routes:
                lines.append(f"router.use('{r.route_prefix}', createProxyMiddleware({{ target: '{r.upstream_url}', changeOrigin: true }}));")
            lines.append("\nmodule.exports = router;\n")
            return "\n".join(lines)

    @staticmethod
    def generate_feature_flags_module(flags: List[FeatureFlagConfig]) -> str:
        """Generate simple, robust feature flags dictionary and helper."""
        lines = [
            '"""Auto-generated Feature Flags configuration."""',
            "import os",
            "from typing import Dict",
            "",
            "FLAGS: Dict[str, bool] = {",
        ]
        for f in flags:
            lines.append(f"    '{f.flag_key}': os.getenv('{f.flag_key.upper()}', '{str(f.enabled).lower()}') in ('1', 'true', 'yes'),")
        lines.extend([
            "}",
            "",
            "def is_feature_enabled(flag_key: str) -> bool:",
            "    return FLAGS.get(flag_key, False)",
            "",
        ])
        return "\n".join(lines)

    @staticmethod
    def split_database_schema_sql(full_schema_sql: str, tables_to_extract: List[str]) -> Tuple[str, str]:
        """Split a monolith schema DDL into retained monolith tables and extracted target tables."""
        table_set = set(t.lower() for t in tables_to_extract)
        retained_statements = []
        extracted_statements = []

        # Split on semicolons
        statements = [s.strip() for s in full_schema_sql.split(";") if s.strip()]
        for stmt in statements:
            match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[`"\[]?([a-zA-Z0-9_]+)[`"\]]?\.)?[`"\[]?([a-zA-Z0-9_]+)[`"\]]?', stmt, re.IGNORECASE)
            if match:
                tbl_name = (match.group(2) or match.group(1)).lower()
                if tbl_name in table_set:
                    extracted_statements.append(stmt + ";")
                else:
                    retained_statements.append(stmt + ";")
            else:
                retained_statements.append(stmt + ";")

        return "\n\n".join(retained_statements) + "\n", "\n\n".join(extracted_statements) + "\n"
