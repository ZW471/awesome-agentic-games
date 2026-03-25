#!/usr/bin/env python3
"""
Signal Lost / 信号遗失 — TUI Viewer
======================================
A Textual-based terminal UI for the cyberpunk knowledge-roguelike "Signal Lost".
Neon hacker terminal aesthetic with bilingual (EN/ZH) support.

Usage:
    .venv/bin/python tui/tui_viewer.py [game_directory] [--terminal true|false] [--refresh N]

Dependencies:
    uv pip install textual pyte rich
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
import sys
import termios
import unicodedata
from pathlib import Path
from typing import Optional

import pyte
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key, Paste, MouseDown, MouseMove, MouseUp
from textual.widgets import (
    Header,
    Footer,
    Static,
    TabbedContent,
    TabPane,
    Input,
)
from textual.css.query import NoMatches
from textual.strip import Strip
from rich.segment import Segment
from rich.style import Style as RichStyle
from rich.text import Text
from rich.table import Table
from rich.console import Group
from rich.panel import Panel
from rich.columns import Columns


# =============================================================================
# BILINGUAL LABELS
# =============================================================================

LABELS = {
    "en": {
        "tab_identity": "IDENTITY",
        "tab_knowledge": "KNOWLEDGE",
        "tab_traces": "TRACES",
        "tab_district": "DISTRICT",
        "tab_inventory": "INVENTORY",
        "tab_network": "NETWORK",
        "tab_world": "WORLD",
        "tab_log": "LOG",
        "tab_tools": "TOOLS",
        "identity": "IDENTITY",
        "name": "Name",
        "alias": "Alias",
        "background": "Background",
        "integrity": "Integrity",
        "credits": "Credits",
        "neural_implant": "Neural Implant",
        "disguise": "Current Disguise",
        "turn": "Turn",
        "time": "Time",
        "status_effects": "Status Effects",
        "none": "None",
        "facts": "Facts",
        "rumors": "Rumors",
        "evidence": "Evidence",
        "theories": "Theories",
        "connections": "Connections",
        "traces": "Traces of Truth",
        "total": "Total",
        "layer": "Layer",
        "discovered": "Discovered",
        "undiscovered": "Undiscovered",
        "district": "District",
        "area": "Area",
        "signal_strength": "Signal Strength",
        "danger_level": "Danger Level",
        "nexus_patrol": "NEXUS Patrol",
        "exits": "Exits",
        "poi": "Points of Interest",
        "npcs_present": "NPCs Present",
        "description": "Description",
        "inventory": "Inventory",
        "slots": "Slots",
        "slot": "Slot",
        "item": "Item",
        "type": "Type",
        "npc_tracker": "NPC Tracker",
        "faction": "Faction",
        "trust": "Trust",
        "location_seen": "Last Seen",
        "knowledge_revealed": "Knowledge Revealed",
        "quest_status": "Quest Status",
        "notes": "Notes",
        "world_state": "World State",
        "nexus_alert": "NEXUS Alert",
        "fragment_decay": "Fragment Decay",
        "district_access": "District Access",
        "global_events": "Global Events",
        "session_log": "Session Log",
        "tools": "Tools",
        "tools_input_placeholder": "Enter tool command...",
        "tool_dice": "DICE",
        "tool_cipher": "CIPHER",
        "tool_signal": "SIGNAL",
        "tool_map": "MAP",
        "empty": "(empty)",
        "no_data": "No data available",
        "safe": "SAFE",
        "low": "LOW",
        "moderate": "MODERATE",
        "high": "HIGH",
        "extreme": "EXTREME",
        "period": "Period",
    },
    "zh": {
        "tab_identity": "身份",
        "tab_knowledge": "知识",
        "tab_traces": "痕迹",
        "tab_district": "区域",
        "tab_inventory": "物品",
        "tab_network": "人脉",
        "tab_world": "世界",
        "tab_log": "日志",
        "tab_tools": "工具",
        "identity": "身份",
        "name": "姓名",
        "alias": "化名",
        "background": "背景",
        "integrity": "完整性",
        "credits": "信用点",
        "neural_implant": "神经植入体",
        "disguise": "当前伪装",
        "turn": "回合",
        "time": "时间",
        "status_effects": "状态效果",
        "none": "无",
        "facts": "事实",
        "rumors": "传闻",
        "evidence": "证据",
        "theories": "推论",
        "connections": "关联",
        "traces": "真相痕迹",
        "total": "总计",
        "layer": "层",
        "discovered": "已发现",
        "undiscovered": "未发现",
        "district": "区域",
        "area": "地点",
        "signal_strength": "信号强度",
        "danger_level": "危险等级",
        "nexus_patrol": "连结巡逻",
        "exits": "出口",
        "poi": "兴趣点",
        "npcs_present": "在场角色",
        "description": "描述",
        "inventory": "物品栏",
        "slots": "槽位",
        "slot": "槽",
        "item": "物品",
        "type": "类型",
        "npc_tracker": "角色追踪",
        "faction": "阵营",
        "trust": "信任",
        "location_seen": "上次出现",
        "knowledge_revealed": "已揭示知识",
        "quest_status": "任务状态",
        "notes": "备注",
        "world_state": "世界状态",
        "nexus_alert": "连结警报",
        "fragment_decay": "碎片衰变",
        "district_access": "区域通行",
        "global_events": "全局事件",
        "session_log": "事件日志",
        "tools": "工具",
        "tools_input_placeholder": "输入工具命令...",
        "tool_dice": "骰子",
        "tool_cipher": "密码",
        "tool_signal": "信号",
        "tool_map": "地图",
        "empty": "(空)",
        "no_data": "无数据",
        "safe": "安全",
        "low": "低",
        "moderate": "中",
        "high": "高",
        "extreme": "极端",
        "period": "时段",
    },
}

# =============================================================================
# THEME COLORS
# =============================================================================

CLR_PRIMARY = "#00ffff"
CLR_ACCENT = "#ff00ff"
CLR_GREEN = "#00ff41"
CLR_WARNING = "#ffbf00"
CLR_DANGER = "#ff3333"
CLR_BG = "#0a0a0f"
CLR_BAR_BG = "#1a1a2e"
CLR_DIM = "#555577"
CLR_TEXT = "#ccccdd"
CLR_MUTED = "#8888aa"

# Layer colors for knowledge entries
LAYER_COLORS = {
    "L1": "white",
    "L2": CLR_PRIMARY,
    "L3": CLR_ACCENT,
    "L4": CLR_WARNING,
    "L5": "bright_green",
}

# Faction colors
FACTION_COLORS = {
    "nexus": CLR_DANGER,
    "listener": CLR_PRIMARY,
    "listeners": CLR_PRIMARY,
    "purist": CLR_WARNING,
    "purists": CLR_WARNING,
    "independent": CLR_MUTED,
    "corporate": CLR_WARNING,
    "underground": CLR_GREEN,
    "unknown": CLR_MUTED,
    "unaffiliated": CLR_MUTED,
}

# Trust colors
TRUST_COLORS = {
    "hostile": CLR_DANGER,
    "suspicious": "#ff6600",
    "neutral": CLR_WARNING,
    "cautious_ally": "#88cc44",
    "trusted": CLR_GREEN,
    "devoted": "bright_magenta",
}


def _extract_english_key(value: str, lookup: dict) -> str:
    """Extract a matching key from a bilingual value like '中立（Neutral）' or '独立 / Listeners'.

    Tries the raw lowercase value first, then looks for parenthesized English,
    then splits on '/' and checks each part against the lookup dict.
    """
    low = value.lower().strip()
    if low in lookup:
        return low
    # Check for English in parentheses: 中立（Neutral） or 中立(Neutral)
    paren = re.search(r"[（(]([A-Za-z_\s]+)[）)]", value)
    if paren:
        candidate = paren.group(1).strip().lower().replace(" ", "_")
        if candidate in lookup:
            return candidate
    # Split on / and check each part
    for part in value.split("/"):
        candidate = part.strip().lower().replace(" ", "_")
        if candidate in lookup:
            return candidate
    return low


# Log tag colors
TAG_COLORS = {
    "movement": CLR_DIM,
    "dialogue": CLR_PRIMARY,
    "discovery": CLR_WARNING,
    "danger": CLR_DANGER,
    "signal": CLR_ACCENT,
    "system": CLR_MUTED,
    "trade": CLR_GREEN,
}

# Item type icons
ITEM_ICONS = {
    "data_chip": "\U0001f4be",
    "keycard": "\U0001f511",
    "disguise": "\U0001f3ad",
    "signal_artifact": "\u2726",
    "evidence": "\U0001f4ce",
    "tool": "\U0001f527",
    "consumable": "\U0001f48a",
}

# Danger level colors
DANGER_COLORS = {
    "safe": CLR_GREEN,
    "low": "#88cc44",
    "moderate": CLR_WARNING,
    "high": "#ff6600",
    "extreme": CLR_DANGER,
}


# =============================================================================
# ASCII ART HEADER
# =============================================================================

SIGNAL_LOST_ASCII = r"""
[cyan]  ███████╗██╗ ██████╗ ███╗   ██╗ █████╗ ██╗          ██╗      ██████╗ ███████╗████████╗[/]
[cyan]  ██╔════╝██║██╔════╝ ████╗  ██║██╔══██╗██║          ██║     ██╔═══██╗██╔════╝╚══██╔══╝[/]
[cyan]  ███████╗██║██║  ███╗██╔██╗ ██║███████║██║          ██║     ██║   ██║███████╗   ██║   [/]
[cyan]  ╚════██║██║██║   ██║██║╚██╗██║██╔══██║██║          ██║     ██║   ██║╚════██║   ██║   [/]
[cyan]  ███████║██║╚██████╔╝██║ ╚████║██║  ██║███████╗     ███████╗╚██████╔╝███████║   ██║   [/]
[cyan]  ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝     ╚══════╝ ╚═════╝ ╚══════╝   ╚═╝   [/]
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def bar(current: float, maximum: float, width: int = 20,
        fill_char: str = "\u2588", empty_char: str = "\u2591",
        fill_style: str = CLR_PRIMARY, empty_style: str = CLR_DIM,
        gradient: bool = False) -> Text:
    """Build a colored progress bar as a Rich Text object."""
    if maximum <= 0:
        ratio = 0.0
    else:
        ratio = max(0.0, min(1.0, current / maximum))
    filled = int(ratio * width)
    empty = width - filled

    txt = Text()
    if gradient:
        for i in range(filled):
            pos = i / max(width - 1, 1)
            if pos < 0.4:
                color = CLR_GREEN
            elif pos < 0.7:
                color = CLR_WARNING
            else:
                color = CLR_DANGER
            txt.append(fill_char, style=color)
    else:
        txt.append(fill_char * filled, style=fill_style)
    txt.append(empty_char * empty, style=empty_style)
    return txt


def waveform_bar(current: float, maximum: float, width: int = 20) -> Text:
    """Build a signal waveform bar."""
    if maximum <= 0:
        ratio = 0.0
    else:
        ratio = max(0.0, min(1.0, current / maximum))
    filled = int(ratio * width)
    empty = width - filled
    txt = Text()
    txt.append("\u223f" * filled, style=CLR_PRIMARY)
    txt.append("\u2591" * empty, style=CLR_DIM)
    return txt


def _cjk_ljust(s: str, width: int) -> str:
    """Left-justify string accounting for CJK double-width characters."""
    display_width = 0
    for ch in s:
        eaw = unicodedata.east_asian_width(ch)
        display_width += 2 if eaw in ("W", "F") else 1
    padding = max(0, width - display_width)
    return s + " " * padding


def _cjk_display_width(s: str) -> int:
    """Return the display width of a string accounting for CJK characters."""
    w = 0
    for ch in s:
        eaw = unicodedata.east_asian_width(ch)
        w += 2 if eaw in ("W", "F") else 1
    return w


# =============================================================================
# PTY TERMINAL WIDGET
# =============================================================================

PYTE_TO_RICH_COLORS = {
    "black": "black", "red": "red", "green": "green", "brown": "yellow",
    "blue": "blue", "magenta": "magenta", "cyan": "cyan", "white": "white",
    "brightblack": "bright_black", "brightred": "bright_red",
    "brightgreen": "bright_green", "brightyellow": "bright_yellow",
    "brightblue": "bright_blue", "brightmagenta": "bright_magenta",
    "brightcyan": "bright_cyan", "brightwhite": "bright_white",
}


class EnhancedScreen(pyte.HistoryScreen):
    """pyte HistoryScreen with alternate screen buffer support (modes 47/1047/1049).

    Programs like vim, less, and htop switch to an alternate screen buffer so
    they don't clobber the main scrollback. This subclass intercepts those mode
    switches and saves/restores the primary buffer accordingly.
    """

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
    """A terminal emulator widget that embeds a real PTY shell using pyte.

    This widget spawns a child shell process connected to a pseudo-terminal.
    Terminal output is parsed by pyte (a Python terminal emulator library) and
    rendered as Rich Segments. Keyboard input is forwarded to the PTY.

    Constructor args:
        command: Shell command to run (default: user's SHELL or "bash").

    Lifecycle:
        1. Widget is mounted -> pyte screen is initialized.
        2. start() is called (typically in App.on_mount) -> PTY is opened,
           shell process is spawned, poll loop begins.
        3. cleanup() is called (in App.on_unmount) -> process is terminated,
           file descriptors are closed.

    Keyboard handling:
        When focused, ALL key events are intercepted and forwarded to the PTY
        as the appropriate byte sequences. This includes:
        - Printable characters (sent as UTF-8)
        - Enter (\\r), Tab (\\t), Escape (\\x1b), Backspace (\\x7f)
        - Arrow keys (ANSI escape sequences, respecting DECCKM app cursor mode)
        - Function keys F1-F12, Home, End, Insert, Delete, PageUp, PageDown
        - Ctrl+<letter> combinations (converted to control codes)
        - Shift+PageUp/Down for scrollback navigation (NOT sent to PTY)

    Scrollback:
        The terminal maintains a history buffer. Use Shift+PageUp/Down or the
        mouse wheel to scroll through past output. Scrollback is disabled when
        the shell is in alternate screen mode (e.g. running vim).

    Resize:
        When the widget is resized, the pyte screen is resized and a TIOCSWINSZ
        ioctl is sent to the PTY so the child process knows the new dimensions.
    """

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

    def __init__(self, command: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.command = command or os.environ.get("SHELL", "bash")
        self.master_fd: Optional[int] = None
        self._process: Optional[subprocess.Popen] = None
        self._pty_screen: Optional[EnhancedScreen] = None
        self._pty_stream: Optional[pyte.Stream] = None
        self._reader_running = False
        # Selection state for copy support
        self._sel_start: Optional[tuple[int, int]] = None  # (x, y)
        self._sel_end: Optional[tuple[int, int]] = None    # (x, y)
        self._selecting = False

    def on_mount(self) -> None:
        """Initialize the pyte virtual screen to match the widget dimensions."""
        cols = max(self.size.width - 2, 10)
        rows = max(self.size.height - 2, 5)
        self._pty_screen = EnhancedScreen(cols, rows)
        self._pty_stream = pyte.Stream(self._pty_screen)

    def start(self) -> None:
        """Spawn a shell process in a new PTY and begin the read loop.

        This opens a master/slave PTY pair, starts the shell as a subprocess
        attached to the slave side, then polls the master side for output.
        The master fd is set to non-blocking so reads never stall the event loop.
        """
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

        # Set master fd to non-blocking so _poll_pty never blocks the event loop
        flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # Wire pyte's device-attribute responses back to the PTY
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
        """Resize the pyte screen and notify the PTY child of the new size."""
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
        """Read available data from the PTY master fd and feed it to pyte.

        This runs on a 20ms timer. Each tick reads up to 64KB of output,
        feeds it through the pyte ANSI parser, and refreshes the widget
        if any screen lines were dirtied.
        """
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

    # -- Clipboard: Paste --

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
        bracketed = self._pty_screen and (2004 in self._pty_screen.mode)
        payload = text.encode("utf-8")
        if bracketed:
            self._write_bytes(b"\x1b[200~" + payload + b"\x1b[201~")
        else:
            self._write_bytes(payload)
        event.prevent_default()
        event.stop()

    # -- Clipboard: Mouse selection & Copy --

    def _sel_ordered(self) -> Optional[tuple[tuple[int, int], tuple[int, int]]]:
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
            self._sel_start = (event.x, event.y)
            self._sel_end = (event.x, event.y)
            self._selecting = True
            self.capture_mouse()
            self.refresh()
            event.stop()

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._selecting and self._pty_screen:
            x = max(0, min(event.x, self._pty_screen.columns - 1))
            y = max(0, min(event.y, self._pty_screen.lines - 1))
            self._sel_end = (x, y)
            self.refresh()
            event.stop()

    def on_mouse_up(self, event: MouseUp) -> None:
        if event.button == 1 and self._selecting:
            self._selecting = False
            self.release_mouse()
            if self._sel_start == self._sel_end:
                self._clear_selection()
                return
            text = self._get_selected_text()
            if text:
                self.app.copy_to_clipboard(text)
                self.app.notify("Copied to clipboard", timeout=1.5)
            event.stop()

    def on_key(self, event: Key) -> None:
        """Translate Textual key events to PTY-compatible byte sequences.

        Scrollback keys (Shift+PageUp/Down) are handled locally and NOT sent
        to the PTY. All other keys are translated and written to the master fd.
        """
        if self.master_fd is None or not self.has_focus:
            return

        # Any keypress clears the visual selection
        if self._sel_start is not None:
            self._clear_selection()

        # Scrollback navigation — handled locally, not sent to PTY
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

        # DECCKM: application cursor mode changes arrow key escape sequences
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
        """Render a single terminal line as a Rich Strip.

        Each character cell from the pyte screen buffer is converted to a Rich
        Segment with the appropriate foreground/background color, bold, italic,
        underline, strikethrough, and reverse attributes. The cursor position
        is rendered as reverse video when the widget is focused. Selected cells
        are highlighted with a distinct background color.
        """
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
                fg_color = PYTE_TO_RICH_COLORS.get(
                    fg,
                    f"#{fg}" if len(fg) == 6 and all(c in "0123456789abcdefABCDEF" for c in fg) else fg,
                )
            bg = char_data.bg
            if bg and bg != "default":
                bg_color = PYTE_TO_RICH_COLORS.get(
                    bg,
                    f"#{bg}" if len(bg) == 6 and all(c in "0123456789abcdefABCDEF" for c in bg) else bg,
                )

            is_cursor = (
                self.has_focus
                and y == self._pty_screen.cursor.y
                and x == self._pty_screen.cursor.x
            )

            selected = has_selection and self._is_selected(x, y)

            # XOR: if char is reverse AND cursor is here, they cancel out
            effective_reverse = char_data.reverse ^ is_cursor

            if selected:
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
        """Terminate the shell process and close the PTY file descriptors."""
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


# =============================================================================
# SESSION PARSER
# =============================================================================

def filter_hidden(data):
    """Recursively remove any dict containing 'hidden': True from the data tree."""
    if isinstance(data, dict):
        if data.get("hidden") is True:
            return None
        return {k: v for k, v in ((k, filter_hidden(v)) for k, v in data.items()) if v is not None}
    if isinstance(data, list):
        return [item for item in (filter_hidden(i) for i in data) if item is not None]
    return data


class SessionParser:
    """Parses all session/*.json files and settings/custom.json into dicts."""

    def __init__(self, game_dir):
        self.game_dir = Path(game_dir)
        self.session_dir = self.game_dir / "session"
        self.settings_dir = self.game_dir / "settings"

    def _read_json(self, path: Path) -> dict:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            return {}

    def parse_settings(self) -> dict:
        return self._read_json(self.settings_dir / "custom.json")

    def parse_player(self) -> dict:
        raw = self._read_json(self.session_dir / "player.json")
        if not raw:
            return {}

        integrity = raw.get("integrity", {})
        disguise = raw.get("current_disguise") or "None"

        status_effects = []
        for eff in raw.get("status_effects", []):
            if isinstance(eff, dict):
                name = eff.get("name", "")
                intensity = eff.get("intensity", "")
                status_effects.append(f"{name} — {intensity}" if intensity else name)
            else:
                status_effects.append(str(eff))

        return {
            "name": raw.get("name", ""),
            "alias": raw.get("alias", ""),
            "background": raw.get("background", ""),
            "integrity_current": integrity.get("current", 0) if isinstance(integrity, dict) else 0,
            "integrity_max": integrity.get("max", 3) if isinstance(integrity, dict) else 3,
            "credits": raw.get("credits", 0),
            "neural_implant": raw.get("neural_implant", "Dormant"),
            "disguise": disguise,
            "turn": raw.get("turn", 0),
            "time": raw.get("time", ""),
            "status_effects": status_effects,
        }

    def parse_knowledge(self) -> dict:
        raw = self._read_json(self.session_dir / "knowledge.json")
        if not raw:
            return {"facts": [], "rumors": [], "evidence": [], "theories": [], "connections": []}

        def _format_entry(entry, prefix=""):
            if isinstance(entry, str):
                return entry
            entry_id = entry.get("id", "")
            desc = entry.get("description", entry.get("statement", ""))
            source = entry.get("source", entry.get("found", ""))
            turn = entry.get("turn", "")
            status = entry.get("status", "")
            based_on = entry.get("based_on", [])

            parts = []
            if entry_id:
                parts.append(f"[{entry_id}]")
            parts.append(desc)
            if source:
                parts.append(f"(Source: {source}, Turn: {turn})" if turn else f"(Source: {source})")
            elif based_on:
                parts.append(f"(Based on: {', '.join(based_on)}, Turn: {turn}, Status: {status})")
            elif turn:
                parts.append(f"(Turn: {turn})")

            text = " ".join(parts)
            if prefix:
                text = f"{prefix} {text}"
            return text

        result = {}

        # Facts
        result["facts"] = [_format_entry(e, "\u2713") for e in raw.get("facts", [])]

        # Rumors
        rumors = []
        for e in raw.get("rumors", []):
            if isinstance(e, str):
                rumors.append(e)
            else:
                status = e.get("status", "unconfirmed")
                if status == "confirmed":
                    prefix = "\u2713"
                elif status == "disproven":
                    prefix = "\u2717"
                else:
                    prefix = "?"
                rumors.append(_format_entry(e, prefix))
        result["rumors"] = rumors

        # Evidence
        result["evidence"] = [_format_entry(e) for e in raw.get("evidence", [])]

        # Theories
        result["theories"] = [_format_entry(e) for e in raw.get("theories", [])]

        # Connections
        connections = []
        for e in raw.get("connections", []):
            if isinstance(e, str):
                connections.append(e)
            else:
                ids = e.get("ids", [])
                rel = e.get("relationship", "")
                if len(ids) >= 2:
                    connections.append(f"{ids[0]} \u2194 {ids[1]}: {rel}")
                else:
                    connections.append(rel)
        result["connections"] = connections

        return result

    def parse_traces(self) -> dict:
        raw = self._read_json(self.session_dir / "traces.json")
        if not raw:
            return {"discovered": []}

        # Only return discovered traces — do NOT expose the _gate_system
        # (total count, layer structure, undiscovered trace IDs) to the TUI.
        # This prevents spoiling the progression mystery for the player.
        discovered = []
        for d in raw.get("discovered", []):
            if isinstance(d, dict):
                discovered.append({
                    "id": d.get("id", ""),
                    "description": d.get("description", ""),
                    "turn_discovered": d.get("turn_discovered", None),
                })
            elif isinstance(d, str):
                discovered.append({"id": d, "description": "", "turn_discovered": None})

        return {"discovered": discovered}

    def parse_location(self) -> dict:
        raw = self._read_json(self.session_dir / "location.json")
        if not raw:
            return {}

        env = raw.get("environment", {})

        # Format exits as strings for the panel
        exits = []
        for ex in raw.get("exits", []):
            if isinstance(ex, dict):
                direction = ex.get("direction_zh", ex.get("direction", ""))
                dest = ex.get("destination", "")
                status = ex.get("status", "")
                exits.append(f"**{direction}:** {dest}（{status}）" if status else f"**{direction}:** {dest}")
            else:
                exits.append(str(ex))

        # Format POIs as strings
        pois = []
        for p in raw.get("points_of_interest", []):
            if isinstance(p, dict):
                name = p.get("name", "")
                direction = p.get("direction", "")
                desc = p.get("description", "")
                pois.append(f"**{name}（{direction}）:** {desc}" if direction else f"**{name}:** {desc}")
            else:
                pois.append(str(p))

        # Format NPCs as strings
        npcs = []
        for n in raw.get("npcs_present", []):
            if isinstance(n, dict):
                name = n.get("name_zh", n.get("name", ""))
                ename = n.get("name", "")
                activity = n.get("activity", "")
                display = f"**{name}（{ename}）:** {activity}" if ename and ename != name else f"**{name}:** {activity}"
                npcs.append(display)
            else:
                npcs.append(str(n))

        district = raw.get("district", "")
        district_zh = raw.get("district_zh", "")
        area = raw.get("area", "")
        area_zh = raw.get("area_zh", "")

        return {
            "district": f"{district_zh}（{district}）" if district_zh else district,
            "area": f"{area_zh}（{area}）" if area_zh else area,
            "signal_strength": env.get("signal_strength", 0),
            "danger_level": env.get("danger_level", "Safe"),
            "nexus_patrol": env.get("nexus_patrol", "None"),
            "exits": exits,
            "pois": pois,
            "npcs": npcs,
            "description": raw.get("description", ""),
        }

    def parse_inventory(self) -> dict:
        raw = self._read_json(self.session_dir / "inventory.json")
        if not raw:
            return {"credits": 0, "slots_used": 0, "slots_max": 6, "items": []}

        items = []
        for item in raw.get("items", []):
            if isinstance(item, dict):
                items.append({
                    "slot": item.get("slot", 0),
                    "name": item.get("name", ""),
                    "type": item.get("type", ""),
                    "description": item.get("description", ""),
                    "evidence_id": item.get("evidence_id", "") or "",
                })

        return {
            "credits": raw.get("credits", 0),
            "slots_used": raw.get("slots_used", 0),
            "slots_max": raw.get("slots_max", 6),
            "items": items,
        }

    def parse_npcs(self) -> list[dict]:
        raw = self._read_json(self.session_dir / "npcs.json")
        if not raw:
            return []

        npcs = []
        for npc in raw.get("npcs", []):
            if not isinstance(npc, dict):
                continue
            name = npc.get("name", "")
            name_zh = npc.get("name_zh", "")
            display_name = f"{name_zh} / {name}" if name_zh else name

            npcs.append({
                "name": display_name,
                "faction": npc.get("faction", npc.get("faction_zh", "Unknown")),
                "trust_level": npc.get("trust_level", "neutral"),
                "location_last_seen": npc.get("location_last_seen", ""),
                "quest_status": ", ".join(npc.get("quest_status", [])) if isinstance(npc.get("quest_status"), list) else str(npc.get("quest_status", "")),
                "notes": npc.get("notes", ""),
            })

        return npcs

    def parse_world_state(self) -> dict:
        raw = self._read_json(self.session_dir / "world_state.json")
        if not raw:
            return {}

        nexus = raw.get("nexus_alert", {})
        decay = raw.get("fragment_decay", {})
        time_data = raw.get("time", {})

        # District access
        districts = []
        for d in raw.get("district_access", []):
            if isinstance(d, dict):
                districts.append({
                    "name": d.get("name", ""),
                    "chinese": d.get("name_zh", ""),
                    "status": d.get("status", ""),
                })

        # Global events
        events = []
        for ev in raw.get("global_events", []):
            if isinstance(ev, str):
                events.append(ev)
            elif isinstance(ev, dict):
                events.append(ev.get("description", str(ev)))

        period = time_data.get("time_of_day", "") if isinstance(time_data, dict) else ""
        period_zh = time_data.get("time_of_day_zh", "") if isinstance(time_data, dict) else ""
        period_display = f"{period_zh}（{period}）" if period_zh else period

        return {
            "nexus_alert": nexus.get("current", 0) if isinstance(nexus, dict) else 0,
            "alert_status": nexus.get("status", "") if isinstance(nexus, dict) else "",
            "fragment_decay": decay.get("current", 0) if isinstance(decay, dict) else 0,
            "fragment_status": decay.get("status", "") if isinstance(decay, dict) else "",
            "districts": districts,
            "period": period_display,
            "turn": time_data.get("turn", 0) if isinstance(time_data, dict) else 0,
            "events": events,
        }

    def parse_log(self) -> list[dict]:
        raw = self._read_json(self.session_dir / "log.json")
        if not raw:
            return []

        entries = []
        for entry in raw.get("entries", []):
            if isinstance(entry, dict):
                entries.append({
                    "turn": entry.get("turn", 0),
                    "title": entry.get("title", ""),
                    "tag": entry.get("tag", "system").lower(),
                    "description": entry.get("text", entry.get("description", "")),
                })

        return entries

    def parse_all(self) -> dict:
        result = {
            "player": self.parse_player(),
            "knowledge": self.parse_knowledge(),
            "traces": self.parse_traces(),
            "location": self.parse_location(),
            "inventory": self.parse_inventory(),
            "npcs": self.parse_npcs(),
            "world_state": self.parse_world_state(),
            "log": self.parse_log(),
        }
        return filter_hidden(result)


# =============================================================================
# PANEL WIDGETS
# =============================================================================

class IdentityPanel(Static):
    """Player identity and status display."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Group:
        L = LABELS[self.lang]
        player = self.data.get("player", {})
        parts = []

        # ASCII art header
        header = Text.from_markup(SIGNAL_LOST_ASCII)
        parts.append(header)

        parts.append(Text(""))

        # Name / Alias / Background
        name_line = Text()
        name_line.append(f"  {L['name']}: ", style=CLR_MUTED)
        name_line.append(player.get("name", "???"), style=f"bold {CLR_PRIMARY}")
        parts.append(name_line)

        alias_line = Text()
        alias_line.append(f"  {L['alias']}: ", style=CLR_MUTED)
        alias_line.append(player.get("alias", "???"), style=f"bold {CLR_ACCENT}")
        parts.append(alias_line)

        bg_line = Text()
        bg_line.append(f"  {L['background']}: ", style=CLR_MUTED)
        bg_line.append(player.get("background", "???"), style=CLR_TEXT)
        parts.append(bg_line)

        parts.append(Text(""))

        # Integrity as colored pips
        integrity_current = player.get("integrity_current", 0)
        integrity_max = player.get("integrity_max", 3)
        integrity_line = Text()
        integrity_line.append(f"  {L['integrity']}: ", style=CLR_MUTED)
        for i in range(integrity_max):
            if i < integrity_current:
                integrity_line.append("\u2588\u2588 ", style=f"bold {CLR_GREEN}")
            else:
                integrity_line.append("\u2591\u2591 ", style=CLR_DIM)
        integrity_line.append(f" {integrity_current}/{integrity_max}", style=CLR_TEXT)
        parts.append(integrity_line)

        parts.append(Text(""))

        # Credits
        credits_line = Text()
        credits_line.append(f"  {L['credits']}: ", style=CLR_MUTED)
        credits_line.append(f"\u00a4 {player.get('credits', 0)}", style=f"bold {CLR_WARNING}")
        parts.append(credits_line)

        # Neural Implant
        implant = player.get("neural_implant", "Dormant")
        implant_color = CLR_MUTED
        if "active" in implant.lower():
            implant_color = CLR_GREEN
        elif "overloaded" in implant.lower():
            implant_color = CLR_DANGER
        elif "resonating" in implant.lower():
            implant_color = CLR_ACCENT

        implant_line = Text()
        implant_line.append(f"  {L['neural_implant']}: ", style=CLR_MUTED)
        implant_line.append(implant, style=f"bold {implant_color}")
        parts.append(implant_line)

        # Disguise
        disguise = player.get("disguise", "None")
        disguise_line = Text()
        disguise_line.append(f"  {L['disguise']}: ", style=CLR_MUTED)
        if disguise and disguise.lower() != "none":
            disguise_line.append(disguise, style=f"bold {CLR_WARNING}")
        else:
            disguise_line.append(L["none"], style=CLR_DIM)
        parts.append(disguise_line)

        parts.append(Text(""))

        # Turn and Time
        turn_line = Text()
        turn_line.append(f"  {L['turn']}: ", style=CLR_MUTED)
        turn_line.append(str(player.get("turn", 0)), style=CLR_TEXT)
        turn_line.append(f"    {L['time']}: ", style=CLR_MUTED)
        time_str = player.get("time", "")
        time_icon = "\u2600"
        if "night" in time_str.lower() or "\u591c" in time_str:
            time_icon = "\U0001f319"
        elif "afternoon" in time_str.lower() or "\u5348" in time_str:
            time_icon = "\u2600\ufe0f"
        elif "morning" in time_str.lower() or "\u6668" in time_str:
            time_icon = "\U0001f305"
        turn_line.append(f"{time_icon} {time_str}", style=CLR_PRIMARY)
        parts.append(turn_line)

        parts.append(Text(""))

        # Status Effects
        effects = player.get("status_effects", [])
        if effects:
            effects_header = Text()
            effects_header.append(f"  {L['status_effects']}:", style=f"bold {CLR_ACCENT}")
            parts.append(effects_header)
            for eff in effects:
                eff_line = Text()
                eff_line.append(f"    \u25b8 ", style=CLR_ACCENT)
                eff_line.append(eff, style=CLR_TEXT)
                parts.append(eff_line)

        return Group(*parts)


class KnowledgePanel(Static):
    """Knowledge database display."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def _get_layer_color(self, entry: str) -> str:
        for layer, color in LAYER_COLORS.items():
            if f"[{layer}]" in entry:
                return color
        return CLR_TEXT

    def render(self) -> Group:
        L = LABELS[self.lang]
        knowledge = self.data.get("knowledge", {})
        parts = []

        # Section header helper
        def section_header(title, icon, color):
            h = Text()
            h.append(f"\n  {icon} {title}", style=f"bold {color}")
            h.append(f"  {'=' * 40}", style=CLR_DIM)
            parts.append(h)

        # Facts
        facts = knowledge.get("facts", [])
        section_header(L["facts"], "\u2713", CLR_GREEN)
        if facts:
            for entry in facts:
                line = Text()
                color = self._get_layer_color(entry)
                line.append("    \u2713 ", style=f"bold {CLR_GREEN}")
                line.append(entry, style=color)
                parts.append(line)
        else:
            parts.append(Text(f"    {L['no_data']}", style=CLR_DIM))

        # Rumors
        rumors = knowledge.get("rumors", [])
        section_header(L["rumors"], "?", CLR_WARNING)
        if rumors:
            for entry in rumors:
                line = Text()
                if entry.startswith("\u2713"):
                    line.append("    \u2713 ", style=f"bold {CLR_GREEN}")
                    line.append(entry.lstrip("\u2713").strip(), style=self._get_layer_color(entry))
                elif entry.startswith("\u2717"):
                    line.append("    \u2717 ", style=f"bold {CLR_DANGER}")
                    line.append(entry.lstrip("\u2717").strip(), style=f"strikethrough {CLR_DIM}")
                else:
                    prefix = "? " if entry.startswith("?") else ""
                    text_part = entry.lstrip("? ").strip() if prefix else entry
                    line.append("    ? ", style=f"bold {CLR_WARNING}")
                    line.append(text_part, style=self._get_layer_color(entry))
                parts.append(line)
        else:
            parts.append(Text(f"    {L['no_data']}", style=CLR_DIM))

        # Evidence
        evidence = knowledge.get("evidence", [])
        section_header(L["evidence"], "\U0001f4ce", CLR_WARNING)
        if evidence:
            for entry in evidence:
                line = Text()
                line.append("    \U0001f4ce ", style=f"bold {CLR_WARNING}")
                text_part = entry.lstrip("\U0001f4ce").strip()
                line.append(text_part, style=self._get_layer_color(entry))
                parts.append(line)
        else:
            parts.append(Text(f"    {L['no_data']}", style=CLR_DIM))

        # Theories
        theories = knowledge.get("theories", [])
        section_header(L["theories"], "\U0001f4a1", CLR_PRIMARY)
        if theories:
            for entry in theories:
                line = Text()
                line.append("    \U0001f4a1 ", style=f"bold {CLR_PRIMARY}")
                text_part = entry.lstrip("\U0001f4a1").strip()
                line.append(text_part, style=self._get_layer_color(entry))
                parts.append(line)
        else:
            parts.append(Text(f"    {L['no_data']}", style=CLR_DIM))

        # Connections
        connections = knowledge.get("connections", [])
        section_header(L["connections"], "\U0001f517", CLR_ACCENT)
        if connections:
            for entry in connections:
                line = Text()
                line.append("    \U0001f517 ", style=f"bold {CLR_ACCENT}")
                text_part = entry.lstrip("\U0001f517").strip()
                line.append(text_part, style=CLR_TEXT)
                parts.append(line)
        else:
            parts.append(Text(f"    {L['no_data']}", style=CLR_DIM))

        return Group(*parts)


class TracesPanel(Static):
    """Traces of Truth — shows only discovered traces.

    The total count, layer structure, and undiscovered trace details are
    hidden from the player to avoid spoiling the progression mystery.
    """

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Group:
        L = LABELS[self.lang]
        traces = self.data.get("traces", {})
        discovered = traces.get("discovered", [])
        parts = []

        # Title
        title = Text()
        title.append(f"\n  \u25c8 {L['traces']}", style=f"bold {CLR_ACCENT}")
        parts.append(title)
        parts.append(Text(""))

        # Discovered count (without revealing total)
        count_line = Text()
        count_line.append(f"  {L.get('discovered', 'Discovered')}: ", style=f"bold {CLR_TEXT}")
        count_line.append(f"{len(discovered)}", style=f"bold {CLR_ACCENT}")
        parts.append(count_line)
        parts.append(Text(""))

        if discovered:
            for d in discovered:
                trace_line = Text()
                trace_line.append("    \u25c6 ", style=f"bold {CLR_ACCENT}")
                trace_id = d.get("id", "")
                desc = d.get("description", "")
                turn = d.get("turn_discovered")
                trace_line.append(f"[{trace_id}] ", style=f"bold {CLR_PRIMARY}")
                trace_line.append(desc, style=CLR_TEXT)
                if turn is not None:
                    trace_line.append(f"  (Turn {turn})", style=CLR_DIM)
                parts.append(trace_line)
            parts.append(Text(""))
        else:
            parts.append(Text(f"  {L.get('no_traces', 'No traces discovered yet.')}", style=CLR_DIM))

        return Group(*parts)


class DistrictPanel(Static):
    """Current district/location display."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Group:
        L = LABELS[self.lang]
        loc = self.data.get("location", {})
        parts = []

        if not loc:
            parts.append(Text(f"\n  {L['no_data']}", style=CLR_DIM))
            return Group(*parts)

        # District name - large, colored by danger
        district = loc.get("district", "Unknown")
        danger = loc.get("danger_level", "safe").lower().strip()
        danger_color = DANGER_COLORS.get(danger, CLR_TEXT)

        district_line = Text()
        district_line.append(f"\n  \u25b6 ", style=danger_color)
        district_line.append(district, style=f"bold {danger_color}")
        parts.append(district_line)

        area = loc.get("area", "")
        if area:
            area_line = Text()
            area_line.append(f"    {L['area']}: ", style=CLR_MUTED)
            area_line.append(area, style=CLR_TEXT)
            parts.append(area_line)

        parts.append(Text(""))

        # Signal Strength waveform
        signal = loc.get("signal_strength", 0)
        signal_line = Text()
        signal_line.append(f"  {L['signal_strength']}: ", style=CLR_MUTED)
        signal_line.append_text(waveform_bar(signal, 100, width=20))
        signal_line.append(f" {signal}%", style=CLR_PRIMARY)
        parts.append(signal_line)

        # Danger Level
        danger_text = L.get(danger, danger.upper())
        danger_line = Text()
        danger_line.append(f"  {L['danger_level']}: ", style=CLR_MUTED)
        danger_line.append(f"\u25a0 {danger_text}", style=f"bold {danger_color}")
        parts.append(danger_line)

        # NEXUS Patrol
        patrol = loc.get("nexus_patrol", "none")
        patrol_color = CLR_GREEN if patrol.lower() == "none" else CLR_WARNING if patrol.lower() == "light" else CLR_DANGER
        patrol_line = Text()
        patrol_line.append(f"  {L['nexus_patrol']}: ", style=CLR_MUTED)
        patrol_line.append(patrol, style=f"bold {patrol_color}")
        parts.append(patrol_line)

        parts.append(Text(""))

        # Description
        desc = loc.get("description", "")
        if desc:
            desc_header = Text()
            desc_header.append(f"  {L['description']}:", style=f"bold {CLR_MUTED}")
            parts.append(desc_header)
            for line in desc.split("\n"):
                if line.strip():
                    desc_line = Text()
                    desc_line.append(f"    {line.strip()}", style=f"italic {CLR_TEXT}")
                    parts.append(desc_line)
            parts.append(Text(""))

        # Exits
        exits = loc.get("exits", [])
        if exits:
            exits_header = Text()
            exits_header.append(f"  {L['exits']}:", style=f"bold {CLR_PRIMARY}")
            parts.append(exits_header)
            for ex in exits:
                ex_line = Text()
                ex_line.append(f"    \u25b8 ", style=CLR_PRIMARY)
                ex_line.append(ex, style=CLR_TEXT)
                parts.append(ex_line)
            parts.append(Text(""))

        # POIs
        pois = loc.get("pois", [])
        if pois:
            poi_header = Text()
            poi_header.append(f"  {L['poi']}:", style=f"bold {CLR_WARNING}")
            parts.append(poi_header)
            for p in pois:
                p_line = Text()
                p_line.append(f"    \u2726 ", style=CLR_WARNING)
                p_line.append(p, style=CLR_TEXT)
                parts.append(p_line)
            parts.append(Text(""))

        # NPCs
        npcs = loc.get("npcs", [])
        if npcs:
            npc_header = Text()
            npc_header.append(f"  {L['npcs_present']}:", style=f"bold {CLR_GREEN}")
            parts.append(npc_header)
            for n in npcs:
                n_line = Text()
                n_line.append(f"    \u25c8 ", style=CLR_GREEN)
                n_line.append(n, style=CLR_TEXT)
                parts.append(n_line)

        return Group(*parts)


class InventoryPanel(Static):
    """Inventory display with 6-slot grid."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Group:
        L = LABELS[self.lang]
        inv = self.data.get("inventory", {})
        parts = []

        # Credits
        credits_line = Text()
        credits_line.append(f"\n  {L['credits']}: ", style=CLR_MUTED)
        credits_line.append(f"\u00a4 {inv.get('credits', 0)}", style=f"bold {CLR_WARNING}")
        credits_line.append(f"    {L['slots']}: ", style=CLR_MUTED)
        credits_line.append(f"{inv.get('slots_used', 0)} / {inv.get('slots_max', 6)}", style=CLR_TEXT)
        parts.append(credits_line)
        parts.append(Text(""))

        items = inv.get("items", [])
        item_by_slot = {}
        for item in items:
            try:
                slot_num = int(item.get("slot", 0))
            except ValueError:
                slot_num = 0
            item_by_slot[slot_num] = item

        # 6 slots in 2 rows of 3
        for row in range(2):
            row_parts = []
            for col in range(3):
                slot_num = row * 3 + col + 1
                item = item_by_slot.get(slot_num)

                if item:
                    item_type = item.get("type", "").lower().strip()
                    icon = ITEM_ICONS.get(item_type, "\u25a0")
                    name = item.get("name", "???")
                    desc = item.get("description", "")

                    # Slot box with item
                    slot_text = Text()
                    slot_text.append(f"  \u250c\u2500\u2500 {L['slot']} {slot_num} ", style=CLR_PRIMARY)
                    slot_text.append("\u2500" * 18 + "\u2510\n", style=CLR_PRIMARY)
                    slot_text.append(f"  \u2502 {icon} ", style=CLR_PRIMARY)
                    slot_text.append(f"{name[:20]:<20s}", style=f"bold {CLR_TEXT}")
                    slot_text.append(" \u2502\n", style=CLR_PRIMARY)
                    slot_text.append(f"  \u2502   ", style=CLR_PRIMARY)
                    type_display = item_type.replace("_", " ").upper()
                    slot_text.append(f"{type_display[:20]:<20s}", style=CLR_MUTED)
                    slot_text.append(" \u2502\n", style=CLR_PRIMARY)
                    slot_text.append(f"  \u2502   ", style=CLR_PRIMARY)
                    slot_text.append(f"{desc[:20]:<20s}", style=CLR_DIM)
                    slot_text.append(" \u2502\n", style=CLR_PRIMARY)
                    slot_text.append(f"  \u2514" + "\u2500" * 24 + "\u2518", style=CLR_PRIMARY)
                    parts.append(slot_text)
                else:
                    # Empty slot
                    slot_text = Text()
                    slot_text.append(f"  \u250c\u2500\u2500 {L['slot']} {slot_num} ", style=CLR_DIM)
                    slot_text.append("\u2500" * 18 + "\u2510\n", style=CLR_DIM)
                    slot_text.append(f"  \u2502", style=CLR_DIM)
                    slot_text.append(f"{'':24s}", style="")
                    slot_text.append("\u2502\n", style=CLR_DIM)
                    slot_text.append(f"  \u2502", style=CLR_DIM)
                    empty_label = L["empty"]
                    slot_text.append(f"    {empty_label:^16s}    ", style=CLR_DIM)
                    slot_text.append("\u2502\n", style=CLR_DIM)
                    slot_text.append(f"  \u2502", style=CLR_DIM)
                    slot_text.append(f"{'':24s}", style="")
                    slot_text.append("\u2502\n", style=CLR_DIM)
                    slot_text.append(f"  \u2514" + "\u2500" * 24 + "\u2518", style=CLR_DIM)
                    parts.append(slot_text)

            parts.append(Text(""))

        return Group(*parts)


class NetworkPanel(Static):
    """NPC network/trust display."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Group:
        L = LABELS[self.lang]
        npcs = self.data.get("npcs", [])
        parts = []

        title = Text()
        title.append(f"\n  \u25c8 {L['npc_tracker']}", style=f"bold {CLR_PRIMARY}")
        parts.append(title)
        parts.append(Text(""))

        if not npcs:
            parts.append(Text(f"  {L['no_data']}", style=CLR_DIM))
            return Group(*parts)

        for npc in npcs:
            name = npc.get("name", "???")
            faction = npc.get("faction", npc.get("Faction", "Unknown"))
            trust = npc.get("trust_level", npc.get("trust", npc.get("Trust", "neutral")))
            location = npc.get("location_last_seen", npc.get("location", ""))
            quest = npc.get("quest_status", npc.get("quest", ""))
            notes = npc.get("notes", npc.get("Notes", ""))

            # Normalize trust for color lookup
            trust_key = _extract_english_key(trust, TRUST_COLORS)
            trust_color = TRUST_COLORS.get(trust_key, CLR_WARNING)

            # Normalize faction for color lookup
            faction_key = _extract_english_key(faction, FACTION_COLORS)
            faction_color = FACTION_COLORS.get(faction_key, CLR_MUTED)

            # NPC name line
            name_line = Text()
            name_line.append(f"  \u25c8 ", style=trust_color)
            name_line.append(name, style=f"bold {CLR_TEXT}")
            parts.append(name_line)

            # Faction
            faction_line = Text()
            faction_line.append(f"    {L['faction']}: ", style=CLR_MUTED)
            faction_line.append(faction, style=f"bold {faction_color}")
            parts.append(faction_line)

            # Trust bar
            trust_levels = ["hostile", "suspicious", "neutral", "cautious_ally", "trusted", "devoted"]
            trust_idx = 0
            for i, t in enumerate(trust_levels):
                if trust_key == t:
                    trust_idx = i
                    break

            trust_line = Text()
            trust_line.append(f"    {L['trust']}: ", style=CLR_MUTED)
            trust_line.append_text(bar(trust_idx + 1, len(trust_levels), width=12,
                                       fill_style=trust_color, empty_style=CLR_DIM))
            trust_line.append(f" {trust}", style=trust_color)
            parts.append(trust_line)

            # Location
            if location:
                loc_line = Text()
                loc_line.append(f"    {L['location_seen']}: ", style=CLR_MUTED)
                loc_line.append(location, style=CLR_TEXT)
                parts.append(loc_line)

            # Quest
            if quest and quest.lower() != "none":
                quest_line = Text()
                quest_line.append(f"    {L['quest_status']}: ", style=CLR_MUTED)
                quest_line.append(quest, style=CLR_PRIMARY)
                parts.append(quest_line)

            # Notes
            if notes:
                notes_line = Text()
                notes_line.append(f"    {L['notes']}: ", style=CLR_MUTED)
                notes_line.append(notes, style=CLR_DIM)
                parts.append(notes_line)

            # Separator
            parts.append(Text(f"    {'.' * 40}", style=CLR_DIM))

        return Group(*parts)


class WorldPanel(Static):
    """World state display."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Group:
        L = LABELS[self.lang]
        world = self.data.get("world_state", {})
        parts = []

        if not world:
            parts.append(Text(f"\n  {L['no_data']}", style=CLR_DIM))
            return Group(*parts)

        # NEXUS Alert - BIG bar with gradient
        alert = world.get("nexus_alert", 0)
        alert_status = world.get("alert_status", "")

        alert_header = Text()
        alert_header.append(f"\n  \u26a0 {L['nexus_alert']}", style=f"bold {CLR_DANGER}")
        parts.append(alert_header)

        alert_bar = Text()
        alert_bar.append("  ")
        alert_bar.append_text(bar(alert, 100, width=40, gradient=True))
        alert_bar.append(f" {alert}%", style=f"bold {CLR_DANGER if alert > 60 else CLR_WARNING if alert > 30 else CLR_GREEN}")
        parts.append(alert_bar)

        if alert_status:
            status_line = Text()
            status_line.append(f"  Status: ", style=CLR_MUTED)
            status_line.append(alert_status.upper(), style=f"bold {CLR_DANGER if alert > 60 else CLR_WARNING}")
            parts.append(status_line)

        parts.append(Text(""))

        # Fragment Decay - magenta bar
        decay = world.get("fragment_decay", 0)
        fragment_status = world.get("fragment_status", "")

        decay_header = Text()
        decay_header.append(f"  \u25c6 {L['fragment_decay']}", style=f"bold {CLR_ACCENT}")
        parts.append(decay_header)

        decay_bar = Text()
        decay_bar.append("  ")
        decay_bar.append_text(bar(decay, 100, width=40, fill_style=CLR_ACCENT, empty_style=CLR_DIM))
        decay_bar.append(f" {decay}%", style=f"bold {CLR_ACCENT}")
        parts.append(decay_bar)

        if fragment_status:
            fs_line = Text()
            fs_line.append(f"  Status: ", style=CLR_MUTED)
            fs_line.append(fragment_status.upper(), style=f"bold {CLR_ACCENT}")
            parts.append(fs_line)

        parts.append(Text(""))

        # District Access Table
        districts = world.get("districts", [])
        if districts:
            dist_header = Text()
            dist_header.append(f"  {L['district_access']}:", style=f"bold {CLR_PRIMARY}")
            parts.append(dist_header)

            for d in districts:
                status = d.get("status", "").strip("[]").lower()
                status_color = CLR_GREEN if status == "open" else CLR_DANGER if status == "locked" else CLR_WARNING
                status_icon = "\u25c6" if status == "open" else "\u25cb" if status == "locked" else "\u25d4"

                d_line = Text()
                d_line.append(f"    {status_icon} ", style=status_color)
                d_line.append(f"{d.get('name', '')}", style=CLR_TEXT)
                if d.get("chinese"):
                    d_line.append(f" ({d['chinese']})", style=CLR_DIM)
                d_line.append(f" [{status}]", style=status_color)
                parts.append(d_line)

            parts.append(Text(""))

        # Period
        period = world.get("period", "")
        if period:
            period_line = Text()
            period_line.append(f"  {L['period']}: ", style=CLR_MUTED)
            time_icon = "\U0001f319" if "night" in period.lower() or "\u591c" in period else "\u2600"
            period_line.append(f"{time_icon} {period}", style=CLR_PRIMARY)
            parts.append(period_line)

        # Global Events
        events = world.get("events", [])
        if events:
            parts.append(Text(""))
            events_header = Text()
            events_header.append(f"  {L['global_events']}:", style=f"bold {CLR_WARNING}")
            parts.append(events_header)
            for ev in events:
                ev_line = Text()
                ev_line.append(f"    \u25b8 ", style=CLR_WARNING)
                ev_line.append(ev, style=CLR_TEXT)
                parts.append(ev_line)

        return Group(*parts)


class LogPanel(Static):
    """Session log display."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Group:
        L = LABELS[self.lang]
        log_entries = self.data.get("log", [])
        parts = []

        title = Text()
        title.append(f"\n  \u25c8 {L['session_log']}", style=f"bold {CLR_PRIMARY}")
        parts.append(title)
        parts.append(Text(""))

        if not log_entries:
            parts.append(Text(f"  {L['no_data']}", style=CLR_DIM))
            return Group(*parts)

        # Reverse chronological
        for entry in reversed(log_entries):
            turn = entry.get("turn", 0)
            title_text = entry.get("title", "")
            tag = entry.get("tag", "system")
            desc = entry.get("description", "")
            color = TAG_COLORS.get(tag, CLR_MUTED)

            header_line = Text()
            header_line.append(f"  [{tag.upper():^10s}] ", style=f"bold {color}")
            header_line.append(f"Turn {turn} ", style=CLR_MUTED)
            header_line.append(f"\u2014 {title_text}", style=f"bold {color}")
            parts.append(header_line)

            if desc:
                desc_line = Text()
                desc_line.append(f"             {desc}", style=CLR_TEXT)
                parts.append(desc_line)

            parts.append(Text(f"  {'- ' * 25}", style=CLR_DIM))

        return Group(*parts)


class ToolsPanel(Static):
    """Tools interface panel."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Group:
        L = LABELS[self.lang]
        parts = []

        title = Text()
        title.append(f"\n  \u25c8 {L['tools']}", style=f"bold {CLR_PRIMARY}")
        parts.append(title)
        parts.append(Text(""))

        # Tool buttons/labels
        tools_info = [
            (L["tool_dice"], "\U0001f3b2", CLR_PRIMARY,
             "Roll dice for skill checks and random events"),
            (L["tool_cipher"], "\U0001f510", CLR_GREEN,
             "Decode encrypted data chips and messages"),
            (L["tool_signal"], "\U0001f4e1", CLR_ACCENT,
             "Scan for Signal traces and Fragment resonance"),
            (L["tool_map"], "\U0001f5fa", CLR_WARNING,
             "View district map and navigation routes"),
        ]

        for tool_name, icon, color, desc in tools_info:
            tool_line = Text()
            tool_line.append(f"  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510", style=color)
            parts.append(tool_line)

            name_line = Text()
            name_line.append(f"  \u2502 {icon} ", style=color)
            name_line.append(f"{tool_name:<24s}", style=f"bold {color}")
            name_line.append(" \u2502", style=color)
            parts.append(name_line)

            desc_line = Text()
            desc_line.append(f"  \u2502   ", style=color)
            desc_line.append(f"{desc[:24]:<24s}", style=CLR_DIM)
            desc_line.append(" \u2502", style=color)
            parts.append(desc_line)

            bottom_line = Text()
            bottom_line.append(f"  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518", style=color)
            parts.append(bottom_line)
            parts.append(Text(""))

        # Results area placeholder
        parts.append(Text(""))
        results_header = Text()
        results_header.append("  Results:", style=f"bold {CLR_MUTED}")
        parts.append(results_header)
        results_line = Text()
        results_line.append("  Enter a tool command below (d=focus input)", style=CLR_DIM)
        parts.append(results_line)

        return Group(*parts)


# =============================================================================
# STATUS BAR WIDGET
# =============================================================================

class StatusBar(Static):
    """Top status bar showing key metrics at a glance."""

    def __init__(self, data: dict, lang: str = "en", **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.lang = lang

    def render(self) -> Text:
        player = self.data.get("player", {})
        traces = self.data.get("traces", {})
        world = self.data.get("world_state", {})
        location = self.data.get("location", {})

        line = Text()

        # Alias
        alias = player.get("alias", "???")
        line.append(" \u25c8 ", style=f"bold {CLR_ACCENT}")
        line.append(_cjk_ljust(alias, 12), style=f"bold {CLR_PRIMARY}")
        line.append(" \u2502 ", style=CLR_DIM)

        # Integrity pips
        ic = player.get("integrity_current", 0)
        im = player.get("integrity_max", 3)
        for i in range(im):
            if i < ic:
                line.append("\u2588", style=f"bold {CLR_GREEN}")
            else:
                line.append("\u2591", style=CLR_DIM)
        line.append(f" {ic}/{im}", style=CLR_TEXT)
        line.append(" \u2502 ", style=CLR_DIM)

        # Traces
        td = traces.get("total_discovered", 0)
        tm = traces.get("total_max", 16)
        trace_filled = min(5, int(td / max(tm, 1) * 5))
        for i in range(5):
            if i < trace_filled:
                line.append("\u25c6", style=f"bold {CLR_ACCENT}")
            else:
                line.append("\u25cb", style=CLR_DIM)
        line.append(f" {td}/{tm}", style=CLR_TEXT)
        line.append(" \u2502 ", style=CLR_DIM)

        # Alert
        alert = world.get("nexus_alert", 0)
        line.append("Alert: ", style=CLR_MUTED)
        alert_width = 10
        alert_filled = int(alert / 100 * alert_width)
        for i in range(alert_width):
            if i < alert_filled:
                if i < 4:
                    line.append("\u2588", style=CLR_GREEN)
                elif i < 7:
                    line.append("\u2588", style=CLR_WARNING)
                else:
                    line.append("\u2588", style=CLR_DANGER)
            else:
                line.append("\u2591", style=CLR_DIM)
        line.append(f" {alert}%", style=CLR_TEXT)
        line.append(" \u2502 ", style=CLR_DIM)

        # District
        district = location.get("district", "???")
        line.append(district, style=CLR_PRIMARY)
        line.append(" \u2502 ", style=CLR_DIM)

        # Time
        time_str = player.get("time", "")
        if "night" in time_str.lower() or "\u591c" in time_str:
            line.append("\U0001f319 ", style="")
        elif "afternoon" in time_str.lower() or "\u5348" in time_str:
            line.append("\u2600 ", style="")
        else:
            line.append("\U0001f305 ", style="")
        line.append(time_str, style=CLR_TEXT)

        return line


# =============================================================================
# CSS GENERATOR
# =============================================================================

def make_css(with_terminal: bool) -> str:
    css = f"""
    Screen {{
        background: {CLR_BG};
    }}

    #status-bar {{
        dock: top;
        height: 1;
        background: {CLR_BAR_BG};
        color: {CLR_TEXT};
        border-bottom: solid {CLR_DIM};
        padding: 0 1;
    }}

    #main-container {{
        height: 1fr;
    }}

    #terminal-panel {{
        width: {'50%' if with_terminal else '0'};
        {'display: block;' if with_terminal else 'display: none;'}
    }}

    #content-panel {{
        width: {'50%' if with_terminal else '100%'};
    }}

    PtyTerminal {{
        height: 1fr;
        width: 1fr;
        border: solid {CLR_DIM};
    }}

    PtyTerminal:focus {{
        border: solid {CLR_PRIMARY};
    }}

    TabbedContent {{
        height: 1fr;
    }}

    TabPane {{
        padding: 0;
        background: {CLR_BG};
    }}

    ContentSwitcher {{
        height: 1fr;
    }}

    Tabs {{
        dock: top;
        background: {CLR_BAR_BG};
    }}

    Tab {{
        color: {CLR_MUTED};
        background: {CLR_BAR_BG};
        padding: 0 1;
    }}

    Tab.-active {{
        color: {CLR_PRIMARY};
        background: {CLR_BG};
        text-style: bold;
    }}

    Tab:hover {{
        color: {CLR_ACCENT};
    }}

    VerticalScroll {{
        height: 1fr;
        background: {CLR_BG};
    }}

    #tools-input {{
        dock: bottom;
        margin: 0 1;
        border: solid {CLR_DIM};
        background: {CLR_BAR_BG};
        color: {CLR_PRIMARY};
    }}

    #tools-input:focus {{
        border: solid {CLR_ACCENT};
    }}

    Footer {{
        background: {CLR_BAR_BG};
        color: {CLR_MUTED};
    }}
    """
    return css


# =============================================================================
# MAIN APP
# =============================================================================

class GameTUI(App):
    """Signal Lost TUI Application."""

    TITLE = "Signal Lost / \u4fe1\u53f7\u9057\u5931"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=False),
        Binding("r", "refresh", "Refresh", show=True, priority=False),
        Binding("t", "focus_terminal", "Terminal", show=True, priority=False),
        Binding("d", "focus_tools_input", "Tools Input", show=True, priority=False),
        Binding("1", "tab_1", "1", show=False, priority=False),
        Binding("2", "tab_2", "2", show=False, priority=False),
        Binding("3", "tab_3", "3", show=False, priority=False),
        Binding("4", "tab_4", "4", show=False, priority=False),
        Binding("5", "tab_5", "5", show=False, priority=False),
        Binding("6", "tab_6", "6", show=False, priority=False),
        Binding("7", "tab_7", "7", show=False, priority=False),
        Binding("8", "tab_8", "8", show=False, priority=False),
        Binding("9", "tab_9", "9", show=False, priority=False),
    ]

    def __init__(
        self,
        game_dir: Path,
        with_terminal: bool = True,
        refresh_interval: int = 5,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.game_dir = game_dir
        self.with_terminal = with_terminal
        self.refresh_interval = refresh_interval
        self.parser = SessionParser(game_dir)
        self.session_data: dict = {}
        self.lang = "en"

        # Load language setting
        settings = self.parser.parse_settings()
        self.lang = settings.get("language", {}).get("tui", "en")
        if self.lang not in LABELS:
            self.lang = "en"

        self.css = make_css(with_terminal)

    @property
    def L(self) -> dict:
        return LABELS[self.lang]

    def compose(self) -> ComposeResult:
        yield StatusBar(self.session_data, self.lang, id="status-bar")
        with Horizontal(id="main-container"):
            if self.with_terminal:
                with Vertical(id="terminal-panel"):
                    yield PtyTerminal(id="pty-terminal")
            with Vertical(id="content-panel"):
                L = self.L
                with TabbedContent(
                    L["tab_identity"],
                    L["tab_knowledge"],
                    L["tab_traces"],
                    L["tab_district"],
                    L["tab_inventory"],
                    L["tab_network"],
                    L["tab_world"],
                    L["tab_log"],
                    L["tab_tools"],
                    id="tabs",
                ):
                    with TabPane(L["tab_identity"], id="tab-identity"):
                        with VerticalScroll():
                            yield IdentityPanel(self.session_data, self.lang, id="panel-identity")
                    with TabPane(L["tab_knowledge"], id="tab-knowledge"):
                        with VerticalScroll():
                            yield KnowledgePanel(self.session_data, self.lang, id="panel-knowledge")
                    with TabPane(L["tab_traces"], id="tab-traces"):
                        with VerticalScroll():
                            yield TracesPanel(self.session_data, self.lang, id="panel-traces")
                    with TabPane(L["tab_district"], id="tab-district"):
                        with VerticalScroll():
                            yield DistrictPanel(self.session_data, self.lang, id="panel-district")
                    with TabPane(L["tab_inventory"], id="tab-inventory"):
                        with VerticalScroll():
                            yield InventoryPanel(self.session_data, self.lang, id="panel-inventory")
                    with TabPane(L["tab_network"], id="tab-network"):
                        with VerticalScroll():
                            yield NetworkPanel(self.session_data, self.lang, id="panel-network")
                    with TabPane(L["tab_world"], id="tab-world"):
                        with VerticalScroll():
                            yield WorldPanel(self.session_data, self.lang, id="panel-world")
                    with TabPane(L["tab_log"], id="tab-log"):
                        with VerticalScroll():
                            yield LogPanel(self.session_data, self.lang, id="panel-log")
                    with TabPane(L["tab_tools"], id="tab-tools"):
                        with VerticalScroll():
                            yield ToolsPanel(self.session_data, self.lang, id="panel-tools")
                        yield Input(
                            placeholder=self.L["tools_input_placeholder"],
                            id="tools-input",
                        )
        yield Footer()

    def on_mount(self) -> None:
        # Start terminal if enabled
        if self.with_terminal:
            try:
                terminal = self.query_one("#pty-terminal", PtyTerminal)
                terminal.start()
            except NoMatches:
                pass

        # Initial data load
        self._load_data()
        self._update_all_panels()

        # Set auto-refresh timer
        if self.refresh_interval > 0:
            self.set_interval(self.refresh_interval, self._periodic_refresh)

    def on_unmount(self) -> None:
        if self.with_terminal:
            try:
                terminal = self.query_one("#pty-terminal", PtyTerminal)
                terminal.cleanup()
            except NoMatches:
                pass

    def _load_data(self) -> None:
        self.session_data = self.parser.parse_all()

    def _update_all_panels(self) -> None:
        """Update all panel widgets with current session data."""
        panel_map = {
            "#status-bar": StatusBar,
            "#panel-identity": IdentityPanel,
            "#panel-knowledge": KnowledgePanel,
            "#panel-traces": TracesPanel,
            "#panel-district": DistrictPanel,
            "#panel-inventory": InventoryPanel,
            "#panel-network": NetworkPanel,
            "#panel-world": WorldPanel,
            "#panel-log": LogPanel,
            "#panel-tools": ToolsPanel,
        }

        for widget_id, widget_cls in panel_map.items():
            try:
                widget = self.query_one(widget_id)
                widget.data = self.session_data
                widget.lang = self.lang
                widget.refresh()
            except NoMatches:
                pass

    def action_refresh(self) -> None:
        self._load_data()
        self._update_all_panels()
        self.notify("Refreshed", timeout=1.5)

    def _periodic_refresh(self) -> None:
        self._load_data()
        self._update_all_panels()

    def action_focus_terminal(self) -> None:
        if self.with_terminal:
            try:
                terminal = self.query_one("#pty-terminal", PtyTerminal)
                terminal.focus()
            except NoMatches:
                pass

    def action_focus_tools_input(self) -> None:
        try:
            tools_input = self.query_one("#tools-input", Input)
            tools_input.focus()
        except NoMatches:
            pass

    def _switch_tab(self, index: int) -> None:
        try:
            tabs = self.query_one("#tabs", TabbedContent)
            tab_ids = [
                "tab-identity", "tab-knowledge", "tab-traces",
                "tab-district", "tab-inventory", "tab-network",
                "tab-world", "tab-log", "tab-tools",
            ]
            if 0 <= index < len(tab_ids):
                tabs.active = tab_ids[index]
        except NoMatches:
            pass

    def action_tab_1(self) -> None:
        self._switch_tab(0)

    def action_tab_2(self) -> None:
        self._switch_tab(1)

    def action_tab_3(self) -> None:
        self._switch_tab(2)

    def action_tab_4(self) -> None:
        self._switch_tab(3)

    def action_tab_5(self) -> None:
        self._switch_tab(4)

    def action_tab_6(self) -> None:
        self._switch_tab(5)

    def action_tab_7(self) -> None:
        self._switch_tab(6)

    def action_tab_8(self) -> None:
        self._switch_tab(7)

    def action_tab_9(self) -> None:
        self._switch_tab(8)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle tool command submission."""
        command = event.value.strip()
        if not command:
            return
        event.input.value = ""

        # Simple tool command routing
        result_text = Text()
        cmd_lower = command.lower()

        if cmd_lower.startswith("dice") or cmd_lower.startswith("roll"):
            import random
            parts = command.split()
            sides = 20
            if len(parts) > 1:
                try:
                    sides = int(parts[1])
                except ValueError:
                    pass
            roll = random.randint(1, sides)
            result_text.append(f"\n  \U0001f3b2 Roll d{sides}: ", style=CLR_MUTED)
            result_text.append(str(roll), style=f"bold {CLR_PRIMARY}")
            if roll == sides:
                result_text.append(" CRITICAL!", style=f"bold {CLR_GREEN}")
            elif roll == 1:
                result_text.append(" FUMBLE!", style=f"bold {CLR_DANGER}")

        elif cmd_lower.startswith("cipher") or cmd_lower.startswith("decode"):
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                encoded = parts[1]
                # Simple ROT13 cipher tool
                decoded = encoded.encode("utf-8").decode("utf-8")
                try:
                    import codecs
                    decoded = codecs.decode(encoded, "rot_13")
                except Exception:
                    pass
                result_text.append(f"\n  \U0001f510 Cipher result: ", style=CLR_MUTED)
                result_text.append(decoded, style=f"bold {CLR_GREEN}")
            else:
                result_text.append("\n  Usage: cipher <text>", style=CLR_DIM)

        elif cmd_lower.startswith("signal") or cmd_lower.startswith("scan"):
            loc = self.session_data.get("location", {})
            strength = loc.get("signal_strength", 0)
            result_text.append(f"\n  \U0001f4e1 Signal Scan: ", style=CLR_MUTED)
            result_text.append_text(waveform_bar(strength, 100, width=30))
            result_text.append(f" {strength}%", style=CLR_ACCENT)

        elif cmd_lower.startswith("map"):
            world = self.session_data.get("world_state", {})
            districts = world.get("districts", [])
            result_text.append(f"\n  \U0001f5fa District Map:", style=f"bold {CLR_WARNING}")
            if districts:
                for d in districts:
                    status = d.get("status", "").strip("[]")
                    icon = "\u25c6" if status == "open" else "\u25cb"
                    color = CLR_GREEN if status == "open" else CLR_DANGER
                    result_text.append(f"\n    {icon} ", style=color)
                    result_text.append(d.get("name", ""), style=CLR_TEXT)
                    result_text.append(f" [{status}]", style=color)
            else:
                result_text.append("\n    No district data available", style=CLR_DIM)

        else:
            result_text.append(f"\n  Unknown command: {command}", style=CLR_DANGER)
            result_text.append("\n  Available: dice, cipher, signal, map", style=CLR_DIM)

        # Update tools panel with result
        try:
            tools_panel = self.query_one("#panel-tools", ToolsPanel)
            tools_panel._last_result = result_text
            tools_panel.refresh()
        except NoMatches:
            pass


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def _resolve_game_dir(arg: Optional[str] = None) -> Path:
    """Resolve the game directory from CLI arg or auto-detect."""
    if arg:
        p = Path(arg).resolve()
        if p.is_dir():
            return p
        raise FileNotFoundError(f"Game directory not found: {p}")

    # Auto-detect: walk up from cwd looking for session/ or game/ dirs
    cwd = Path.cwd()
    for candidate in [cwd, cwd.parent, cwd.parent.parent]:
        if (candidate / "session").is_dir() or (candidate / "game").is_dir():
            return candidate

    # Fallback: use cwd
    return cwd


def main():
    parser = argparse.ArgumentParser(
        description="Signal Lost TUI Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "game_dir",
        nargs="?",
        default=None,
        help="Path to the game root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--terminal",
        default="true",
        help="Enable embedded terminal (true/false, default: true)",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=5,
        help="Auto-refresh interval in seconds (default: 5)",
    )

    args = parser.parse_args()

    game_dir = _resolve_game_dir(args.game_dir)
    with_terminal = args.terminal.lower() in ("true", "1", "yes", "on")

    app = GameTUI(
        game_dir=game_dir,
        with_terminal=with_terminal,
        refresh_interval=args.refresh,
    )
    app.run()


if __name__ == "__main__":
    main()
