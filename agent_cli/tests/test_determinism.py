import tempfile
import os
from pathlib import Path
from mono2micro.core.orchestrator import MigrationOrchestrator

def test_heuristic_determinism():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        (src / "main.py").write_text("import os\nclass App:\n    pass\n", encoding="utf-8")
        
        orch1 = MigrationOrchestrator(tmpdir)
        res1 = orch1.step_1_discover()
        
        orch2 = MigrationOrchestrator(tmpdir)
        res2 = orch2.step_1_discover()
        
        assert res1.total_files_scanned == res2.total_files_scanned
        assert res1.frameworks_detected == res2.frameworks_detected
