"""RedTeam Framework - Configuration Manager"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

_BASE_DIR = Path(__file__).resolve().parents[2]

_DEFAULTS: Dict[str, Any] = {
    "base_dir": str(_BASE_DIR),
    "tools_dir": str(_BASE_DIR / "tools"),
    "wordlists_dir": str(_BASE_DIR / "wordlists"),
    "payloads_dir": str(_BASE_DIR / "payloads"),
    "labs_dir": str(_BASE_DIR / "labs"),
    "data_dir": str(_BASE_DIR / "data"),
    "logs_dir": str(_BASE_DIR / "logs"),
    "scripts_dir": str(_BASE_DIR / "scripts"),
    "config_dir": str(_BASE_DIR / "config"),
    "modules_dir": str(_BASE_DIR / "framework" / "modules"),
    "db_path": str(_BASE_DIR / "data" / "framework.db"),
    "tool_registry_path": str(_BASE_DIR / "data" / "tool_registry.json"),
    "vuln_db_path": str(_BASE_DIR / "data" / "vuln_db.json"),
    "api_host": "0.0.0.0",
    "api_port": 8000,
    "api_secret_key": "CHANGE_ME_IN_PRODUCTION",
    "api_keys": [],
    "api_debug": False,
    "dashboard_host": "127.0.0.1",
    "dashboard_port": 5000,
    "scheduler_max_workers": 10,
    "scheduler_default_timeout": 3600,
    "log_level": "INFO",
    "log_file": str(_BASE_DIR / "logs" / "framework.log"),
    "shodan_api_key": "",
    "censys_api_id": "",
    "censys_api_secret": "",
    "virustotal_api_key": "",
    "hunter_api_key": "",
    "go_bin_dir": str(Path.home() / "go" / "bin"),
}


class Config:
    _instance: Optional["Config"] = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data: Dict[str, Any] = {}
            cls._instance._loaded = False
        return cls._instance

    def load(self, config_file: Optional[str] = None) -> None:
        self._data = dict(_DEFAULTS)
        cfg_path = Path(config_file) if config_file else self._find_config_file()
        if cfg_path and cfg_path.exists():
            self._load_file(cfg_path)
        for key in list(self._data.keys()):
            env_key = f"RTF_{key.upper()}"
            env_val = os.environ.get(env_key)
            if env_val is not None:
                self._data[key] = self._coerce(env_val, self._data[key])
        for dir_key in ("tools_dir", "wordlists_dir", "payloads_dir", "labs_dir",
                        "data_dir", "logs_dir", "scripts_dir", "config_dir"):
            try:
                Path(self._data[dir_key]).mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        self._loaded = True

    def get(self, key: str, default: Any = None) -> Any:
        if not self._loaded:
            self.load()
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if not self._loaded:
            self.load()
        self._data[key] = value

    def as_dict(self) -> Dict[str, Any]:
        if not self._loaded:
            self.load()
        return dict(self._data)

    def save(self, path: Optional[str] = None) -> None:
        if not self._loaded:
            self.load()
        out = Path(path) if path else Path(self._data["config_dir"]) / "framework.yaml"
        out.parent.mkdir(parents=True, exist_ok=True)
        if _HAS_YAML:
            out.with_suffix(".yaml").write_text(
                yaml.dump(self._data, default_flow_style=False, sort_keys=True)
            )
        else:
            out.with_suffix(".json").write_text(json.dumps(self._data, indent=2))

    def _find_config_file(self) -> Optional[Path]:
        config_dir = Path(_DEFAULTS["config_dir"])
        for name in ("framework.yaml", "framework.yml", "framework.json"):
            p = config_dir / name
            if p.exists():
                return p
        return None

    def _load_file(self, path: Path) -> None:
        text = path.read_text()
        if path.suffix in (".yaml", ".yml") and _HAS_YAML:
            data = yaml.safe_load(text) or {}
        else:
            try:
                data = json.loads(text)
            except Exception:
                data = {}
        if isinstance(data, dict):
            self._data.update(data)

    @staticmethod
    def _coerce(value: str, reference: Any) -> Any:
        if isinstance(reference, list):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                try:
                    parsed = json.loads(raw)
                    return parsed if isinstance(parsed, list) else [value]
                except json.JSONDecodeError:
                    return [p.strip() for p in value.split(",") if p.strip()]
            return [p.strip() for p in value.split(",") if p.strip()]
        if isinstance(reference, bool):
            return value.lower() in ("1", "true", "yes")
        if isinstance(reference, int):
            try:
                return int(value)
            except ValueError:
                return value
        if isinstance(reference, float):
            try:
                return float(value)
            except ValueError:
                return value
        return value


config = Config()
