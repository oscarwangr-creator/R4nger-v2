"""
RedTeam Framework v2.0 - Interactive CLI Console
Metasploit-style operator console with full feature parity + enterprise extensions.

NEW in v2.0:
  setg/unsetg    — persistent global options across modules
  workspace      — named investigation workspaces
  sessions       — session management
  history/!N     — command history with replay
  grep           — pipe output through regex filter
  resource <rc>  — run .rc resource script files
  notes          — per-target investigation notes
  report         — generate engagement reports
  spool          — log all output to file
  banner         — display random quote
  color on|off   — toggle rich color
  reload         — hot-reload modules
  db_status      — show database connection status
  loot           — show captured credentials/hashes
  creds          — manage credential store
  pivot          — show pivot chains
"""

from __future__ import annotations

import asyncio
import cmd
import json
import os
import random
import re
import shutil
import sys
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Startup PATH fix (critical for sudo and clean environments) ──────────
# sudo strips ~/go/bin, ~/.local/bin etc. — restore them so tool checks work.
def _fix_path() -> None:
    """Ensure user tool directories are in PATH regardless of sudo."""
    import pwd
    try:
        # Get the real user's home even under sudo
        sudo_user = os.environ.get("SUDO_USER", "")
        if sudo_user:
            home = pwd.getpwnam(sudo_user).pw_dir
        else:
            home = str(Path.home())
    except Exception:
        home = str(Path.home())

    extra_paths = [
        os.path.join(home, "go", "bin"),
        os.path.join(home, ".local", "bin"),
        os.path.join(home, ".cargo", "bin"),
        "/usr/local/go/bin",
        "/snap/bin",
        "/usr/local/bin",
        os.path.join(home, "redteam-lab", "tools"),
    ]
    current = os.environ.get("PATH", "").split(":")
    added = [p for p in extra_paths if p not in current and os.path.isdir(p)]
    if added:
        os.environ["PATH"] = ":".join(added) + ":" + os.environ.get("PATH", "")

_fix_path()


try:
    from rich.console import Console as RichConsole
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.columns import Columns
    from rich import box
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

BANNER = r"""
 ██████╗ ████████╗███████╗  v2.0
 ██╔══██╗╚══██╔══╝██╔════╝  Enterprise RedTeam Platform
 ██████╔╝   ██║   █████╗    ══════════════════════════
 ██╔══██╗   ██║   ██╔══╝    [bold red]AUTHORIZED USE ONLY[/bold red]
 ██║  ██║   ██║   ██║       Operators: use responsibly
 ╚═╝  ╚═╝   ╚═╝   ╚═╝
"""

QUOTES = [
    "The quieter you become, the more you can hear. — Ram Dass",
    "Offense is the best defense... in red teaming. — RTF",
    "Know your enemy and know yourself. — Sun Tzu",
    "Security is a process, not a product. — Bruce Schneier",
    "The only truly secure system is powered off. — Gene Spafford",
    "Hackers are the immune system of the internet. — Keren Elazari",
    "Simplicity is the soul of efficiency. — Austin Freeman",
    "Every system has a weakness; find it before the adversary does. — RTF",
]


class _Con:
    """Thin Rich/fallback console wrapper with spool support."""

    def __init__(self) -> None:
        if _HAS_RICH:
            self._rc = RichConsole(highlight=True)
        else:
            self._rc = None
        self._spool: Optional[Path] = None
        self._color = True

    def print(self, *args: Any, **kwargs: Any) -> None:
        text = " ".join(str(a) for a in args)
        if self._spool:
            # Strip rich markup for file
            clean = re.sub(r"\[/?[^\]]*\]", "", text)
            with self._spool.open("a") as fh:
                fh.write(clean + "\n")
        if self._rc and self._color:
            self._rc.print(*args, **kwargs)
        else:
            clean = re.sub(r"\[/?[^\]]*\]", "", text)
            print(clean)

    def rule(self, title: str = "") -> None:
        if self._rc and self._color:
            self._rc.rule(title)
        else:
            print(f"{'─' * 20} {title} {'─' * 20}")

    def print_table(self, table: Any) -> None:
        if self._rc and self._color:
            self._rc.print(table)
        else:
            print(str(table))

    def start_spool(self, path: str) -> None:
        self._spool = Path(path)
        self._spool.parent.mkdir(parents=True, exist_ok=True)
        self._spool.touch()

    def stop_spool(self) -> None:
        self._spool = None


_con = _Con()


class RTFConsole(cmd.Cmd):
    """
    RTF v2.0 interactive operator console.

    Metasploit-compatible commands + enterprise extensions.
    """

    intro = ""
    prompt = "rtf > "

    def __init__(self) -> None:
        super().__init__()
        self._active_module = None
        self._active_path: Optional[str] = None
        self._options: Dict[str, Any] = {}          # per-module options
        self._global_opts: Dict[str, Any] = {}       # persistent across modules
        self._workspace: str = "default"
        self._workspaces: Dict[str, Dict] = {"default": {}}
        self._sessions: Dict[str, Dict] = {}
        self._notes: Dict[str, List[str]] = {}
        self._loot: List[Dict] = []
        self._history: List[str] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._color = True
        self._last_result = None

    # ─────────────────────────────────────────────────────────────────
    # Startup
    # ─────────────────────────────────────────────────────────────────

    def start(self) -> None:
        """
        Initialise and enter the REPL.

        Safe startup sequence:
          1. PATH is already fixed by _fix_path() at module import time
          2. Create ONE event loop and reuse it throughout the session
          3. tool_registry.refresh() uses shutil.which() only (no subprocesses)
          4. cmdloop() is only entered when stdin is a real TTY
        """
        # ── Event loop: create once, reuse throughout session ──────────
        # Never recreate the loop during a session — causes crashes on Py3.10+
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        except Exception:
            import asyncio as _asyncio
            self._loop = _asyncio.new_event_loop()
            _asyncio.set_event_loop(self._loop)

        # ── Config ─────────────────────────────────────────────────────
        try:
            from framework.core.config import config
            config.load()
        except Exception as e:
            _con.print(f"[yellow]Config load warning: {e}[/yellow]")

        # ── Database ───────────────────────────────────────────────────
        try:
            from framework.db.database import db
            from framework.core.config import config
            db_path = config.get("db_path", "data/framework.db")
            # Ensure data dir exists (important when running as sudo)
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            db.init(db_path)
        except Exception as e:
            _con.print(f"[yellow]DB init warning: {e}[/yellow]")

        # ── Modules (lazy import per category to avoid memory spike) ───
        try:
            from framework.modules.loader import module_loader
            n = module_loader.load_all()
        except Exception as e:
            n = 0
            _con.print(f"[yellow]Module loader warning: {e}[/yellow]")

        # ── Tool registry (shutil.which() ONLY — no subprocess calls) ──
        # Version checks are deferred to `tools list --versions` command.
        # Running subprocess calls here on a Kali system with 20+ tools
        # installed would spawn 80+ blocking processes and crash low-RAM machines.
        try:
            from framework.registry.tool_registry import tool_registry
            tool_registry.refresh(check_versions=False)   # FAST: which() only
            tools_total     = len(tool_registry.list_all())
            tools_installed = len(tool_registry.list_installed())
        except Exception as e:
            tools_total = tools_installed = 0
            _con.print(f"[yellow]Registry warning: {e}[/yellow]")

        # ── Banner ─────────────────────────────────────────────────────
        if _HAS_RICH:
            rc = RichConsole()
            rc.print(BANNER)
        else:
            print(re.sub(r"\[/?[^\]]*\]", "", BANNER))

        _con.print(f"[bold green]       RTF Enterprise RedTeam Framework v2.0[/bold green]")
        _con.print(f"[dim]       {random.choice(QUOTES)}[/dim]\n")
        _con.print(f"[green]✓[/green] Modules    : [bold]{n}[/bold] loaded")
        _con.print(f"[green]✓[/green] Tools      : [bold]{tools_installed}/{tools_total}[/bold] installed")
        _con.print(f"[green]✓[/green] Workspace  : [bold]{self._workspace}[/bold]")
        _con.print(f"[dim]Type 'help' for commands, 'search <term>' to find modules[/dim]\n")

        # ── REPL entry ─────────────────────────────────────────────────────
        # cmd.Cmd.cmdloop() handles both TTY and pipe input correctly
        # now that do_EOF is defined (returns True = stop loop on Ctrl-D/EOF).
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            _con.print("\n[dim]Use 'exit' to quit.[/dim]")
        except EOFError:
            # Piped stdin exhausted (e.g. `echo exit | sudo python3 rtf.py console`)
            pass

        # ── Cleanup ────────────────────────────────────────────────────
        if self._loop and not self._loop.is_closed():
            try:
                # Cancel any pending async tasks cleanly
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            finally:
                self._loop.close()

    # ─────────────────────────────────────────────────────────────────
    # Prompt helper
    # ─────────────────────────────────────────────────────────────────

    def _update_prompt(self) -> None:
        ws = f"[{self._workspace}]" if self._workspace != "default" else ""
        if self._active_path:
            self.prompt = f"rtf {ws}({self._active_path}) > "
        else:
            self.prompt = f"rtf {ws}> "

    # ─────────────────────────────────────────────────────────────────
    # Module management
    # ─────────────────────────────────────────────────────────────────

    def do_use(self, arg: str) -> None:
        """use <module_path>  — Select a module (e.g. use recon/port_scan)"""
        path = arg.strip()
        if not path:
            _con.print("[red]Usage: use <category/module_name>[/red]")
            return
        try:
            from framework.modules.loader import module_loader
            cls = module_loader.get(path)
            self._active_module = cls()
            self._active_path = path
            self._options = {}
            # Apply globals
            for k, v in self._global_opts.items():
                try:
                    self._active_module.set(k, v)
                    self._options[k] = v
                except Exception:
                    pass
            meta = self._active_module.info()
            _con.print(f"\n[bold green]Using module:[/bold green] [bold]{path}[/bold]")
            _con.print(f"[cyan]  Category :[/cyan] {meta.get('category','')}")
            _con.print(f"[cyan]  Version  :[/cyan] {meta.get('version','1.0')}")
            _con.print(f"[cyan]  Desc     :[/cyan] {meta.get('description','')}")
            refs = meta.get('references', [])
            if refs:
                _con.print(f"[cyan]  Refs     :[/cyan] {refs[0]}")
            _con.print()
            self._update_prompt()
            self._history.append(f"use {path}")
        except Exception as exc:
            _con.print(f"[red]Error:[/red] {exc}")

    def complete_use(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        try:
            from framework.modules.loader import module_loader
            paths = [m["path"] for m in module_loader.list_modules()]
            return [p for p in paths if p.startswith(text)]
        except Exception:
            return []

    def do_back(self, _: str) -> None:
        """back  — Deselect the current module"""
        self._active_module = None
        self._active_path = None
        self._options = {}
        self._update_prompt()

    def do_set(self, arg: str) -> None:
        """set <option> <value>  — Set an option on the active module"""
        if not self._active_module:
            _con.print("[yellow]No module selected. Use 'use <module>'[/yellow]")
            return
        parts = arg.split(None, 1)
        if len(parts) != 2:
            _con.print("[red]Usage: set <option> <value>[/red]")
            return
        key, val = parts
        try:
            self._active_module.set(key, val)
            self._options[key] = val
            _con.print(f"  [green]{key}[/green] => [bold]{val}[/bold]")
        except Exception as exc:
            _con.print(f"[red]Error:[/red] {exc}")

    def do_setg(self, arg: str) -> None:
        """setg <option> <value>  — Set a GLOBAL option (persists across modules)"""
        parts = arg.split(None, 1)
        if len(parts) != 2:
            _con.print("[red]Usage: setg <option> <value>[/red]")
            return
        key, val = parts
        self._global_opts[key] = val
        if self._active_module:
            try:
                self._active_module.set(key, val)
                self._options[key] = val
            except Exception:
                pass
        _con.print(f"  [bold green]GLOBAL[/bold green] [green]{key}[/green] => [bold]{val}[/bold]")

    def do_unset(self, arg: str) -> None:
        """unset <option>  — Clear a module option"""
        key = arg.strip()
        if not key:
            _con.print("[red]Usage: unset <option>[/red]")
            return
        self._options.pop(key, None)
        if self._active_module:
            try:
                self._active_module.set(key, "")
            except Exception:
                pass
        _con.print(f"[green]Unset {key}[/green]")

    def do_unsetg(self, arg: str) -> None:
        """unsetg <option>  — Clear a global option"""
        key = arg.strip()
        self._global_opts.pop(key, None)
        _con.print(f"[green]Unset global {key}[/green]")

    def do_show(self, arg: str) -> None:
        """show [options|modules|categories|findings|jobs|globals|loot|sessions]"""
        arg = arg.strip().lower()
        dispatch = {
            "": self._show_options,
            "options": self._show_options,
            "modules": self._show_modules,
            "categories": self._show_categories,
            "findings": self._show_findings,
            "jobs": self._show_jobs,
            "globals": self._show_globals,
            "loot": self._show_loot,
            "sessions": self._show_sessions,
        }
        fn = dispatch.get(arg)
        if fn:
            fn()
        else:
            _con.print(f"[red]Unknown show target: {arg}[/red]")
            _con.print("[dim]Options: options|modules|categories|findings|jobs|globals|loot|sessions[/dim]")

    def _show_options(self) -> None:
        if not self._active_module:
            _con.print("[yellow]No module selected.[/yellow]")
            return
        if _HAS_RICH:
            t = Table(title=f"Module Options: {self._active_path}", box=box.SIMPLE_HEAVY,
                      border_style="bright_red", show_header=True, header_style="bold cyan")
            t.add_column("Name", style="bold cyan", width=22)
            t.add_column("Current Value", style="green", width=30)
            t.add_column("Req", style="yellow", width=4)
            t.add_column("Default", style="dim", width=20)
            t.add_column("Description", style="dim")
            for opt in self._active_module.show_options():
                cv = str(opt.get("current_value") or "")
                t.add_row(
                    opt["name"],
                    cv[:30] or "[dim]<unset>[/dim]",
                    "✓" if opt["required"] else "",
                    str(opt.get("default") or "")[:20],
                    opt.get("description", "")[:60],
                )
            _con.print_table(t)
        else:
            print(f"\n--- Options: {self._active_path} ---")
            for opt in self._active_module.show_options():
                req = "*" if opt["required"] else " "
                print(f"  {req} {opt['name']:22} {str(opt.get('current_value','') or ''):25} {opt.get('description','')[:50]}")

    def _show_modules(self) -> None:
        try:
            from framework.modules.loader import module_loader
            modules = module_loader.list_modules()
        except Exception:
            _con.print("[red]Module loader not available[/red]")
            return
        if _HAS_RICH:
            t = Table(title=f"Loaded Modules ({len(modules)})", box=box.SIMPLE,
                      border_style="red", header_style="bold")
            t.add_column("Path", style="bold cyan", width=40)
            t.add_column("Category", style="yellow", width=18)
            t.add_column("Version", style="dim", width=7)
            t.add_column("Description", style="dim")
            for m in modules:
                t.add_row(m["path"], m["category"], str(m.get("version","1.0")), m["description"][:55])
            _con.print_table(t)
        else:
            for m in modules:
                print(f"  {m['path']:40} {m['category']:18} {m['description'][:50]}")

    def _show_categories(self) -> None:
        try:
            from framework.modules.loader import module_loader
            cats = module_loader.categories()
            for cat in cats:
                mods = module_loader.list_modules(category=cat)
                _con.print(f"  [cyan]{cat:22}[/cyan] [dim]({len(mods)} modules)[/dim]")
        except Exception as e:
            _con.print(f"[red]Error: {e}[/red]")

    def _show_findings(self) -> None:
        try:
            from framework.db.database import db
            findings = db.list_findings(limit=50)
        except Exception:
            _con.print("[yellow]Database not available[/yellow]")
            return
        if not findings:
            _con.print("[dim]No findings recorded yet.[/dim]")
            return
        if _HAS_RICH:
            t = Table(title=f"Findings ({len(findings)})", box=box.SIMPLE, border_style="red")
            t.add_column("Sev", style="bold", width=10)
            t.add_column("Title", width=50)
            t.add_column("Target", style="cyan", width=25)
            t.add_column("Date", style="dim", width=16)
            sev_colors = {"critical": "bold red", "high": "red", "medium": "yellow", "low": "green", "info": "blue"}
            for f in findings:
                sev = f.get("severity", "info").lower()
                color = sev_colors.get(sev, "white")
                t.add_row(
                    f"[{color}]{sev.upper()}[/{color}]",
                    f.get("title", "")[:50],
                    f.get("target", "")[:25],
                    str(f.get("created_at", ""))[:16],
                )
            _con.print_table(t)
        else:
            for f in findings:
                print(f"  [{f.get('severity','info').upper():8}] {f.get('title','')[:50]:50} {f.get('target','')}")

    def _show_jobs(self) -> None:
        try:
            from framework.db.database import db
            jobs = db.list_jobs(limit=20)
        except Exception:
            _con.print("[yellow]Database not available[/yellow]")
            return
        if not jobs:
            _con.print("[dim]No jobs yet.[/dim]")
            return
        if _HAS_RICH:
            t = Table(title="Recent Jobs (20)", box=box.SIMPLE, border_style="red")
            t.add_column("ID", style="dim", width=10)
            t.add_column("Name", style="bold", width=30)
            t.add_column("Status", width=12)
            t.add_column("Created", style="dim", width=17)
            status_colors = {"completed": "green", "failed": "red", "running": "yellow", "pending": "blue"}
            for j in jobs:
                st = j.get("status", "")
                col = status_colors.get(st, "white")
                t.add_row(
                    str(j.get("id",""))[:8],
                    j.get("name","")[:30],
                    f"[{col}]{st.upper()}[/{col}]",
                    str(j.get("created_at",""))[:17],
                )
            _con.print_table(t)
        else:
            for j in jobs:
                print(f"  {str(j.get('id',''))[:8]}  {j.get('name',''):30} {j.get('status',''):12}")

    def _show_globals(self) -> None:
        if not self._global_opts:
            _con.print("[dim]No global options set.[/dim]")
            return
        _con.print("\n[bold cyan]Global Options:[/bold cyan]")
        for k, v in self._global_opts.items():
            _con.print(f"  [green]{k:20}[/green] {v}")

    def _show_loot(self) -> None:
        if not self._loot:
            _con.print("[dim]No loot captured yet.[/dim]")
            return
        _con.print(f"\n[bold red]Loot ({len(self._loot)} items):[/bold red]")
        for item in self._loot:
            _con.print(f"  [{item.get('type','?'):12}] {item.get('target','?'):20} {str(item.get('data',''))[:60]}")

    def _show_sessions(self) -> None:
        if not self._sessions:
            _con.print("[dim]No active sessions.[/dim]")
            return
        _con.print(f"\n[bold cyan]Sessions ({len(self._sessions)}):[/bold cyan]")
        for sid, info in self._sessions.items():
            _con.print(f"  [{sid}] {info.get('target','?'):20} {info.get('type','?'):15} {info.get('opened_at','?')}")

    # ─────────────────────────────────────────────────────────────────
    # Info / Search
    # ─────────────────────────────────────────────────────────────────

    def do_info(self, arg: str) -> None:
        """info [module_path]  — Show detailed module information"""
        path = arg.strip() or self._active_path
        if not path:
            _con.print("[red]Usage: info <module_path>[/red]")
            return
        try:
            from framework.modules.loader import module_loader
            cls = module_loader.get(path)
            inst = cls()
            meta = inst.info()
            _con.print(f"\n[bold red]{'═' * 60}[/bold red]")
            _con.print(f"  [bold cyan]Module:[/bold cyan]      {path}")
            for k in ("name", "description", "author", "category", "version"):
                if k in meta:
                    _con.print(f"  [cyan]{k:12}[/cyan] {meta[k]}")
            refs = meta.get("references", [])
            for ref in refs[:3]:
                _con.print(f"  [cyan]{'reference':12}[/cyan] [dim]{ref}[/dim]")
            _con.print(f"\n[bold]Options:[/bold]")
            for opt in inst.show_options():
                req = "[bold red]*[/bold red]" if opt["required"] else " "
                _con.print(f"  {req} [cyan]{opt['name']:22}[/cyan] [dim]{opt['description']}[/dim]")
            _con.print(f"[bold red]{'═' * 60}[/bold red]\n")
        except Exception as exc:
            _con.print(f"[red]Error:[/red] {exc}")

    def complete_info(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        return self.complete_use(text, line, begidx, endidx)

    def do_search(self, arg: str) -> None:
        """search <query>  — Search modules by name/description/category"""
        if not arg.strip():
            _con.print("[red]Usage: search <query>[/red]")
            return
        self._history.append(f"search {arg}")
        try:
            from framework.modules.loader import module_loader
            results = module_loader.search(arg.strip())
        except Exception as e:
            _con.print(f"[red]Error: {e}[/red]")
            return
        if not results:
            _con.print("[dim]No results found.[/dim]")
            return
        _con.print(f"\n[bold]Found [green]{len(results)}[/green] modules matching '[cyan]{arg}[/cyan]':[/bold]")
        if _HAS_RICH:
            t = Table(box=box.SIMPLE, border_style="dim")
            t.add_column("Path", style="bold cyan", width=38)
            t.add_column("Category", style="yellow", width=18)
            t.add_column("Description", style="dim")
            for m in results:
                t.add_row(m["path"], m["category"], m["description"][:55])
            _con.print_table(t)
        else:
            for m in results:
                print(f"  {m['path']:38} {m['category']:18} {m['description'][:50]}")

    # ─────────────────────────────────────────────────────────────────
    # Execution
    # ─────────────────────────────────────────────────────────────────

    def do_run(self, arg: str) -> None:
        """run  — Execute the active module"""
        self._history.append("run")
        self._execute_active()

    do_exploit = do_run  # Metasploit alias
    do_check = do_run   # Alias

    def _execute_active(self) -> None:
        if not self._active_module:
            _con.print("[yellow]No module selected. Use 'use <module>'[/yellow]")
            return
        _con.print(f"\n[bold cyan]► Executing:[/bold cyan] [bold]{self._active_path}[/bold]")
        _con.rule()
        start = time.time()
        try:
            if self._loop and not self._loop.is_closed():
                result = self._loop.run_until_complete(
                    self._active_module.execute(self._options)
                )
            else:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                result = self._loop.run_until_complete(
                    self._active_module.execute(self._options)
                )
            self._last_result = result
            elapsed = time.time() - start
            if result.success:
                _con.print(f"\n[bold green]✓ Success[/bold green] | elapsed=[bold]{elapsed:.2f}s[/bold] | findings=[bold]{len(result.findings)}[/bold]")
                if result.findings:
                    _con.print(f"\n[bold]Findings:[/bold]")
                    sev_colors = {"critical": "bold red", "high": "red", "medium": "yellow", "low": "green", "info": "blue"}
                    for f in result.findings[:20]:
                        sev = f.severity.value if hasattr(f.severity, 'value') else str(f.severity)
                        color = sev_colors.get(sev.lower(), "white")
                        _con.print(f"  [{color}]{sev.upper():8}[/{color}] {f.title[:60]}")
                if result.output and isinstance(result.output, dict):
                    _con.print(f"\n[dim]Output summary:[/dim]")
                    for k, v in list(result.output.items())[:6]:
                        if not isinstance(v, (list, dict)):
                            _con.print(f"  [cyan]{k}[/cyan] : {str(v)[:80]}")
                        elif isinstance(v, list):
                            _con.print(f"  [cyan]{k}[/cyan] : {len(v)} items")
            else:
                _con.print(f"\n[bold red]✗ Failed:[/bold red] {result.error}")
        except KeyboardInterrupt:
            _con.print("\n[yellow]⚠ Interrupted[/yellow]")
        except Exception as exc:
            _con.print(f"\n[bold red]✗ Exception:[/bold red] {exc}")
        _con.rule()

    # ─────────────────────────────────────────────────────────────────
    # Workspace management
    # ─────────────────────────────────────────────────────────────────

    def do_workspace(self, arg: str) -> None:
        """workspace [name | -d name | -l]  — Manage named workspaces"""
        parts = arg.strip().split()
        if not parts or parts[0] == "-l":
            _con.print(f"\n[bold cyan]Workspaces:[/bold cyan]")
            for ws in self._workspaces:
                marker = "[bold green]►[/bold green]" if ws == self._workspace else " "
                _con.print(f"  {marker} [bold]{ws}[/bold]")
            return
        if parts[0] == "-d" and len(parts) > 1:
            name = parts[1]
            if name == "default":
                _con.print("[red]Cannot delete default workspace[/red]")
                return
            self._workspaces.pop(name, None)
            if self._workspace == name:
                self._workspace = "default"
            _con.print(f"[green]Deleted workspace: {name}[/green]")
            self._update_prompt()
            return
        name = parts[0]
        if name not in self._workspaces:
            self._workspaces[name] = {}
            _con.print(f"[green]Created workspace: {name}[/green]")
        self._workspace = name
        _con.print(f"[green]Switched to workspace: [bold]{name}[/bold][/green]")
        self._update_prompt()

    # ─────────────────────────────────────────────────────────────────
    # Workflows
    # ─────────────────────────────────────────────────────────────────

    def do_workflows(self, _: str) -> None:
        """workflows  — List all available workflows"""
        try:
            from framework.workflows.engine import BUILTIN_WORKFLOWS
        except Exception as e:
            _con.print(f"[red]Error loading workflows: {e}[/red]")
            return
        _con.print(f"\n[bold red]Available Workflows ({len(BUILTIN_WORKFLOWS)}):[/bold red]")
        if _HAS_RICH:
            t = Table(box=box.SIMPLE, border_style="red")
            t.add_column("Name", style="bold cyan", width=25)
            t.add_column("Description", style="dim")
            for name, cls in BUILTIN_WORKFLOWS.items():
                try:
                    desc = cls().description
                except Exception:
                    desc = ""
                t.add_row(name, desc)
            _con.print_table(t)
        else:
            for name, cls in BUILTIN_WORKFLOWS.items():
                try:
                    desc = cls().description
                except Exception:
                    desc = ""
                print(f"  {name:25} {desc}")

    def do_run_workflow(self, arg: str) -> None:
        """run_workflow <name> [json_opts]  — Execute a workflow"""
        parts = arg.strip().split(None, 1)
        if not parts:
            _con.print("[red]Usage: run_workflow <name> ['{\"target\":\"example.com\"}'][/red]")
            return
        wf_name = parts[0]
        opts = {}
        if len(parts) > 1:
            try:
                opts = json.loads(parts[1])
            except json.JSONDecodeError:
                _con.print("[red]Invalid JSON options[/red]")
                return
        # Merge globals
        merged = {**self._global_opts, **opts}
        try:
            from framework.workflows.engine import get_workflow
            wf = get_workflow(wf_name, merged)
        except KeyError as exc:
            _con.print(f"[red]Error:[/red] {exc}")
            return
        _con.print(f"\n[bold cyan]► Running workflow:[/bold cyan] [bold]{wf_name}[/bold]")
        _con.rule()
        try:
            if self._loop and not self._loop.is_closed():
                result = self._loop.run_until_complete(wf.run(merged))
            else:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                result = self._loop.run_until_complete(wf.run(merged))
            status_color = "green" if result.success else "red"
            status_icon = "✓" if result.success else "✗"
            _con.print(f"\n[{status_color}]{status_icon} Workflow finished[/{status_color}] | elapsed=[bold]{result.elapsed:.1f}s[/bold] | findings=[bold]{result.total_findings}[/bold]")
            for step in result.steps:
                step_color = "green" if step.success else "red"
                step_icon = "✓" if step.success else "✗"
                findings_count = len(step.result.findings) if step.result else 0
                _con.print(f"  [{step_color}]{step_icon}[/{step_color}] [dim]{step.step_name:30}[/dim] [dim]{findings_count} findings[/dim]")
        except KeyboardInterrupt:
            _con.print("\n[yellow]⚠ Workflow interrupted[/yellow]")
        except Exception as exc:
            _con.print(f"[red]Error:[/red] {exc}")
        _con.rule()

    # ─────────────────────────────────────────────────────────────────
    # Tools
    # ─────────────────────────────────────────────────────────────────

    def do_tools(self, arg: str) -> None:
        """tools [--installed|--missing|--category <cat>|--search <term>]"""
        arg = arg.strip()
        try:
            from framework.registry.tool_registry import tool_registry, ToolCategory
            tools = tool_registry.list_all()
        except Exception as e:
            _con.print(f"[red]Registry error: {e}[/red]")
            return
        if arg == "--installed":
            tools = [t for t in tools if t.installed]
        elif arg == "--missing":
            tools = [t for t in tools if not t.installed]
        elif arg.startswith("--category "):
            cat_name = arg[11:].strip()
            try:
                tools = tool_registry.list_all(ToolCategory(cat_name))
            except ValueError:
                _con.print(f"[red]Unknown category: {cat_name}[/red]")
                return
        elif arg.startswith("--search "):
            term = arg[9:].strip().lower()
            tools = [t for t in tools if term in t.name.lower() or term in t.description.lower()]

        if _HAS_RICH:
            t = Table(title=f"Tool Registry ({len(tools)} tools)", box=box.SIMPLE,
                      border_style="red", header_style="bold")
            t.add_column("Name", style="bold", width=22)
            t.add_column("Category", style="yellow", width=16)
            t.add_column("Method", style="dim", width=8)
            t.add_column("Status", width=10)
            t.add_column("Description", style="dim")
            for tool in tools:
                status = "[green]✓ INSTALLED[/green]" if tool.installed else "[red]✗ MISSING[/red]"
                t.add_row(tool.name, tool.category.value, tool.install_type.value, status, tool.description[:45])
            _con.print_table(t)
        else:
            for tool in tools:
                s = "✓" if tool.installed else "✗"
                print(f"  {s} {tool.name:22} {tool.category.value:16} {tool.description[:45]}")

    def do_install(self, arg: str) -> None:
        """install <tool_name>  — Install a tool from the registry"""
        name = arg.strip()
        if not name:
            _con.print("[red]Usage: install <tool_name>[/red]")
            return
        self._history.append(f"install {name}")
        _con.print(f"[cyan]Installing [bold]{name}[/bold]…[/cyan]")
        try:
            from framework.registry.tool_registry import tool_registry
            ok = tool_registry.install(name)
            if ok:
                _con.print(f"[green]✓ {name} installed successfully[/green]")
            else:
                _con.print(f"[red]✗ Failed to install {name}. Check logs for details.[/red]")
        except Exception as e:
            _con.print(f"[red]Error: {e}[/red]")

    # ─────────────────────────────────────────────────────────────────
    # History, resource files, grep
    # ─────────────────────────────────────────────────────────────────

    def do_history(self, _: str) -> None:
        """history  — Show command history (with line numbers for !N replay)"""
        if not self._history:
            _con.print("[dim]No history yet.[/dim]")
            return
        for idx, item in enumerate(self._history[-100:], 1):
            _con.print(f"  [dim]{idx:3d}[/dim]  {item}")

    def default(self, line: str) -> bool:
        # !N replay from history
        if line.startswith("!"):
            try:
                idx = int(line[1:]) - 1
                if 0 <= idx < len(self._history):
                    cmd_replay = self._history[idx]
                    _con.print(f"[dim]Replaying: {cmd_replay}[/dim]")
                    return self.onecmd(cmd_replay)
            except (ValueError, IndexError):
                pass
        _con.print(f"[red]Unknown command:[/red] {line}  [dim](type 'help' for commands)[/dim]")
        return False

    def do_resource(self, arg: str) -> None:
        """resource <file.rc>  — Execute commands from a resource file"""
        path = arg.strip()
        if not path:
            _con.print("[red]Usage: resource <file.rc>[/red]")
            return
        try:
            lines = Path(path).read_text().splitlines()
            _con.print(f"[cyan]Executing resource file: {path} ({len(lines)} commands)[/cyan]")
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                _con.print(f"[dim]  rc > {line}[/dim]")
                self.onecmd(line)
        except FileNotFoundError:
            _con.print(f"[red]File not found: {path}[/red]")
        except Exception as e:
            _con.print(f"[red]Error reading resource file: {e}[/red]")

    def do_grep(self, arg: str) -> None:
        """grep <pattern> <command>  — Run command and filter output by regex"""
        parts = arg.split(None, 1)
        if len(parts) < 2:
            _con.print("[red]Usage: grep <pattern> <command>[/red]")
            return
        pattern, rest_cmd = parts[0], parts[1]
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = buf = StringIO()
        try:
            self.onecmd(rest_cmd)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()
        try:
            rx = re.compile(pattern, re.IGNORECASE)
            hits = [line for line in output.splitlines() if rx.search(line)]
            if hits:
                for h in hits:
                    _con.print(h)
            else:
                _con.print(f"[dim]No matches for '{pattern}'[/dim]")
        except re.error as e:
            _con.print(f"[red]Invalid regex: {e}[/red]")

    # ─────────────────────────────────────────────────────────────────
    # Notes / Loot / Creds
    # ─────────────────────────────────────────────────────────────────

    def do_notes(self, arg: str) -> None:
        """notes [target] [text]  — Manage investigation notes"""
        parts = arg.strip().split(None, 1)
        if not parts:
            # Show all notes
            if not self._notes:
                _con.print("[dim]No notes recorded.[/dim]")
                return
            for target, note_list in self._notes.items():
                _con.print(f"\n[bold cyan]{target}:[/bold cyan]")
                for i, note in enumerate(note_list, 1):
                    _con.print(f"  {i}. {note}")
            return
        target = parts[0]
        if len(parts) == 1:
            # Show notes for target
            notes_for = self._notes.get(target, [])
            if not notes_for:
                _con.print(f"[dim]No notes for {target}[/dim]")
            else:
                _con.print(f"\n[bold cyan]Notes for {target}:[/bold cyan]")
                for i, note in enumerate(notes_for, 1):
                    _con.print(f"  {i}. {note}")
        else:
            # Add note
            note_text = parts[1]
            self._notes.setdefault(target, []).append(note_text)
            _con.print(f"[green]Note added for {target}[/green]")

    def do_creds(self, arg: str) -> None:
        """creds [add|list|export]  — Manage captured credentials"""
        parts = arg.strip().split(None, 1)
        subcommand = parts[0] if parts else "list"
        if subcommand == "list":
            cred_loot = [l for l in self._loot if l.get("type") == "credential"]
            if not cred_loot:
                _con.print("[dim]No credentials captured yet.[/dim]")
                return
            _con.print(f"\n[bold red]Captured Credentials ({len(cred_loot)}):[/bold red]")
            for c in cred_loot:
                _con.print(f"  [cyan]{c.get('target','?'):20}[/cyan] {c.get('data','?')[:60]}")
        elif subcommand == "add" and len(parts) > 1:
            self._loot.append({
                "type": "credential",
                "target": "manual",
                "data": parts[1],
                "added_at": datetime.utcnow().isoformat(),
            })
            _con.print("[green]Credential added[/green]")

    # ─────────────────────────────────────────────────────────────────
    # Reporting / Spool
    # ─────────────────────────────────────────────────────────────────

    def do_report(self, arg: str) -> None:
        """report [html|pdf|md|json|xlsx] [output_path]  — Generate engagement report"""
        parts = arg.strip().split()
        fmt = parts[0].lower() if parts else "html"
        out_path = parts[1] if len(parts) > 1 else f"data/report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        _con.print(f"[cyan]Generating {fmt.upper()} report → {out_path}[/cyan]")
        try:
            from framework.reporting.engine import report_engine
            findings_data = []
            try:
                from framework.db.database import db
                findings_data = db.list_findings(limit=1000)
            except Exception:
                pass
            from framework.reporting.engine import Finding as RF, Severity as RS
            findings_objs = [
                RF(
                    title=f.get("title",""),
                    target=f.get("target",""),
                    severity=RS(f.get("severity","info")),
                    description=f.get("description",""),
                    category=f.get("category","general"),
                )
                for f in findings_data
            ]
            path = report_engine.generate(
                title=f"RTF Engagement Report — {self._workspace}",
                findings=findings_objs,
                format=fmt,
                output_path=out_path,
                metadata={"workspace": self._workspace, "operator": os.environ.get("USER","unknown")},
            )
            _con.print(f"[green]✓ Report saved: {path}[/green]")
        except Exception as e:
            _con.print(f"[red]Report error: {e}[/red]")

    def do_spool(self, arg: str) -> None:
        """spool [filepath|off]  — Log console output to file"""
        path = arg.strip()
        if path == "off" or not path:
            _con.stop_spool()
            _con.print("[green]Spool stopped[/green]")
        else:
            _con.start_spool(path)
            _con.print(f"[green]Spooling to: {path}[/green]")

    # ─────────────────────────────────────────────────────────────────
    # DB / Jobs / Findings shortcuts
    # ─────────────────────────────────────────────────────────────────

    def do_jobs(self, _: str) -> None:
        """jobs  — Show recent jobs"""
        self._show_jobs()

    def do_findings(self, arg: str) -> None:
        """findings [--severity critical|high|medium|low|info] [--limit N]"""
        severity = None
        limit = 50
        parts = arg.split()
        i = 0
        while i < len(parts):
            if parts[i] == "--severity" and i + 1 < len(parts):
                severity = parts[i + 1]
                i += 2
            elif parts[i] == "--limit" and i + 1 < len(parts):
                try:
                    limit = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1
        try:
            from framework.db.database import db
            findings = db.list_findings(severity=severity, limit=limit)
        except Exception:
            _con.print("[yellow]DB not available[/yellow]")
            return
        if not findings:
            _con.print("[dim]No findings.[/dim]")
            return
        sev_colors = {"critical": "bold red", "high": "red", "medium": "yellow", "low": "green", "info": "blue"}
        for f in findings:
            sev = f.get("severity", "info").lower()
            color = sev_colors.get(sev, "white")
            _con.print(f"  [{color}]{sev.upper():8}[/{color}] {f.get('title','')[:60]:60}  [cyan]{f.get('target','')[:30]}[/cyan]")

    def do_db_status(self, _: str) -> None:
        """db_status  — Show database connection status"""
        try:
            from framework.db.database import db
            jobs = db.count_jobs()
            findings = db.count_findings()
            targets = db.count_targets()
            _con.print(f"[green]✓ Database connected[/green]")
            _con.print(f"  Jobs     : [bold]{jobs}[/bold]")
            _con.print(f"  Findings : [bold]{findings}[/bold]")
            _con.print(f"  Targets  : [bold]{targets}[/bold]")
        except Exception as e:
            _con.print(f"[red]✗ Database error: {e}[/red]")

    def do_targets(self, arg: str) -> None:
        """targets [add <value> [type]]  — Manage target list"""
        parts = arg.strip().split()
        if parts and parts[0] == "add":
            if len(parts) < 2:
                _con.print("[red]Usage: targets add <value> [type][/red]")
                return
            val = parts[1]
            typ = parts[2] if len(parts) > 2 else "domain"
            try:
                from framework.db.database import db
                db.add_target(val, typ)
                _con.print(f"[green]Target added: {val} ({typ})[/green]")
            except Exception as e:
                _con.print(f"[red]Error: {e}[/red]")
        else:
            try:
                from framework.db.database import db
                targets = db.list_targets(limit=50)
                if not targets:
                    _con.print("[dim]No targets.[/dim]")
                    return
                for t in targets:
                    _con.print(f"  [cyan]{t.get('type','?'):10}[/cyan] [bold]{t.get('value','')}[/bold]")
            except Exception as e:
                _con.print(f"[red]Error: {e}[/red]")

    # ─────────────────────────────────────────────────────────────────
    # Save / Load / Options shortcuts
    # ─────────────────────────────────────────────────────────────────

    def do_options(self, _: str) -> None:
        """options  — Alias for: show options"""
        self._show_options()

    def do_save(self, arg: str) -> None:
        """save <file.json>  — Save current module/options as resource file"""
        path = arg.strip()
        if not path:
            _con.print("[red]Usage: save <file.json>[/red]")
            return
        payload = {
            "module": self._active_path,
            "options": self._options,
            "globals": self._global_opts,
            "workspace": self._workspace,
            "saved_at": datetime.utcnow().isoformat(),
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _con.print(f"[green]Saved: {path}[/green]")

    def do_load(self, arg: str) -> None:
        """load <file.json>  — Load module/options from resource file"""
        path = arg.strip()
        if not path:
            _con.print("[red]Usage: load <file.json>[/red]")
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            _con.print(f"[red]Error loading file: {e}[/red]")
            return
        if data.get("globals"):
            self._global_opts.update(data["globals"])
        if data.get("module"):
            self.do_use(data["module"])
        for k, v in (data.get("options") or {}).items():
            self._options[k] = v
            if self._active_module:
                try:
                    self._active_module.set(k, v)
                except Exception:
                    pass
        _con.print(f"[green]Loaded: {path}[/green]")

    # ─────────────────────────────────────────────────────────────────
    # Misc
    # ─────────────────────────────────────────────────────────────────

    def do_reload(self, _: str) -> None:
        """reload  — Hot-reload all modules from disk"""
        self._history.append("reload")
        try:
            from framework.modules.loader import module_loader
            count = module_loader.load_all()
            _con.print(f"[green]✓ Reloaded {count} modules[/green]")
        except Exception as e:
            _con.print(f"[red]Reload error: {e}[/red]")

    def do_banner(self, _: str) -> None:
        """banner  — Display random operator quote"""
        if _HAS_RICH:
            rc = RichConsole()
            rc.print(Panel(f"[italic]{random.choice(QUOTES)}[/italic]",
                           border_style="red", title="[bold]RTF[/bold]"))
        else:
            print(f"\n  {random.choice(QUOTES)}\n")

    def do_color(self, arg: str) -> None:
        """color [on|off]  — Toggle Rich color output"""
        a = arg.strip().lower()
        if a == "off":
            _con._color = False
            _con.print("[dim]Color output disabled[/dim]")
        else:
            _con._color = True
            _con.print("[green]Color output enabled[/green]")

    def do_version(self, _: str) -> None:
        """version  — Print framework version"""
        _con.print("[bold green]RedTeam Framework v2.0.0[/bold green]")
        _con.print("[dim]Enterprise RedTeam Platform — Professional Grade[/dim]")

    def do_clear(self, _: str) -> None:
        """clear  — Clear the terminal screen"""
        os.system("clear" if os.name != "nt" else "cls")

    def do_exit(self, _: str) -> bool:
        """exit  — Quit the console"""
        _con.print("[dim]Goodbye. Stay authorized.[/dim]")
        return True

    def do_EOF(self, _: str) -> bool:
        """Handle EOF (Ctrl-D or piped stdin exhausted) — exit cleanly."""
        _con.print("")  # newline after ^D
        return self.do_exit("")

    do_quit = do_exit  # 'quit' as alias

    do_quit = do_exit

    def emptyline(self) -> bool:
        """Do nothing on empty input (no repeat last command)."""
        return False

    # ─────────────────────────────────────────────────────────────────
    # Help overrides
    # ─────────────────────────────────────────────────────────────────

    def do_help(self, arg: str) -> None:
        """help [command]  — Show help"""
        if arg:
            super().do_help(arg)
            return
        _con.print("\n[bold red]RTF v2.0 — Command Reference[/bold red]")
        sections = {
            "Module Management": [
                ("use <path>", "Select a module"),
                ("back", "Deselect module"),
                ("set <k> <v>", "Set option"),
                ("setg <k> <v>", "Set global option (persistent)"),
                ("unset/unsetg", "Clear option"),
                ("show [options|modules|…]", "Show info"),
                ("info [path]", "Show module details"),
                ("search <term>", "Search modules"),
                ("reload", "Hot-reload modules"),
            ],
            "Execution": [
                ("run / exploit", "Execute active module"),
                ("run_workflow <n>", "Run a workflow"),
                ("workflows", "List workflows"),
                ("resource <file.rc>", "Run commands from file"),
            ],
            "Workspace & Data": [
                ("workspace [name]", "Switch workspace"),
                ("targets", "Manage targets"),
                ("jobs", "Show recent jobs"),
                ("findings", "Show findings"),
                ("notes [target] [text]", "Investigation notes"),
                ("creds", "Credential store"),
                ("db_status", "Database status"),
            ],
            "Reporting & Output": [
                ("report [fmt] [path]", "Generate report"),
                ("spool [file|off]", "Log output to file"),
                ("grep <pat> <cmd>", "Filter command output"),
                ("save <file>", "Save module state"),
                ("load <file>", "Load module state"),
            ],
            "Tools": [
                ("tools [--installed|--missing]", "List tools"),
                ("install <name>", "Install a tool"),
            ],
            "Console": [
                ("history", "Show command history"),
                ("!N", "Replay history command N"),
                ("banner", "Random quote"),
                ("color on|off", "Toggle color"),
                ("clear", "Clear screen"),
                ("version", "Show version"),
                ("exit / quit", "Quit"),
            ],
        }
        for section, cmds in sections.items():
            _con.print(f"\n  [bold cyan]{section}[/bold cyan]")
            for cmd_name, desc in cmds:
                _con.print(f"    [green]{cmd_name:35}[/green] [dim]{desc}[/dim]")
        _con.print()


def run_console() -> None:
    """Entry point for the interactive console."""
    console = RTFConsole()
    console.start()
