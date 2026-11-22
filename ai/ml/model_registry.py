"""Versioned Model Registry with Champion/Challenger promotion and rollback."""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class ModelRegistry:
    """Persists trained ML model bundles and manages Champion promotion & rollback."""

    def __init__(self, registry_dir: str | Path = "models/registry"):
        self.root = Path(registry_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_file = self.root / "champion.json"

    def save_model(self, version: str, bundle: Any, metrics: Dict[str, Any], promote: bool = False) -> Path:
        v_dir = self.root / version
        v_dir.mkdir(parents=True, exist_ok=True)
        with open(v_dir / "model.pkl", "wb") as f:
            pickle.dump(bundle, f)

        meta = {
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
        }
        (v_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        if promote:
            self.promote(version)
        return v_dir

    def promote(self, version: str) -> None:
        state = self._read_state()
        prev = state.get("champion")
        history = state.get("history", [])
        if prev and prev != version:
            history.append(prev)
        self.state_file.write_text(
            json.dumps({"champion": version, "previous": prev, "history": history[-10:]}, indent=2),
            encoding="utf-8",
        )

    def rollback(self) -> Optional[str]:
        state = self._read_state()
        prev = state.get("previous")
        if not prev or not (self.root / prev / "model.pkl").exists():
            return None
        self.state_file.write_text(
            json.dumps({"champion": prev, "previous": state.get("champion"), "history": state.get("history", [])}, indent=2),
            encoding="utf-8",
        )
        return prev

    def load_champion(self) -> Tuple[Optional[str], Optional[Any], Dict[str, Any]]:
        state = self._read_state()
        champ = state.get("champion")
        if not champ:
            return None, None, {}
        pkl_path = self.root / champ / "model.pkl"
        meta_path = self.root / champ / "metadata.json"
        if not pkl_path.exists():
            return None, None, {}
        with open(pkl_path, "rb") as f:
            bundle = pickle.load(f)
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        return champ, bundle, meta

    def _read_state(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
