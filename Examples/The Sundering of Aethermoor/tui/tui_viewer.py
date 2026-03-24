#!/usr/bin/env python3
"""
Agentic Game Session TUI Viewer
================================
A Textual-based terminal UI for viewing and interacting with
agentic game sessions. Built for The Sundering of Aethermoor.

Usage:
    python tui_viewer.py [game_directory] [--terminal true|false]

If no directory is provided, uses the current directory.
Use --terminal false to disable the integrated PTY terminal panel.
"""

import argparse
import copy
import fcntl
import json
import os
import pty
import re
import struct
import subprocess
import termios
import unicodedata
from pathlib import Path
from typing import Optional

import pyte
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual.events import Key, Paste, MouseDown, MouseMove, MouseUp
from textual.reactive import reactive
from textual.widgets import (
    Header,
    Footer,
    Static,
    Label,
    TabbedContent,
    TabPane,
    DataTable,
    RichLog,
    Input,
    Button,
    Rule,
    Markdown,
)
from textual.css.query import NoMatches
from textual.strip import Strip
from rich.segment import Segment
from rich.style import Style as RichStyle
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from rich.markup import escape


# ─── PTY Terminal Widget ─────────────────────────────────────────────────────

PYTE_TO_RICH_COLORS = {
    "black": "black", "red": "red", "green": "green", "brown": "yellow",
    "blue": "blue", "magenta": "magenta", "cyan": "cyan", "white": "white",
    "brightblack": "bright_black", "brightred": "bright_red",
    "brightgreen": "bright_green", "brightyellow": "bright_yellow",
    "brightblue": "bright_blue", "brightmagenta": "bright_magenta",
    "brightcyan": "bright_cyan", "brightwhite": "bright_white",
}


class EnhancedScreen(pyte.HistoryScreen):
    """HistoryScreen with alternate screen buffer (modes 47/1047/1049)."""

    def __init__(self, columns, lines, history=1000, ratio=0.5):
        super().__init__(columns, lines, history=history, ratio=ratio)
        self._saved_buffer = None
        self._saved_cursor = None
        self._saved_history = None
        self._in_alternate = False

    def set_mode(self, *modes, **kwargs):
        if kwargs.get("private"):
            for mode in modes:
                if mode in (47, 1047, 1049):
                    self._enter_alternate()
                    break
        super().set_mode(*modes, **kwargs)

    def reset_mode(self, *modes, **kwargs):
        if kwargs.get("private"):
            for mode in modes:
                if mode in (47, 1047, 1049):
                    self._leave_alternate()
                    break
        super().reset_mode(*modes, **kwargs)

    def _enter_alternate(self):
        if not self._in_alternate:
            self._saved_buffer = copy.deepcopy(self.buffer)
            self._saved_cursor = copy.copy(self.cursor)
            self._saved_history = copy.deepcopy(self.history)
            self.erase_in_display(2)
            self._in_alternate = True

    def _leave_alternate(self):
        if self._in_alternate:
            self.buffer = self._saved_buffer
            self.cursor = self._saved_cursor
            self.history = self._saved_history
            self._in_alternate = False
            self.dirty.update(range(self.lines))

    # pyte's CSI dispatcher passes private=True for '?' prefixed sequences,
    # but several Screen methods don't accept that kwarg. Override them to
    # absorb the extra keyword so the parser doesn't crash on sequences
    # emitted by modern shells and tools (e.g., opencode, kitty, ghostty).
    def report_device_status(self, *args, **kwargs):
        kwargs.pop("private", None)
        super().report_device_status(*args, **kwargs)

    def report_device_attributes(self, *args, **kwargs):
        kwargs.pop("private", None)
        super().report_device_attributes(*args, **kwargs)

    def prev_page(self):
        if not self._in_alternate:
            super().prev_page()

    def next_page(self):
        if not self._in_alternate:
            super().next_page()


class PtyTerminal(Static, can_focus=True):
    """A terminal widget that embeds a real PTY shell using pyte."""

    DEFAULT_CSS = """
    PtyTerminal {
        height: 1fr;
        width: 1fr;
        border: solid grey;
    }
    PtyTerminal:focus {
        border: solid $accent;
    }
    """

    def __init__(self, command: str = "bash", **kwargs):
        super().__init__(**kwargs)
        self.command = command
        self.master_fd: int | None = None
        self._process: subprocess.Popen | None = None
        self._pty_screen: EnhancedScreen | None = None
        self._pty_stream: pyte.Stream | None = None
        self._reader_running = False
        # Selection state for copy support
        self._sel_start: tuple[int, int] | None = None  # (x, y)
        self._sel_end: tuple[int, int] | None = None    # (x, y)
        self._selecting = False

    def on_mount(self) -> None:
        cols = max(self.size.width - 2, 10)
        rows = max(self.size.height - 2, 5)
        self._pty_screen = EnhancedScreen(cols, rows)
        self._pty_stream = pyte.Stream(self._pty_screen)

    def start(self) -> None:
        """Spawn a shell in a PTY using subprocess.Popen."""
        master_fd, slave_fd = pty.openpty()
        self.master_fd = master_fd

        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLUMNS"] = str(self._pty_screen.columns if self._pty_screen else 80)
        env["LINES"] = str(self._pty_screen.lines if self._pty_screen else 24)

        self._process = subprocess.Popen(
            [self.command],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            preexec_fn=os.setsid,
            close_fds=True,
        )
        os.close(slave_fd)

        # Set master to non-blocking
        flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # Relay pyte's device attribute responses back to the PTY
        _master = self.master_fd
        def _write_to_pty(data):
            try:
                os.write(_master, data.encode("utf-8"))
            except OSError:
                pass
        if self._pty_screen:
            self._pty_screen.write_process_input = _write_to_pty

        self._reader_running = True
        self._poll_pty()

    def _resize_pty(self, cols: int, rows: int) -> None:
        if self.master_fd is not None and self._pty_screen is not None:
            self._pty_screen.resize(rows, cols)
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except OSError:
                pass

    def on_resize(self, event) -> None:
        self._trigger_resize()

    def on_focus(self, event) -> None:
        self._trigger_resize()

    def on_blur(self, event) -> None:
        self._trigger_resize()

    def _trigger_resize(self) -> None:
        cols = max(self.size.width - 2, 10)
        rows = max(self.size.height - 2, 5)
        if self._pty_screen and (cols != self._pty_screen.columns or rows != self._pty_screen.lines):
            self._resize_pty(cols, rows)

    def _poll_pty(self) -> None:
        """Read available data from the PTY and feed it to pyte."""
        if not self._reader_running or self.master_fd is None:
            return
        try:
            data = os.read(self.master_fd, 65536)
            if data:
                self._pty_stream.feed(data.decode("utf-8", errors="replace"))
                if self._pty_screen.dirty:
                    self.refresh()
                    self._pty_screen.dirty.clear()
        except (OSError, BlockingIOError):
            pass
        if self._reader_running:
            self.set_timer(0.02, self._poll_pty)

    def _write_bytes(self, data: bytes) -> None:
        """Write raw bytes to the PTY master fd."""
        if self.master_fd is not None:
            try:
                os.write(self.master_fd, data)
            except OSError:
                pass

    # ── Clipboard: Paste ──────────────────────────────────────────────────

    def on_paste(self, event: Paste) -> None:
        """Handle paste from system clipboard into the PTY.

        If the shell has bracketed paste mode enabled (mode 2004), the pasted
        text is wrapped in escape sequences so the shell knows it's a paste
        and doesn't interpret special characters (like newlines) as commands.
        """
        if self.master_fd is None or not self.has_focus:
            return
        text = event.text
        if not text:
            return
        # Bracketed paste mode: wrap so shell treats it as literal paste
        bracketed = self._pty_screen and (2004 in self._pty_screen.mode)
        payload = text.encode("utf-8")
        if bracketed:
            self._write_bytes(b"\x1b[200~" + payload + b"\x1b[201~")
        else:
            self._write_bytes(payload)
        event.prevent_default()
        event.stop()

    # ── Clipboard: Mouse selection & Copy ─────────────────────────────────

    def _sel_ordered(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """Return selection endpoints in reading order (top-left, bottom-right)."""
        if self._sel_start is None or self._sel_end is None:
            return None
        s, e = self._sel_start, self._sel_end
        if (s[1], s[0]) > (e[1], e[0]):
            s, e = e, s
        return s, e

    def _is_selected(self, x: int, y: int) -> bool:
        """Check if cell (x, y) is within the current selection."""
        sel = self._sel_ordered()
        if sel is None:
            return False
        (sx, sy), (ex, ey) = sel
        if sy == ey:
            return y == sy and sx <= x <= ex
        if y == sy:
            return x >= sx
        if y == ey:
            return x <= ex
        return sy < y < ey

    def _get_selected_text(self) -> str:
        """Extract the text content of the current selection from pyte buffer."""
        sel = self._sel_ordered()
        if sel is None or self._pty_screen is None:
            return ""
        (sx, sy), (ex, ey) = sel
        lines = []
        for row in range(sy, ey + 1):
            line_buf = self._pty_screen.buffer[row]
            start = sx if row == sy else 0
            end = ex if row == ey else self._pty_screen.columns - 1
            chars = []
            col = start
            while col <= end:
                ch = line_buf[col].data
                if ch:
                    chars.append(ch)
                    eaw = unicodedata.east_asian_width(ch)
                    col += 2 if eaw in ('W', 'F') else 1
                else:
                    col += 1
            lines.append("".join(chars).rstrip())
        return "\n".join(lines)

    def _clear_selection(self) -> None:
        if self._sel_start is not None:
            self._sel_start = None
            self._sel_end = None
            self._selecting = False
            self.refresh()

    def on_mouse_down(self, event: MouseDown) -> None:
        if event.button == 1:
            # Left click: start a new selection
            self._sel_start = (event.x, event.y)
            self._sel_end = (event.x, event.y)
            self._selecting = True
            self.capture_mouse()
            self.refresh()
            event.stop()

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._selecting and self._pty_screen:
            # Clamp to screen bounds
            x = max(0, min(event.x, self._pty_screen.columns - 1))
            y = max(0, min(event.y, self._pty_screen.lines - 1))
            self._sel_end = (x, y)
            self.refresh()
            event.stop()

    def on_mouse_up(self, event: MouseUp) -> None:
        if event.button == 1 and self._selecting:
            self._selecting = False
            self.release_mouse()
            # If start == end, it was just a click — clear selection, don't copy
            if self._sel_start == self._sel_end:
                self._clear_selection()
                return
            text = self._get_selected_text()
            if text:
                self.app.copy_to_clipboard(text)
                self.app.notify("Copied to clipboard", timeout=1.5)
            event.stop()

    def on_key(self, event: Key) -> None:
        if self.master_fd is None or not self.has_focus:
            return

        # Any keypress clears the visual selection
        if self._sel_start is not None:
            self._clear_selection()

        # Scrollback navigation (don't send to PTY)
        if event.key == "shift+pageup" and self._pty_screen:
            self._pty_screen.prev_page()
            self.refresh()
            event.prevent_default()
            event.stop()
            return
        if event.key == "shift+pagedown" and self._pty_screen:
            self._pty_screen.next_page()
            self.refresh()
            event.prevent_default()
            event.stop()
            return

        # Check if cursor keys are in application mode (DECCKM, private mode 1)
        app_cursor = self._pty_screen and (32 in self._pty_screen.mode)

        key_map = {
            "enter": "\r", "escape": "\x1b", "tab": "\t",
            "shift+tab": "\x1b[Z",
            "backspace": "\x7f", "delete": "\x1b[3~",
            "up": "\x1bOA" if app_cursor else "\x1b[A",
            "down": "\x1bOB" if app_cursor else "\x1b[B",
            "right": "\x1bOC" if app_cursor else "\x1b[C",
            "left": "\x1bOD" if app_cursor else "\x1b[D",
            "home": "\x1b[H", "end": "\x1b[F",
            "insert": "\x1b[2~",
            "pageup": "\x1b[5~", "pagedown": "\x1b[6~",
            "f1": "\x1bOP", "f2": "\x1bOQ", "f3": "\x1bOR", "f4": "\x1bOS",
            "f5": "\x1b[15~", "f6": "\x1b[17~", "f7": "\x1b[18~",
            "f8": "\x1b[19~", "f9": "\x1b[20~", "f10": "\x1b[21~",
            "f11": "\x1b[23~", "f12": "\x1b[24~",
        }

        char = key_map.get(event.key)
        if char is None:
            if event.key.startswith("ctrl+") and len(event.key) == 6:
                ch = event.key[-1]
                char = chr(ord(ch) - ord('a') + 1)
            elif event.character:
                char = event.character
            else:
                return

        try:
            os.write(self.master_fd, char.encode("utf-8"))
        except OSError:
            pass
        event.prevent_default()
        event.stop()

    def get_content_width(self, container, viewport):
        if self._pty_screen:
            return self._pty_screen.columns
        return container.width

    def get_content_height(self, container, viewport, width):
        if self._pty_screen:
            return self._pty_screen.lines
        return container.height

    def render_line(self, y: int) -> Strip:
        if self._pty_screen is None or y >= self._pty_screen.lines:
            return Strip.blank(self.size.width)

        has_selection = self._sel_start is not None and self._sel_end is not None
        segments = []
        line = self._pty_screen.buffer[y]
        x = 0
        while x < self._pty_screen.columns:
            char_data = line[x]
            ch = char_data.data
            if not ch:
                # Stub cell from wide character — skip
                x += 1
                continue
            fg_color = None
            bg_color = None

            fg = char_data.fg
            if fg and fg != "default":
                fg_color = PYTE_TO_RICH_COLORS.get(fg, f"#{fg}" if len(fg) == 6 and all(c in "0123456789abcdefABCDEF" for c in fg) else fg)
            bg = char_data.bg
            if bg and bg != "default":
                bg_color = PYTE_TO_RICH_COLORS.get(bg, f"#{bg}" if len(bg) == 6 and all(c in "0123456789abcdefABCDEF" for c in bg) else bg)

            is_cursor = (
                self.has_focus
                and y == self._pty_screen.cursor.y
                and x == self._pty_screen.cursor.x
            )

            selected = has_selection and self._is_selected(x, y)

            # XOR: if char is reverse AND cursor is here, they cancel out
            effective_reverse = char_data.reverse ^ is_cursor

            if selected:
                # Selection highlight: white text on blue background
                style = RichStyle(
                    color="white",
                    bgcolor="#354a6d",
                    bold=char_data.bold,
                    italic=char_data.italics,
                    underline=char_data.underscore,
                    strike=char_data.strikethrough,
                )
            else:
                style = RichStyle(
                    color=fg_color,
                    bgcolor=bg_color,
                    bold=char_data.bold,
                    italic=char_data.italics,
                    underline=char_data.underscore,
                    strike=char_data.strikethrough,
                    reverse=effective_reverse,
                )
            segments.append(Segment(ch, style))

            # Skip stub cell for wide (2-cell) characters
            eaw = unicodedata.east_asian_width(ch)
            x += 2 if eaw in ('W', 'F') else 1

        return Strip(segments, self._pty_screen.columns)

    def on_mouse_scroll_up(self, event) -> None:
        if self._pty_screen:
            self._pty_screen.prev_page()
            self.refresh()
            event.stop()

    def on_mouse_scroll_down(self, event) -> None:
        if self._pty_screen:
            self._pty_screen.next_page()
            self.refresh()
            event.stop()

    def cleanup(self) -> None:
        self._reader_running = False
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    self._process.kill()
                except OSError:
                    pass
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
        self.master_fd = None


# ─── Session Parser ───────────────────────────────────────────────────────────

class SessionParser:
    """Parses all markdown and JSON files from an agentic game session."""

    def __init__(self, game_dir: str):
        self.game_dir = Path(game_dir)
        self.session_dir = self.game_dir / "session"
        self.settings_dir = self.game_dir / "settings"
        self.game_data_dir = self.game_dir / "game"
        self.tools_dir = self.game_dir / "tools"

    def _read(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError):
            return ""

    # ── Player ────────────────────────────────────────────────────────────
    def parse_player(self) -> dict:
        text = self._read(self.session_dir / "player.md")
        if not text:
            return {}
        p = {}
        # Name
        m = re.search(r"# Player:\s*(.+)", text)
        p["name"] = m.group(1).strip() if m else "Unknown"
        # Class / Subclass
        m = re.search(r"\*\*Class:\*\*\s*(.+)", text)
        p["class"] = m.group(1).strip() if m else "Unknown"
        # Save name
        m = re.search(r"\*\*Save Name:\*\*\s*(.+)", text)
        p["save_name"] = m.group(1).strip() if m else ""
        # Stats table
        p["stats"] = {}
        for m in re.finditer(r"\|\s*(HP|MP|STR|INT|AGI)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", text):
            p["stats"][m.group(1)] = {"base": int(m.group(2)), "current": int(m.group(3))}
        # Rift Points
        m = re.search(r"\*\*Rift Points:\*\*\s*(\d+)\s*/\s*(\d+)", text)
        if m:
            p["rift_points"] = {"current": int(m.group(1)), "max": int(m.group(2))}
        # Shards
        p["shards"] = []
        for m in re.finditer(r"- \[([ xX])\]\s*(.+?)(?:\n|$)", text):
            p["shards"].append({
                "collected": m.group(1).strip().lower() == "x",
                "name": m.group(2).strip()
            })
        # Abilities
        p["abilities"] = []
        in_abilities = False
        for line in text.split("\n"):
            if "## Active Abilities" in line:
                in_abilities = True
                continue
            if in_abilities and line.startswith("## "):
                break
            if in_abilities and line.startswith("- **"):
                p["abilities"].append(line.strip("- ").strip())
        # Status Effects
        p["status_effects"] = []
        in_status = False
        for line in text.split("\n"):
            if "## Status Effects" in line:
                in_status = True
                continue
            if in_status and line.startswith("## "):
                break
            if in_status and line.strip() and line.strip().lower() != "none":
                if line.startswith("- "):
                    p["status_effects"].append(line.strip("- ").strip())
                elif not line.startswith("#"):
                    p["status_effects"].append(line.strip())
        # Turn counter
        m = re.search(r"\*\*Turns Elapsed:\*\*\s*(\d+)", text)
        p["turns"] = int(m.group(1)) if m else 0
        return p

    # ── World State ───────────────────────────────────────────────────────
    def parse_world_state(self) -> dict:
        text = self._read(self.session_dir / "world_state.md")
        if not text:
            return {}
        w = {}
        m = re.search(r"\*\*Current Corruption:\*\*\s*(\d+)%", text)
        w["corruption"] = int(m.group(1)) if m else 0
        m = re.search(r"\*\*Corruption Rate:\*\*\s*([\d.]+)%", text)
        w["corruption_rate"] = float(m.group(1)) if m else 1.0
        m = re.search(r"\*\*Status:\*\*\s*(\w+)", text)
        w["status"] = m.group(1) if m else "Unknown"
        # Realms
        w["realms"] = []
        for m in re.finditer(r"\|\s*(Emberveil|Thornwood|Crystalmere|Ashen Wastes|Skyreach)\s*\|\s*(\w+)\s*\|\s*(.+?)\s*\|", text):
            w["realms"].append({"name": m.group(1), "status": m.group(2), "notes": m.group(3).strip()})
        # Shards
        w["shards"] = []
        for m in re.finditer(r"\|\s*(\w[\w\s]*Shard)\s*\|\s*(.+?)\s*\|\s*(\w[\w\s]*)\s*\|", text):
            w["shards"].append({"name": m.group(1).strip(), "location": m.group(2).strip(), "status": m.group(3).strip()})
        # Malachar
        m = re.search(r"Malachar's Awareness.*?\n\*\*Level:\*\*\s*(\w+)", text, re.DOTALL)
        w["malachar"] = m.group(1) if m else "Unknown"
        # Rift Gates
        w["rift_gates"] = []
        in_gates = False
        for line in text.split("\n"):
            if "Known Rift Gate" in line:
                in_gates = True
                continue
            if in_gates and line.startswith("- "):
                w["rift_gates"].append(line.strip("- ").strip())
        return w

    # ── Location ──────────────────────────────────────────────────────────
    def parse_location(self) -> dict:
        text = self._read(self.session_dir / "location.md")
        if not text:
            return {}
        loc = {}
        m = re.search(r"\*\*Realm:\*\*\s*(.+)", text)
        loc["realm"] = m.group(1).strip() if m else ""
        m = re.search(r"\*\*Area:\*\*\s*(.+)", text)
        loc["area"] = m.group(1).strip() if m else ""
        m = re.search(r"\*\*Zone:\*\*\s*(.+)", text)
        loc["zone"] = m.group(1).strip() if m else ""
        # Description
        m = re.search(r"## Description\n(.+?)(?=\n## )", text, re.DOTALL)
        loc["description"] = m.group(1).strip() if m else ""
        # Exits
        loc["exits"] = []
        in_exits = False
        for line in text.split("\n"):
            if "## Exits" in line:
                in_exits = True
                continue
            if in_exits and line.startswith("## "):
                break
            if in_exits and line.startswith("- "):
                loc["exits"].append(line.strip("- ").strip())
        # Points of interest
        loc["poi"] = []
        in_poi = False
        for line in text.split("\n"):
            if "## Points of Interest" in line:
                in_poi = True
                continue
            if in_poi and line.startswith("## "):
                break
            if in_poi and line.startswith("- "):
                loc["poi"].append(line.strip("- ").strip())
        # NPCs
        m = re.search(r"## NPCs Present\n(.+?)(?=\n## )", text, re.DOTALL)
        loc["npcs"] = m.group(1).strip() if m else "None"
        # Rift Gate
        m = re.search(r"## Rift Gate\n(.+?)(?=\n## |\Z)", text, re.DOTALL)
        loc["rift_gate"] = m.group(1).strip() if m else "None"
        # Void Presence
        m = re.search(r"## Void Presence\n(.+?)(?=\n## |\Z)", text, re.DOTALL)
        loc["void_presence"] = m.group(1).strip() if m else "None"
        return loc

    # ── Inventory ─────────────────────────────────────────────────────────
    def parse_inventory(self) -> dict:
        text = self._read(self.session_dir / "inventory.md")
        if not text:
            return {}
        inv = {}
        m = re.search(r"\*\*Gold:\*\*\s*(\d+)", text)
        inv["gold"] = int(m.group(1)) if m else 0
        m = re.search(r"\*\*Slots Used:\*\*\s*(\d+)\s*/\s*(\d+)", text)
        inv["slots"] = {"used": int(m.group(1)), "max": int(m.group(2))} if m else {"used": 0, "max": 20}

        def parse_table(header: str) -> list[dict]:
            pattern = rf"## {header}\n\|.+\|\n\|[-\s|]+\|\n((?:\|.+\|\n?)*)"
            m = re.search(pattern, text)
            if not m:
                return []
            rows = []
            for line in m.group(1).strip().split("\n"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                rows.append(cells)
            return rows

        inv["weapons"] = parse_table("Weapons")
        inv["armor"] = parse_table("Armor & Accessories")
        inv["consumables"] = parse_table("Consumables")
        inv["quest_items"] = parse_table("Quest Items")
        inv["artifacts"] = parse_table("Artifacts")
        return inv

    # ── Companions ────────────────────────────────────────────────────────
    def parse_companions(self) -> dict:
        text = self._read(self.session_dir / "companions.md")
        if not text:
            return {}
        comp = {}
        m = re.search(r"\*\*Slots Used:\*\*\s*(\d+)\s*/\s*(\d+)", text)
        comp["slots"] = {"used": int(m.group(1)), "max": int(m.group(2))} if m else {"used": 0, "max": 3}
        comp["companions"] = []
        sections = re.split(r"\n---\n", text)
        for sec in sections:
            m = re.search(r"## (.+)", sec)
            if not m:
                continue
            c = {"name": m.group(1).strip()}
            for field, key in [
                (r"\*\*Race/Class:\*\*\s*(.+)", "race_class"),
                (r"\*\*HP:\*\*\s*(\d+)\s*/\s*(\d+)", "hp"),
                (r"\*\*MP:\*\*\s*(\d+)\s*/\s*(\d+)", "mp"),
                (r"\*\*Special Ability:\*\*\s*(.+)", "ability"),
                (r"\*\*Status:\*\*\s*(.+)", "status"),
                (r"\*\*Disposition toward player:\*\*\s*(.+)", "disposition"),
                (r"\*\*Notes:\*\*\s*(.+)", "notes"),
            ]:
                fm = re.search(field, sec)
                if fm:
                    if key in ("hp", "mp"):
                        c[key] = {"current": int(fm.group(1)), "max": int(fm.group(2))}
                    else:
                        c[key] = fm.group(1).strip()
            comp["companions"].append(c)
        return comp

    # ── NPCs ──────────────────────────────────────────────────────────────
    def parse_npcs(self) -> list[dict]:
        text = self._read(self.session_dir / "npcs.md")
        if not text:
            return []
        npcs = []
        sections = re.split(r"\n---\n", text)
        for sec in sections:
            m = re.search(r"## (.+)", sec)
            if not m:
                continue
            npc = {"name": m.group(1).strip()}
            for field, key in [
                (r"\*\*Location:\*\*\s*(.+)", "location"),
                (r"\*\*Disposition:\*\*\s*(.+)", "disposition"),
                (r"\*\*Status:\*\*\s*(.+)", "status"),
                (r"\*\*Quests Given:\*\*\s*(.+)", "quests_given"),
                (r"\*\*Quests Completed:\*\*\s*(.+)", "quests_completed"),
                (r"\*\*Notes:\*\*\s*(.+)", "notes"),
            ]:
                fm = re.search(field, sec)
                if fm:
                    npc[key] = fm.group(1).strip()
            npcs.append(npc)
        return npcs

    # ── Quests ────────────────────────────────────────────────────────────
    def parse_quests(self) -> dict:
        text = self._read(self.session_dir / "quests.md")
        if not text:
            return {"active": [], "completed": []}

        def parse_quest_section(section_text: str) -> list[dict]:
            quests = []
            blocks = re.split(r"\n---\n", section_text)
            for block in blocks:
                m = re.search(r"### (.+)", block)
                if not m:
                    continue
                q = {"title": m.group(1).strip().rstrip(" ✓")}
                for field, key in [
                    (r"\*\*Given by:\*\*\s*(.+)", "given_by"),
                    (r"\*\*Realm:\*\*\s*(.+)", "realm"),
                    (r"\*\*Objective:\*\*\s*(.+)", "objective"),
                    (r"\*\*Progress:\*\*\s*(.+)", "progress"),
                    (r"\*\*Reward:\*\*\s*(.+)", "reward"),
                    (r"\*\*Completed:\*\*\s*(.+)", "completed_turn"),
                    (r"\*\*Outcome:\*\*\s*(.+)", "outcome"),
                    (r"\*\*Reward received:\*\*\s*(.+)", "reward_received"),
                ]:
                    fm = re.search(field, block)
                    if fm:
                        q[key] = fm.group(1).strip()
                quests.append(q)
            return quests

        active_text = ""
        completed_text = ""
        m = re.search(r"## Active Quests\n(.*?)(?=## Completed Quests|\Z)", text, re.DOTALL)
        if m:
            active_text = m.group(1)
        m = re.search(r"## Completed Quests\n(.*)", text, re.DOTALL)
        if m:
            completed_text = m.group(1)

        return {
            "active": parse_quest_section(active_text),
            "completed": parse_quest_section(completed_text),
        }

    # ── Log ───────────────────────────────────────────────────────────────
    def parse_log(self) -> list[dict]:
        text = self._read(self.session_dir / "log.md")
        if not text:
            return []
        entries = []
        blocks = re.split(r"\n---\n", text)
        for block in blocks:
            m = re.search(r"## \[Turn (\d+)\] — (.+)\n(.+)", block, re.DOTALL)
            if m:
                entries.append({
                    "turn": int(m.group(1)),
                    "title": m.group(2).strip(),
                    "text": m.group(3).strip(),
                })
        return entries

    # ── Settings ──────────────────────────────────────────────────────────
    def parse_settings(self) -> dict:
        text = self._read(self.settings_dir / "custom.json")
        if not text:
            text = self._read(self.settings_dir / "default.json")
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    # ── Background ────────────────────────────────────────────────────────
    def parse_background(self) -> str:
        return self._read(self.game_data_dir / "background.md")

    # ── NPC Definitions ───────────────────────────────────────────────────
    def parse_npc_defs(self) -> str:
        return self._read(self.game_data_dir / "npcs.md")

    # ── Full parse ────────────────────────────────────────────────────────
    def parse_all(self) -> dict:
        return {
            "player": self.parse_player(),
            "world": self.parse_world_state(),
            "location": self.parse_location(),
            "inventory": self.parse_inventory(),
            "companions": self.parse_companions(),
            "npcs": self.parse_npcs(),
            "quests": self.parse_quests(),
            "log": self.parse_log(),
            "settings": self.parse_settings(),
        }


# ─── Helper: progress bar as rich text ────────────────────────────────────────

def bar(current: int, maximum: int, width: int = 20, fill_color: str = "green",
        empty_color: str = "grey37", label: str = "") -> Text:
    if maximum <= 0:
        maximum = 1
    ratio = max(0, min(1, current / maximum))
    filled = int(ratio * width)
    empty = width - filled
    t = Text()
    if label:
        t.append(f"{label} ", style="bold")
    t.append("█" * filled, style=fill_color)
    t.append("░" * empty, style=empty_color)
    t.append(f" {current}/{maximum}", style="bold white")
    return t


def void_bar(pct: int, width: int = 30) -> Text:
    if pct <= 25:
        color = "green"
    elif pct <= 50:
        color = "yellow"
    elif pct <= 75:
        color = "dark_orange"
    else:
        color = "red"
    filled = int(pct / 100 * width)
    empty = width - filled
    t = Text()
    t.append("VOID ", style="bold magenta")
    t.append("█" * filled, style=color)
    t.append("░" * empty, style="grey23")
    t.append(f" {pct}%", style=f"bold {color}")
    return t


def shard_display(shards: list[dict]) -> Text:
    t = Text()
    shard_icons = {
        "Emberveil": ("🔥", "red"),
        "Thornwood": ("🌿", "green"),
        "Crystalmere": ("❄️ ", "cyan"),
        "Ashen": ("💀", "grey70"),
        "Skyreach": ("⚡", "yellow"),
    }
    for s in shards:
        name = s["name"]
        icon = "◆"
        color = "white"
        for key, (ic, col) in shard_icons.items():
            if key in name:
                icon = ic
                color = col
                break
        if s["collected"]:
            t.append(f" {icon} ", style=f"bold {color}")
        else:
            t.append(f" ○ ", style="grey50")
    return t


# ─── Widgets ──────────────────────────────────────────────────────────────────

class CharacterPanel(Static):
    """Displays player character info."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        p = self.data.get("player", {})
        if not p:
            return Group(Text("No player data found.", style="dim"))

        parts = []

        # Title
        title = Text()
        title.append(f"  ⚔  {p.get('name', '?')}  ", style="bold white on dark_blue")
        title.append(f"  {p.get('class', '?')}  ", style="italic cyan")
        parts.append(title)
        parts.append(Text())

        # HP / MP bars
        stats = p.get("stats", {})
        hp = stats.get("HP", {})
        mp = stats.get("MP", {})
        hp_color = "green" if hp.get("current", 0) > hp.get("base", 1) * 0.5 else ("yellow" if hp.get("current", 0) > hp.get("base", 1) * 0.25 else "red")
        parts.append(bar(hp.get("current", 0), hp.get("base", 100), 25, hp_color, label="HP"))
        parts.append(bar(mp.get("current", 0), mp.get("base", 50), 25, "dodger_blue1", label="MP"))

        # Rift Points
        rp = p.get("rift_points", {})
        parts.append(bar(rp.get("current", 0), rp.get("max", 10), 15, "medium_purple", label="RP"))
        parts.append(Text())

        # Core stats line
        stat_line = Text()
        for sn in ["STR", "INT", "AGI"]:
            s = stats.get(sn, {})
            val = s.get("current", 0)
            mod = (val - 10) // 2
            sign = "+" if mod >= 0 else ""
            stat_line.append(f"  {sn} ", style="bold")
            stat_line.append(f"{val}", style="bold cyan")
            stat_line.append(f" ({sign}{mod})  ", style="dim")
        parts.append(stat_line)
        parts.append(Text())

        # Shards
        shard_line = Text("  Shards: ", style="bold")
        collected = sum(1 for s in p.get("shards", []) if s["collected"])
        total = len(p.get("shards", []))
        parts.append(shard_line)
        parts.append(shard_display(p.get("shards", [])))
        parts.append(Text(f"  {collected} / {total} collected", style="dim"))
        parts.append(Text())

        # Turn & Status
        turn_line = Text()
        turn_line.append(f"  Turn: ", style="bold")
        turn_line.append(f"{p.get('turns', 0)}", style="bold yellow")
        parts.append(turn_line)

        # Status effects
        effects = p.get("status_effects", [])
        if effects:
            parts.append(Text())
            parts.append(Text("  Status Effects:", style="bold red"))
            for eff in effects:
                parts.append(Text(f"    ⚠ {eff}", style="red"))

        return Group(*parts)


class WorldPanel(Static):
    """Displays world state."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        w = self.data.get("world", {})
        if not w:
            return Group(Text("No world data found.", style="dim"))

        parts = []

        # Void Corruption
        parts.append(void_bar(w.get("corruption", 0)))
        rate = w.get("corruption_rate", 1.0)
        status = w.get("status", "Unknown")
        status_colors = {"Stable": "green", "Creeping": "yellow", "Critical": "dark_orange", "Catastrophic": "red"}
        sc = status_colors.get(status, "white")
        info = Text()
        info.append(f"  Rate: {rate}%/turn  ", style="dim")
        info.append(f"Status: ", style="bold")
        info.append(status, style=f"bold {sc}")
        parts.append(info)
        parts.append(Text())

        # Malachar
        mal = w.get("malachar", "Unknown")
        mal_colors = {"Dormant": "green", "Watching": "yellow", "Active": "dark_orange", "Pursuing": "red"}
        mc = mal_colors.get(mal, "white")
        mal_line = Text()
        mal_line.append("  Malachar: ", style="bold")
        mal_line.append(mal, style=f"bold {mc}")
        parts.append(mal_line)
        parts.append(Text())

        # Realm table
        realm_table = Table(title="Realm Status", expand=True, show_edge=False, pad_edge=False)
        realm_table.add_column("Realm", style="bold")
        realm_table.add_column("Status")
        realm_table.add_column("Notes", style="dim")
        realm_icons = {"Emberveil": "🔥", "Thornwood": "🌿", "Crystalmere": "❄️ ", "Ashen Wastes": "💀", "Skyreach": "⚡"}
        status_styles = {"Intact": "green", "Damaged": "yellow", "Critical": "red", "Lost": "bright_red"}
        for r in w.get("realms", []):
            icon = realm_icons.get(r["name"], "")
            sty = status_styles.get(r["status"], "white")
            realm_table.add_row(f"{icon} {r['name']}", Text(r["status"], style=sty), r.get("notes", ""))
        parts.append(realm_table)
        parts.append(Text())

        # Rift Gates
        gates = w.get("rift_gates", [])
        if gates:
            parts.append(Text("  Known Rift Gates:", style="bold"))
            for g in gates:
                parts.append(Text(f"    ◊ {g}", style="cyan"))

        return Group(*parts)


class LocationPanel(Static):
    """Displays current location."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        loc = self.data.get("location", {})
        if not loc:
            return Group(Text("No location data found.", style="dim"))

        parts = []

        # Location header
        header = Text()
        header.append(f"  {loc.get('realm', '?')}", style="bold bright_green")
        header.append(f" › ", style="dim")
        header.append(f"{loc.get('area', '?')}", style="bold")
        header.append(f" › ", style="dim")
        header.append(f"{loc.get('zone', '?')}", style="bold yellow")
        parts.append(header)
        parts.append(Text())

        # Description
        desc = loc.get("description", "")
        if desc:
            parts.append(Text(f"  {desc}", style="italic"))
            parts.append(Text())

        # Void Presence
        vp = loc.get("void_presence", "None")
        vp_colors = {"None": "green", "Faint": "yellow", "Strong": "dark_orange", "Overwhelming": "red"}
        vpc = "white"
        for k, v in vp_colors.items():
            if k.lower() in vp.lower():
                vpc = v
                break
        vp_line = Text()
        vp_line.append("  Void: ", style="bold")
        vp_line.append(vp, style=f"italic {vpc}")
        parts.append(vp_line)
        parts.append(Text())

        # Exits
        exits = loc.get("exits", [])
        if exits:
            parts.append(Text("  Exits:", style="bold"))
            for e in exits:
                parts.append(Text(f"    → {e}", style="cyan"))
            parts.append(Text())

        # Points of Interest
        pois = loc.get("poi", [])
        if pois:
            parts.append(Text("  Points of Interest:", style="bold"))
            for poi in pois:
                parts.append(Text(f"    ★ {poi}", style="yellow"))
            parts.append(Text())

        # NPCs
        npcs = loc.get("npcs", "None")
        parts.append(Text(f"  NPCs: ", style="bold") + Text(npcs, style="bright_magenta"))

        # Rift Gate
        rg = loc.get("rift_gate", "None")
        parts.append(Text(f"  Rift Gate: ", style="bold") + Text(rg, style="dim"))

        return Group(*parts)


class InventoryPanel(Static):
    """Displays inventory."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        inv = self.data.get("inventory", {})
        if not inv:
            return Group(Text("No inventory data found.", style="dim"))

        parts = []

        # Header
        gold_line = Text()
        gold_line.append("  💰 Gold: ", style="bold")
        gold_line.append(str(inv.get("gold", 0)), style="bold yellow")
        slots = inv.get("slots", {})
        gold_line.append(f"    📦 Slots: {slots.get('used', 0)}/{slots.get('max', 20)}", style="dim")
        parts.append(gold_line)
        parts.append(Text())

        # Weapons
        weapons = inv.get("weapons", [])
        if weapons:
            wt = Table(title="⚔ Weapons", expand=True, show_edge=False)
            wt.add_column("Item", style="bold")
            wt.add_column("Damage", style="red")
            wt.add_column("Notes", style="dim")
            for row in weapons:
                wt.add_row(*[str(c) for c in row[:3]] if len(row) >= 3 else (*row, ""))
            parts.append(wt)
            parts.append(Text())

        # Armor
        armor = inv.get("armor", [])
        if armor:
            at = Table(title="🛡 Armor", expand=True, show_edge=False)
            at.add_column("Item", style="bold")
            at.add_column("Defense", style="cyan")
            at.add_column("Notes", style="dim")
            for row in armor:
                at.add_row(*[str(c) for c in row[:3]] if len(row) >= 3 else (*row, ""))
            parts.append(at)
            parts.append(Text())

        # Consumables
        consumables = inv.get("consumables", [])
        if consumables:
            ct = Table(title="🧪 Consumables", expand=True, show_edge=False)
            ct.add_column("Item", style="bold")
            ct.add_column("Effect", style="green")
            ct.add_column("Qty", style="yellow")
            for row in consumables:
                ct.add_row(*[str(c) for c in row[:3]] if len(row) >= 3 else (*row, ""))
            parts.append(ct)
            parts.append(Text())

        # Quest Items
        quest_items = inv.get("quest_items", [])
        if quest_items:
            qt = Table(title="📜 Quest Items", expand=True, show_edge=False)
            qt.add_column("Item", style="bold")
            qt.add_column("Quest", style="magenta")
            qt.add_column("Notes", style="dim")
            for row in quest_items:
                qt.add_row(*[str(c) for c in row[:3]] if len(row) >= 3 else (*row, ""))
            parts.append(qt)
            parts.append(Text())

        # Artifacts
        artifacts = inv.get("artifacts", [])
        if artifacts:
            aft = Table(title="✨ Artifacts", expand=True, show_edge=False)
            aft.add_column("Item", style="bold bright_magenta")
            aft.add_column("Power", style="cyan")
            aft.add_column("Notes", style="dim")
            for row in artifacts:
                aft.add_row(*[str(c) for c in row[:3]] if len(row) >= 3 else (*row, ""))
            parts.append(aft)

        return Group(*parts)


class CompanionsPanel(Static):
    """Displays companions."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        comp = self.data.get("companions", {})
        if not comp:
            return Group(Text("No companion data found.", style="dim"))

        parts = []
        slots = comp.get("slots", {})
        parts.append(Text(f"  Party Slots: {slots.get('used', 0)} / {slots.get('max', 3)}", style="bold"))
        parts.append(Text())

        for c in comp.get("companions", []):
            name_line = Text()
            name_line.append(f"  ⚔ {c.get('name', '?')}", style="bold bright_yellow")
            name_line.append(f"  ({c.get('race_class', '?')})", style="dim")
            parts.append(name_line)

            hp = c.get("hp", {})
            mp = c.get("mp", {})
            if hp:
                hp_color = "green" if hp["current"] > hp["max"] * 0.5 else "yellow" if hp["current"] > hp["max"] * 0.25 else "red"
                parts.append(bar(hp["current"], hp["max"], 15, hp_color, label="    HP"))
            if mp:
                parts.append(bar(mp["current"], mp["max"], 15, "dodger_blue1", label="    MP"))

            if c.get("ability"):
                parts.append(Text(f"    Ability: {c['ability']}", style="cyan"))
            if c.get("status"):
                parts.append(Text(f"    Status: {c['status']}", style="green" if c["status"] == "Active" else "yellow"))
            if c.get("disposition"):
                parts.append(Text(f"    Disposition: {c['disposition']}", style="bright_magenta"))
            if c.get("notes"):
                parts.append(Text(f"    Notes: {c['notes']}", style="dim italic"))
            parts.append(Text())

        if not comp.get("companions"):
            parts.append(Text("  No companions yet.", style="dim italic"))

        return Group(*parts)


class QuestsPanel(Static):
    """Displays quest log."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        quests = self.data.get("quests", {})
        if not quests:
            return Group(Text("No quest data found.", style="dim"))

        parts = []

        # Active quests
        active = quests.get("active", [])
        parts.append(Text("  📋 ACTIVE QUESTS", style="bold bright_yellow underline"))
        parts.append(Text())

        if active:
            for q in active:
                parts.append(Text(f"  ▸ {q.get('title', '?')}", style="bold"))
                if q.get("given_by"):
                    parts.append(Text(f"    Given by: {q['given_by']}", style="dim"))
                if q.get("realm"):
                    parts.append(Text(f"    Realm: {q['realm']}", style="cyan"))
                if q.get("objective"):
                    parts.append(Text(f"    Objective: {q['objective']}", style="white"))
                if q.get("progress"):
                    parts.append(Text(f"    Progress: {q['progress']}", style="yellow"))
                if q.get("reward"):
                    parts.append(Text(f"    Reward: {q['reward']}", style="green"))
                parts.append(Text())
        else:
            parts.append(Text("    No active quests.", style="dim italic"))
            parts.append(Text())

        # Completed quests
        completed = quests.get("completed", [])
        parts.append(Text("  ✅ COMPLETED QUESTS", style="bold green underline"))
        parts.append(Text())

        if completed:
            for q in completed:
                parts.append(Text(f"  ✓ {q.get('title', '?')}", style="bold green"))
                if q.get("completed_turn"):
                    parts.append(Text(f"    Completed: {q['completed_turn']}", style="dim"))
                if q.get("outcome"):
                    parts.append(Text(f"    Outcome: {q['outcome']}", style="dim italic"))
                if q.get("reward_received"):
                    parts.append(Text(f"    Reward: {q['reward_received']}", style="dim"))
                parts.append(Text())
        else:
            parts.append(Text("    No completed quests.", style="dim italic"))

        return Group(*parts)


class NPCPanel(Static):
    """Displays NPC tracker."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        npcs = self.data.get("npcs", [])
        if not npcs:
            return Group(Text("No NPC data found.", style="dim"))

        parts = []
        disp_colors = {
            "hostile": "red",
            "wary": "dark_orange",
            "neutral": "yellow",
            "friendly": "green",
            "devoted": "bright_magenta",
            "unknown": "grey50",
        }

        for npc in npcs:
            name_line = Text()
            name_line.append(f"  👤 {npc.get('name', '?')}", style="bold")
            parts.append(name_line)

            disp = npc.get("disposition", "Unknown").lower()
            dc = disp_colors.get(disp, "white")
            parts.append(Text(f"    Disposition: ", style="dim") + Text(npc.get("disposition", "?"), style=f"bold {dc}"))
            parts.append(Text(f"    Location: {npc.get('location', '?')}", style="dim"))
            parts.append(Text(f"    Status: {npc.get('status', '?')}", style="cyan"))
            if npc.get("quests_given"):
                parts.append(Text(f"    Quests: {npc['quests_given']}", style="yellow"))
            if npc.get("notes"):
                parts.append(Text(f"    Notes: {npc['notes']}", style="dim italic"))
            parts.append(Text())

        return Group(*parts)


class LogPanel(Static):
    """Displays session log."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        entries = self.data.get("log", [])
        if not entries:
            return Group(Text("No log entries found.", style="dim"))

        parts = []
        for entry in entries:
            header = Text()
            header.append(f"  [Turn {entry.get('turn', '?')}] ", style="bold yellow")
            header.append(f"— {entry.get('title', '?')}", style="bold")
            parts.append(header)
            parts.append(Text(f"  {entry.get('text', '')}", style="italic dim"))
            parts.append(Text())

        return Group(*parts)


class SettingsPanel(Static):
    """Displays settings."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        settings = self.data.get("settings", {})
        if not settings:
            return Group(Text("No settings found.", style="dim"))

        parts = []

        # Game info
        game = settings.get("game", {})
        parts.append(Text(f"  {game.get('title', 'Unknown Game')}", style="bold bright_cyan"))
        parts.append(Text(f"  Version: {game.get('version', '?')}", style="dim"))
        parts.append(Text())

        # Difficulty
        diff = settings.get("difficulty", {})
        mode = diff.get("mode", "normal")
        mode_colors = {"easy": "green", "normal": "yellow", "hard": "dark_orange", "nightmare": "red"}
        parts.append(Text("  ⚙ Difficulty", style="bold underline"))
        parts.append(Text(f"    Mode: ", style="dim") + Text(mode.upper(), style=f"bold {mode_colors.get(mode, 'white')}"))
        parts.append(Text(f"    Void Rate: {diff.get('void_corruption_rate', {}).get(mode, '?')}x", style="dim"))
        parts.append(Text(f"    DC Modifier: {diff.get('dc_modifier', {}).get(mode, '?'):+d}", style="dim"))
        parts.append(Text(f"    HP Bonus: {diff.get('player_hp_bonus', {}).get(mode, '?'):+d}", style="dim"))
        parts.append(Text())

        # Narrative
        narr = settings.get("narrative", {})
        parts.append(Text("  📖 Narrative", style="bold underline"))
        parts.append(Text(f"    Verbosity: {narr.get('verbosity', '?')}", style="dim"))
        parts.append(Text(f"    Tone: {narr.get('tone', '?')}", style="dim"))
        parts.append(Text(f"    Show Stats: {narr.get('show_stat_blocks', '?')}", style="dim"))
        parts.append(Text(f"    Show Void Counter: {narr.get('show_void_counter', '?')}", style="dim"))
        parts.append(Text(f"    Show Rolls: {narr.get('show_roll_details', '?')}", style="dim"))
        parts.append(Text())

        # Gameplay
        gp = settings.get("gameplay", {})
        parts.append(Text("  🎮 Gameplay", style="bold underline"))
        parts.append(Text(f"    Permadeath: {gp.get('permadeath', False)}", style="dim"))
        parts.append(Text(f"    Auto-save: every {gp.get('auto_save_turns', '?')} turns", style="dim"))
        parts.append(Text(f"    Max Companions: {gp.get('max_companions', '?')}", style="dim"))
        parts.append(Text(f"    Max Inventory: {gp.get('max_inventory_slots', '?')}", style="dim"))
        parts.append(Text())

        # Combat
        cb = settings.get("combat", {})
        parts.append(Text("  ⚔ Combat", style="bold underline"))
        parts.append(Text(f"    Dice Tool: {cb.get('use_dice_tool', '?')}", style="dim"))
        parts.append(Text(f"    Crit Multiplier: {cb.get('critical_hit_multiplier', '?')}x", style="dim"))
        parts.append(Text(f"    Fumble Self-Damage: {cb.get('fumble_causes_self_damage', '?')}", style="dim"))

        return Group(*parts)


class DicePanel(Static):
    """Interactive dice roller."""

    def __init__(self, game_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.game_dir = game_dir
        self.last_result = ""

    def compose(self) -> ComposeResult:
        yield Static(Text("  🎲 Dice Roller", style="bold bright_yellow underline"), id="dice-title")
        yield Static(Text("  Type a dice expression and press Enter", style="dim"), id="dice-help")
        yield Static(Text("  Examples: d20, 2d6+3, d20 --advantage, d20 --dc 15", style="dim"), id="dice-examples")
        yield Input(placeholder="d20+5", id="dice-input")
        yield Static("", id="dice-result")


# ─── Main App ─────────────────────────────────────────────────────────────────

def make_css(with_terminal: bool) -> str:
    """Generate the app CSS based on whether the terminal panel is enabled."""
    base = """
Screen {
    background: $surface;
}

#top-bar {
    height: 3;
    background: #1a1a2e;
    padding: 0 1;
    color: white;
}

TabbedContent {
    height: 1fr;
}

TabPane {
    padding: 1 2;
}

#dice-input {
    margin: 1 2;
    width: 40;
}

#dice-result {
    margin: 1 2;
    min-height: 5;
}

VerticalScroll {
    height: 1fr;
}
"""
    if with_terminal:
        base += """
#split-view {
    height: 1fr;
}

#terminal-panel {
    width: 50%;
    height: 1fr;
    border-right: solid grey;
}

#main-content {
    width: 50%;
    height: 1fr;
}
"""
    else:
        base += """
#main-content {
    height: 1fr;
}
"""
    return base


class AethermoorTUI(App):
    """The Sundering of Aethermoor — Game Session Viewer"""

    TITLE = "Agentic Game Session Viewer"
    SUB_TITLE = "The Sundering of Aethermoor"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "focus_dice", "Dice Roller"),
        Binding("t", "focus_terminal", "Terminal"),
        Binding("1", "tab_character", "Character", show=False),
        Binding("2", "tab_world", "World", show=False),
        Binding("3", "tab_location", "Location", show=False),
        Binding("4", "tab_inventory", "Inventory", show=False),
        Binding("5", "tab_quests", "Quests", show=False),
        Binding("6", "tab_npcs", "NPCs", show=False),
        Binding("7", "tab_companions", "Companions", show=False),
        Binding("8", "tab_log", "Log", show=False),
    ]

    def __init__(self, game_dir: str, with_terminal: bool = True, auto_refresh: float = 5.0):
        super().__init__()
        self.game_dir = game_dir
        self.with_terminal = with_terminal
        self.auto_refresh_interval = auto_refresh
        self.parser = SessionParser(game_dir)
        self.session_data = {}
        self.CSS = make_css(with_terminal)

    def compose(self) -> ComposeResult:
        self.session_data = self.parser.parse_all()
        player = self.session_data.get("player", {})
        world = self.session_data.get("world", {})

        # Top status bar
        top_bar = self._make_top_bar(player, world)
        yield Static(top_bar, id="top-bar")

        yield Header()

        tabs_content = TabbedContent(
            "Character", "World", "Location", "Inventory",
            "Quests", "NPCs", "Companions", "Log", "Dice", "Settings",
        )

        if self.with_terminal:
            with Horizontal(id="split-view"):
                with Vertical(id="terminal-panel"):
                    yield PtyTerminal(command="bash", id="game-terminal")
                with Vertical(id="main-content"):
                    with tabs_content:
                        yield from self._compose_tab_panes()
        else:
            with Vertical(id="main-content"):
                with tabs_content:
                    yield from self._compose_tab_panes()

        yield Footer()

    def _compose_tab_panes(self) -> ComposeResult:
        with TabPane("Character", id="tab-character"):
            with VerticalScroll():
                yield CharacterPanel(self.session_data)

        with TabPane("World", id="tab-world"):
            with VerticalScroll():
                yield WorldPanel(self.session_data)

        with TabPane("Location", id="tab-location"):
            with VerticalScroll():
                yield LocationPanel(self.session_data)

        with TabPane("Inventory", id="tab-inventory"):
            with VerticalScroll():
                yield InventoryPanel(self.session_data)

        with TabPane("Quests", id="tab-quests"):
            with VerticalScroll():
                yield QuestsPanel(self.session_data)

        with TabPane("NPCs", id="tab-npcs"):
            with VerticalScroll():
                yield NPCPanel(self.session_data)

        with TabPane("Companions", id="tab-companions"):
            with VerticalScroll():
                yield CompanionsPanel(self.session_data)

        with TabPane("Log", id="tab-log"):
            with VerticalScroll():
                yield LogPanel(self.session_data)

        with TabPane("Dice", id="tab-dice"):
            with VerticalScroll():
                yield DicePanel(self.game_dir)

        with TabPane("Settings", id="tab-settings"):
            with VerticalScroll():
                yield SettingsPanel(self.session_data)

    def _make_top_bar(self, player: dict, world: dict) -> Text:
        t = Text()
        name = player.get("name", "No Active Session")
        cls = player.get("class", "")
        corruption = world.get("corruption", 0)

        t.append("  ⚔ ", style="bold")
        t.append(name, style="bold white")
        if cls:
            t.append(f" ({cls})", style="dim cyan")

        stats = player.get("stats", {})
        hp = stats.get("HP", {})
        mp = stats.get("MP", {})
        t.append("   HP:", style="bold")
        t.append(f"{hp.get('current', '?')}/{hp.get('base', '?')}", style="green")
        t.append("  MP:", style="bold")
        t.append(f"{mp.get('current', '?')}/{mp.get('base', '?')}", style="dodger_blue1")

        rp = player.get("rift_points", {})
        t.append("  RP:", style="bold")
        t.append(f"{rp.get('current', '?')}/{rp.get('max', '?')}", style="medium_purple")

        vc_color = "green" if corruption <= 25 else "yellow" if corruption <= 50 else "dark_orange" if corruption <= 75 else "red"
        t.append("   VOID:", style="bold")
        t.append(f"{corruption}%", style=f"bold {vc_color}")

        turn = player.get("turns", 0)
        t.append(f"   Turn:{turn}", style="dim")

        return t

    def on_mount(self) -> None:
        if self.auto_refresh_interval > 0:
            self.set_interval(self.auto_refresh_interval, self._periodic_refresh)
        if self.with_terminal:
            try:
                terminal = self.query_one("#game-terminal", PtyTerminal)
                terminal.start()
            except NoMatches:
                pass

    def action_focus_terminal(self) -> None:
        if not self.with_terminal:
            self.notify("Terminal is disabled. Restart with --terminal true to enable.")
            return
        try:
            self.query_one("#game-terminal", PtyTerminal).focus()
        except NoMatches:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "dice-input":
            expr = event.value.strip()
            if not expr:
                return
            dice_path = Path(self.game_dir) / "tools" / "dice.py"
            try:
                args = ["python3", str(dice_path)] + expr.split()
                result = subprocess.run(args, capture_output=True, text=True, timeout=5)
                output = result.stdout.strip() or result.stderr.strip() or "No output"
            except Exception as e:
                output = f"Error: {e}"

            try:
                result_widget = self.query_one("#dice-result", Static)
                result_text = Text()
                result_text.append(f"\n  {output}\n", style="bold bright_yellow")
                result_widget.update(result_text)
            except NoMatches:
                pass
            event.input.value = ""

    def action_refresh(self) -> None:
        self.session_data = self.parser.parse_all()
        # Push new data into every panel widget and re-render.
        # layout=True is required so VerticalScroll parents recalculate
        # when content size changes (e.g., new log entries added).
        for widget in self.query(
            "CharacterPanel, WorldPanel, LocationPanel, "
            "InventoryPanel, CompanionsPanel, QuestsPanel, "
            "NPCPanel, LogPanel, SettingsPanel"
        ):
            widget.data = self.session_data
            widget.refresh(layout=True)
        # Update the top status bar
        player = self.session_data.get("player", {})
        world = self.session_data.get("world", {})
        try:
            self.query_one("#top-bar", Static).update(
                self._make_top_bar(player, world)
            )
        except NoMatches:
            pass
        self.notify("Session data refreshed!")

    def _periodic_refresh(self) -> None:
        """Silent auto-refresh — same as action_refresh but without the notification toast."""
        self.session_data = self.parser.parse_all()
        for widget in self.query(
            "CharacterPanel, WorldPanel, LocationPanel, "
            "InventoryPanel, CompanionsPanel, QuestsPanel, "
            "NPCPanel, LogPanel, SettingsPanel"
        ):
            widget.data = self.session_data
            widget.refresh(layout=True)
        player = self.session_data.get("player", {})
        world = self.session_data.get("world", {})
        try:
            self.query_one("#top-bar", Static).update(
                self._make_top_bar(player, world)
            )
        except NoMatches:
            pass

    def action_focus_dice(self) -> None:
        try:
            self.query_one("#dice-input", Input).focus()
        except NoMatches:
            pass

    def _switch_tab(self, tab_id: str) -> None:
        try:
            tc = self.query_one(TabbedContent)
            tc.active = tab_id
        except NoMatches:
            pass

    def action_tab_character(self) -> None:
        self._switch_tab("tab-character")
    def action_tab_world(self) -> None:
        self._switch_tab("tab-world")
    def action_tab_location(self) -> None:
        self._switch_tab("tab-location")
    def action_tab_inventory(self) -> None:
        self._switch_tab("tab-inventory")
    def action_tab_quests(self) -> None:
        self._switch_tab("tab-quests")
    def action_tab_npcs(self) -> None:
        self._switch_tab("tab-npcs")
    def action_tab_companions(self) -> None:
        self._switch_tab("tab-companions")
    def action_tab_log(self) -> None:
        self._switch_tab("tab-log")

    def on_unmount(self) -> None:
        if self.with_terminal:
            try:
                terminal = self.query_one("#game-terminal", PtyTerminal)
                terminal.cleanup()
            except NoMatches:
                pass


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="The Sundering of Aethermoor — TUI Session Viewer",
    )
    parser.add_argument(
        "game_dir",
        nargs="?",
        default=None,
        help="Path to the game root directory (default: auto-detect from cwd)",
    )
    parser.add_argument(
        "--terminal",
        choices=["true", "false"],
        default="true",
        help="Enable or disable the integrated PTY terminal panel (default: true)",
    )
    parser.add_argument(
        "--refresh",
        type=float,
        default=5.0,
        help="Auto-refresh interval in seconds (default: 5). Set to 0 to disable auto-refresh.",
    )
    args = parser.parse_args()

    if args.game_dir:
        game_dir = args.game_dir
    else:
        # Auto-detect game root: if run from inside tui/, look one level up
        cwd = Path(os.getcwd())
        if cwd.name == "tui" and (cwd.parent / "session").exists():
            game_dir = str(cwd.parent)
        elif (cwd / "session").exists():
            game_dir = str(cwd)
        else:
            # Default: assume tui_viewer.py lives in <game_root>/tui/
            game_dir = str(Path(__file__).resolve().parent.parent)

    # Verify session directory exists
    session_path = Path(game_dir) / "session"
    if not session_path.exists():
        print(f"Warning: No session/ directory found in {game_dir}")
        print("The TUI will show empty panels. Start a game first to populate session data.")

    with_terminal = args.terminal == "true"
    app = AethermoorTUI(game_dir, with_terminal=with_terminal, auto_refresh=args.refresh)
    app.run()


if __name__ == "__main__":
    main()
