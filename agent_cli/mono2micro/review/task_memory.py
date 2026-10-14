"""Grounded task memory engine with cryptographic proof and automatic expiry."""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from mono2micro.models.memory import GroundedMemoryProof, TaskMemoryItem
from mono2micro.models.time_utils import utc_now


class TaskMemoryStore:
    """Manages persistent task memories linked to physical filesystem proofs."""

    def __init__(self, target_directory: str):
        self.target_directory = str(Path(target_directory).resolve())
        self.memory_file = Path(self.target_directory) / ".mono2micro" / "task_memory.json"
        self._memories: Dict[str, TaskMemoryItem] = {}
        self._load()

    def _load(self):
        if not self.memory_file.exists():
            return
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item_data in data.get("memories", []):
                item = TaskMemoryItem(**item_data)
                self._memories[item.memory_id] = item
        except Exception:
            pass

    def _save(self):
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "last_updated": utc_now().isoformat(),
            "memories": [m.model_dump(mode="json") for m in self._memories.values()],
        }
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def _compute_file_sha256(self, rel_path: str) -> Optional[str]:
        abs_p = os.path.join(self.target_directory, rel_path)
        if not os.path.exists(abs_p) or not os.path.isfile(abs_p):
            return None
        try:
            with open(abs_p, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except OSError:
            return None

    def record_memory(
        self,
        key: str,
        observation: str,
        file_path: str,
        line_number: int,
    ) -> TaskMemoryItem:
        """Record a new fact memory with cryptographic proof of the underlying file."""
        sha = self._compute_file_sha256(file_path)
        if not sha:
            raise FileNotFoundError(f"Cannot record proof: file '{file_path}' does not exist.")

        proof = GroundedMemoryProof(
            file_path=file_path,
            line_number=line_number,
            content_sha256=sha,
        )
        item = TaskMemoryItem(
            memory_id=f"MEM-{uuid4().hex[:8]}",
            key=key,
            observation=observation,
            proof=proof,
            created_at=utc_now(),
            last_verified_at=utc_now(),
        )
        self._memories[item.memory_id] = item
        self._save()
        return item

    def get_valid_memories(self) -> List[TaskMemoryItem]:
        """Verify proofs against current filesystem state and return only non-expired memories."""
        valid: List[TaskMemoryItem] = []
        changed = False

        for item in list(self._memories.values()):
            current_sha = self._compute_file_sha256(item.proof.file_path)
            if not current_sha:
                if not item.is_expired:
                    item.is_expired = True
                    item.expiry_reason = f"Source file '{item.proof.file_path}' was removed or cannot be read."
                    changed = True
            elif current_sha != item.proof.content_sha256:
                if not item.is_expired:
                    item.is_expired = True
                    item.expiry_reason = f"Source file '{item.proof.file_path}' modified since observation."
                    changed = True
            else:
                item.last_verified_at = utc_now()
                valid.append(item)

        if changed:
            self._save()

        return valid

    def prune_expired(self) -> int:
        """Remove all expired memories and persist the cleaned store."""
        initial_count = len(self._memories)
        self.get_valid_memories()  # update expiry flags
        self._memories = {mid: m for mid, m in self._memories.items() if not m.is_expired}
        pruned_count = initial_count - len(self._memories)
        if pruned_count > 0:
            self._save()
        return pruned_count
