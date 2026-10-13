"""Safe, read-only filesystem and static repository scanner.

Guarantees:
- Never executes any code from the repository.
- Respects exclusion patterns (.git, node_modules, dist, __pycache__, .venv).
- Detects polyglot technologies, dependencies, databases, and entrypoints.
- Generates empirical VerifiedFact instances with file and line evidence.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple

from mono2micro.models.discovery import (
    DiscoveryReport,
    DetectedComponent,
    ComponentType,
    VerifiedFact,
    FactEvidenceType,
    DatabaseCouplingInfo,
)
from mono2micro.core.security import SafePathValidator, SecretMasker


# Directories ignored by default
IGNORED_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", "__pycache__",
    ".pytest_cache", ".venv", "venv", "env", "vendor", ".idea", ".vscode",
    "coverage", ".turbo", ".gradle", "target", "bin", "obj"
}

# Recognized manifest files
MANIFEST_FILES = {
    "package.json": "JavaScript/TypeScript (Node.js)",
    "requirements.txt": "Python (pip)",
    "pyproject.toml": "Python (PEP 517/621)",
    "Pipfile": "Python (Pipenv)",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "Gemfile": "Ruby (Bundler)",
    "composer.json": "PHP (Composer)",
    "csproj": "C# (.NET)",
}


class SafeRepoScanner:
    """Performs passive, non-executing structural scanning of a codebase."""

    def __init__(self, target_dir: str):
        self.validator = SafePathValidator(target_dir)
        self.root_path = self.validator.base_path
        self._content_test_frameworks: Set[str] = set()

    def scan(self) -> DiscoveryReport:
        """Run full passive inspection and compile DiscoveryReport."""
        verified_facts: List[VerifiedFact] = []
        components: List[DetectedComponent] = []
        languages: Set[str] = set()
        frameworks: Set[str] = set()
        test_frameworks: Set[str] = set()
        ci_cd_configs: List[str] = []
        
        total_files = 0
        total_loc = 0
        db_models: List[str] = []
        cross_module_tables: Dict[str, List[str]] = {}
        raw_sql_count = 0
        detected_db_types: Set[str] = set()

        fact_counter = 1

        for root, dirs, files in os.walk(self.root_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(self.root_path))
                total_files += 1

                # Detect CI/CD files
                if ".github/workflows" in rel_path or "gitlab-ci" in rel_path or "Jenkinsfile" in file:
                    ci_cd_configs.append(rel_path)

                # Process manifests
                if file in MANIFEST_FILES:
                    manifest_facts, mf_frameworks, mf_tests = self._inspect_manifest(file_path, rel_path, fact_counter)
                    fact_counter += len(manifest_facts)
                    verified_facts.extend(manifest_facts)
                    frameworks.update(mf_frameworks)
                    test_frameworks.update(mf_tests)
                    languages.add(MANIFEST_FILES[file].split()[0])

                # Process source files for AST/regex patterns
                ext = file_path.suffix.lower()
                lang = self._extension_to_language(ext)
                if lang:
                    languages.add(lang)
                    loc, file_facts, comp, db_hints = self._inspect_source_file(file_path, rel_path, lang, fact_counter)
                    total_loc += loc
                    fact_counter += len(file_facts)
                    verified_facts.extend(file_facts)
                    if comp:
                        components.append(comp)
                    
                    if db_hints:
                        for model_name, db_type in db_hints:
                            db_models.append(model_name)
                            if db_type:
                                detected_db_types.add(db_type)
                            cross_module_tables.setdefault(model_name, []).append(rel_path)

                # Check SQL migrations
                if ext == ".sql":
                    raw_sql_count += 1
                    verified_facts.append(VerifiedFact(
                        fact_id=f"FACT-SQL-{fact_counter}",
                        evidence_type=FactEvidenceType.DATABASE_MIGRATION,
                        file_path=rel_path,
                        observation=f"Fichier de migration ou schéma SQL détecté ({file})"
                    ))
                    fact_counter += 1

        test_frameworks.update(self._content_test_frameworks)

        db_coupling = DatabaseCouplingInfo(
            db_type=", ".join(detected_db_types) if detected_db_types else "Non déterminé (fichiers ORM ou SQL)",
            connection_strings_detected=0,
            detected_models_or_tables=sorted(list(set(db_models))),
            cross_module_table_access={k: list(set(v)) for k, v in cross_module_tables.items()},
            raw_sql_queries_found=raw_sql_count,
            migrations_path=self._find_migrations_dir()
        )

        return DiscoveryReport(
            target_directory=str(self.root_path),
            languages_detected=sorted(list(languages)),
            frameworks_detected=sorted(list(frameworks)),
            total_files_scanned=total_files,
            total_loc_scanned=total_loc,
            components=components,
            database_coupling=db_coupling,
            test_frameworks_detected=sorted(list(test_frameworks)),
            ci_cd_configs_detected=sorted(ci_cd_configs),
            verified_facts=verified_facts,
            model_assumptions=[],
            analysis_limitations=[
                "Analyse statique pure sans exécution dynamique des scripts du projet.",
                "Les dépendances chargées par injection dynamique ou configuration d'exécution distante nécessitent validation humaine.",
                "Les requêtes SQL dynamiques construites par concaténation de chaînes ne sont pas toutes analysables statiquement."
            ]
        )

    def _find_migrations_dir(self) -> Optional[str]:
        candidates = ["migrations", "prisma", "db/migrate", "alembic", "src/db/migrations"]
        for c in candidates:
            p = self.root_path / c
            if p.exists() and p.is_dir():
                return c
        return None

    def _extension_to_language(self, ext: str) -> Optional[str]:
        mapping = {
            ".py": "Python",
            ".ts": "TypeScript",
            ".tsx": "TypeScript (React)",
            ".js": "JavaScript",
            ".jsx": "JavaScript (React)",
            ".go": "Go",
            ".java": "Java",
            ".rb": "Ruby",
            ".php": "PHP",
            ".cs": "C#",
            ".rs": "Rust",
        }
        return mapping.get(ext)

    def _inspect_manifest(self, path: Path, rel_path: str, start_id: int) -> Tuple[List[VerifiedFact], Set[str], Set[str]]:
        facts: List[VerifiedFact] = []
        frameworks: Set[str] = set()
        tests: Set[str] = set()
        
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return facts, frameworks, tests

        if path.name == "package.json":
            try:
                data = json.loads(content)
                all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                # Check known frameworks
                for lib, fw_name in [
                    ("express", "Express.js"), ("fastify", "Fastify"), ("@nestjs/core", "NestJS"),
                    ("next", "Next.js"), ("react", "React"), ("vue", "Vue"), ("prisma", "Prisma ORM"),
                    ("typeorm", "TypeORM"), ("sequelize", "Sequelize"), ("mongoose", "Mongoose")
                ]:
                    if lib in all_deps:
                        frameworks.add(fw_name)
                        facts.append(VerifiedFact(
                            fact_id=f"FACT-PKG-{start_id}",
                            evidence_type=FactEvidenceType.PACKAGE_DEPENDENCY,
                            file_path=rel_path,
                            observation=f"Dépendance {fw_name} ({lib}@{all_deps[lib]}) déclarée"
                        ))
                        start_id += 1

                for t_lib in ["jest", "vitest", "mocha", "cypress", "playwright"]:
                    if t_lib in all_deps:
                        tests.add(t_lib)
            except Exception:
                pass

        elif path.name in ("requirements.txt", "pyproject.toml"):
            for line in content.splitlines():
                clean = line.strip().lower()
                for py_lib, fw in [
                    ("fastapi", "FastAPI"), ("django", "Django"), ("flask", "Flask"),
                    ("sqlalchemy", "SQLAlchemy"), ("tortoise-orm", "Tortoise-ORM"),
                    ("celery", "Celery"), ("pytest", "Pytest")
                ]:
                    if py_lib in clean:
                        if py_lib == "pytest":
                            tests.add("pytest")
                        else:
                            frameworks.add(fw)
                        facts.append(VerifiedFact(
                            fact_id=f"FACT-PKG-{start_id}",
                            evidence_type=FactEvidenceType.PACKAGE_DEPENDENCY,
                            file_path=rel_path,
                            observation=f"Dépendance Python {fw} identifiée dans {path.name}"
                        ))
                        start_id += 1
                        break

        elif path.name in ("pom.xml", "build.gradle"):
            lowered = content.lower()
            for needle, fw in [
                ("spring-boot", "Spring Boot"), ("spring-webmvc", "Spring MVC"),
                ("mybatis", "MyBatis"), ("hibernate", "Hibernate"),
                ("jakarta.persistence", "JPA"), ("javax.persistence", "JPA"),
                ("stripes", "Stripes"), ("quarkus", "Quarkus"),
            ]:
                if needle in lowered:
                    frameworks.add(fw)
                    facts.append(VerifiedFact(
                        fact_id=f"FACT-PKG-{start_id}",
                        evidence_type=FactEvidenceType.PACKAGE_DEPENDENCY,
                        file_path=rel_path,
                        observation=f"Dépendance Java {fw} identifiée dans {path.name}"
                    ))
                    start_id += 1
            for needle, tf in [("junit", "junit"), ("testng", "testng"), ("mockito", "mockito")]:
                if needle in lowered:
                    tests.add(tf)

        return facts, frameworks, tests

    def _detect_test_frameworks_in_content(self, content: str) -> Set[str]:
        """Identify the test framework actually used by a test source file."""
        found: Set[str] = set()
        checks = [
            (r"^\s*(import|from)\s+unittest\b", "unittest"),
            (r"^\s*(import|from)\s+pytest\b|^def\s+test_\w+\s*\(", "pytest"),
            (r"org\.junit", "junit"),
            (r"org\.testng", "testng"),
            (r"\b(describe|it|test)\s*\(\s*['\"]", "js-test-runner"),
        ]
        for pattern, name in checks:
            if re.search(pattern, content, re.MULTILINE):
                found.add(name)
        return found

    def _inspect_source_file(
        self, path: Path, rel_path: str, lang: str, start_id: int
    ) -> Tuple[int, List[VerifiedFact], Optional[DetectedComponent], List[Tuple[str, str]]]:
        facts: List[VerifiedFact] = []
        db_hints: List[Tuple[str, str]] = []
        component: Optional[DetectedComponent] = None

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return 0, facts, None, db_hints

        lines = content.splitlines()
        loc = len(lines)

        comp_type = ComponentType.UNKNOWN
        entrypoint = None

        # Check for HTTP routes or controllers
        if re.search(r'(@app\.(get|post|put|delete)|router\.(get|post|put|delete)|app\.(get|post|use)|@Controller|@\w+\.route\(|@(Get|Post|Put|Delete|Request)Mapping|@RestController|@Path\()', content, re.IGNORECASE):
            comp_type = ComponentType.API_ROUTER
            entrypoint = rel_path
            facts.append(VerifiedFact(
                fact_id=f"FACT-ROUTE-{start_id}",
                evidence_type=FactEvidenceType.ROUTE_DEFINITION,
                file_path=rel_path,
                observation=f"Définition de routes d'API HTTP détectée ({lang})"
            ))
            start_id += 1

        # Check for ORM models or schemas
        orm_model_match = re.findall(r'class\s+([A-Za-z0-9_]+)\s*\(\s*(?:Base|Model|db\.Model)\s*\)', content)
        if orm_model_match:
            comp_type = ComponentType.DATABASE_ORM
            for m in orm_model_match:
                db_hints.append((m, "Relational (SQLAlchemy/Django)"))
                facts.append(VerifiedFact(
                    fact_id=f"FACT-DB-{start_id}",
                    evidence_type=FactEvidenceType.DATABASE_MIGRATION,
                    file_path=rel_path,
                    observation=f"Modèle d'entité relationnelle '{m}' identifié"
                ))
                start_id += 1

        # Check for Prisma models: model User { ... }
        prisma_match = re.findall(r'model\s+([A-Za-z0-9_]+)\s*\{', content)
        if prisma_match:
            comp_type = ComponentType.DATABASE_ORM
            for m in prisma_match:
                db_hints.append((m, "Prisma Schema"))

        # Java: JPA entities and MyBatis mappers
        if lang == "Java":
            for m in re.findall(r'@Entity[\s\S]{0,200}?class\s+([A-Za-z0-9_]+)', content):
                comp_type = ComponentType.DATABASE_ORM
                db_hints.append((m, "Relational (JPA)"))
            if re.search(r'@Mapper\b|interface\s+\w+Mapper\b', content):
                mapper = re.search(r'interface\s+(\w+?)Mapper\b', content)
                if mapper:
                    comp_type = ComponentType.DATABASE_ORM
                    db_hints.append((mapper.group(1), "Relational (MyBatis)"))

        # Check for test files
        if "test" in path.name.lower() or "spec" in path.name.lower():
            comp_type = ComponentType.TEST_SUITE
            self._content_test_frameworks.update(self._detect_test_frameworks_in_content(content))

        if comp_type != ComponentType.UNKNOWN:
            component = DetectedComponent(
                name=path.stem,
                relative_path=rel_path,
                component_type=comp_type,
                language=lang,
                loc_estimate=loc,
                entrypoint=entrypoint
            )

        return loc, facts, component, db_hints
