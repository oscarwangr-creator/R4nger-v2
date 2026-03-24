"""RedTeam Framework - Module Loader"""
from __future__ import annotations
import importlib, importlib.util, inspect, pkgutil, sys
from pathlib import Path
from typing import Dict, List, Optional, Type
from framework.core.exceptions import ModuleNotFoundError
from framework.core.logger import get_logger
from framework.modules.base import BaseModule

log = get_logger("rtf.loader")

class ModuleLoader:
    def __init__(self) -> None:
        self._registry: Dict[str, Type[BaseModule]] = {}
        self._extra_dirs: List[Path] = []

    def load_all(self, extra_dirs: Optional[List[str]] = None) -> int:
        base = Path(__file__).parent
        count = self._scan_package_dir(base)
        if extra_dirs:
            for d in extra_dirs:
                p = Path(d)
                if p.is_dir():
                    self._extra_dirs.append(p)
                    count += self._scan_filesystem_dir(p)
        for d in self._extra_dirs:
            count += self._scan_filesystem_dir(d)
        log.info(f"Loaded {count} modules ({len(self._registry)} registered)")
        return count

    def get(self, module_path: str) -> Type[BaseModule]:
        cls = self._registry.get(module_path)
        if cls is None:
            matches = [k for k in self._registry if module_path.lower() in k.lower()]
            if len(matches) == 1:
                return self._registry[matches[0]]
            if len(matches) > 1:
                raise ModuleNotFoundError(f"Ambiguous path '{module_path}'. Matches: {matches}")
            raise ModuleNotFoundError(f"Module not found: '{module_path}'")
        return cls

    def instantiate(self, module_path: str) -> BaseModule:
        return self.get(module_path)()

    def list_modules(self, category: Optional[str] = None) -> List[Dict]:
        result = []
        for path, cls in self._registry.items():
            try:
                meta = cls().info()
            except Exception:
                meta = {"name": path, "description": "", "category": "unknown"}
            if category and meta.get("category") != category:
                continue
            result.append({"path": path, "name": meta.get("name", path),
                            "description": meta.get("description", ""),
                            "category": meta.get("category", "unknown"),
                            "author": meta.get("author", ""),
                            "version": meta.get("version", "1.0")})
        return sorted(result, key=lambda x: (x["category"], x["name"]))

    def categories(self) -> List[str]:
        cats: set = set()
        for cls in self._registry.values():
            try:
                cats.add(cls().info().get("category", "unknown"))
            except Exception:
                pass
        return sorted(cats)

    def search(self, query: str) -> List[Dict]:
        q = query.lower()
        return [m for m in self.list_modules()
                if q in f"{m['name']} {m['description']} {m['category']} {m.get('author','')}".lower()]

    def _scan_package_dir(self, base: Path) -> int:
        count = 0
        for importer, pkg_name, is_pkg in pkgutil.walk_packages(
            path=[str(base)], prefix="framework.modules.",
            onerror=lambda name: log.warning(f"Import error scanning {name}")):
            if is_pkg or pkg_name.endswith(".base") or pkg_name.endswith(".loader"):
                continue
            try:
                mod = importlib.import_module(pkg_name)
                parts = pkg_name.split(".")
                if len(parts) >= 3:
                    category = parts[-2]
                    count += self._register_from_module(mod, category)
            except Exception as exc:
                log.warning(f"Failed to import {pkg_name}: {exc}")
        return count

    def _scan_filesystem_dir(self, directory: Path) -> int:
        count = 0
        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            category = py_file.parent.name
            try:
                spec = importlib.util.spec_from_file_location(
                    f"ext_modules.{category}.{py_file.stem}", py_file)
                if spec is None or spec.loader is None:
                    continue
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                count += self._register_from_module(mod, category)
            except Exception as exc:
                log.warning(f"Failed to load {py_file}: {exc}")
        return count

    def _register_from_module(self, mod: object, category: str) -> int:
        count = 0
        for _name, cls in inspect.getmembers(mod, inspect.isclass):
            if (issubclass(cls, BaseModule) and cls is not BaseModule
                    and not inspect.isabstract(cls)
                    and cls.__module__ == getattr(mod, "__name__", None)):
                try:
                    src = inspect.getfile(cls)
                    stem = Path(src).stem
                    path = f"{category}/{stem}"
                    if path not in self._registry:
                        self._registry[path] = cls
                        log.debug(f"  ↳ registered {path} → {cls.__name__}")
                        count += 1
                except Exception as exc:
                    log.warning(f"Could not register {cls}: {exc}")
        return count

module_loader = ModuleLoader()
