#!/usr/bin/env python3
"""
Agentic Game — TUI Viewer Template
====================================
A generic Textual-based terminal UI template for any agentic game that follows
the structure defined in game_template.md. Game creators should copy this file
into their game's tui/ folder and customize the SessionParser methods, panel
widgets, and tab layout to match their game's session schema.

Usage:
    .venv/bin/python tui/tui_viewer.py [game_directory] [--terminal true|false]

Arguments:
    game_directory   Path to the game root (default: auto-detect from cwd)
    --terminal       Enable or disable the integrated PTY terminal panel
                     (default: true). When enabled, a live shell is embedded
                     on the left side of the screen. When disabled, the tabbed
                     content takes the full width.

Dependencies (install via uv in the game root):
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


# ═══════════════════════════════════════════════════════════════════════════════
# PTY TERMINAL WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
#
# The PtyTerminal widget embeds a real pseudo-terminal (PTY) shell inside the
# TUI. This lets the player interact with their AI agent (e.g. Claude Code)
# in one half of the screen while viewing game state in the other half.
#
# How it works:
#   1. On mount, a pyte virtual terminal screen is created to track terminal
#      state (cursor position, colors, scrollback, alternate screen buffer).
#   2. On start(), a subprocess is spawned attached to a PTY (via pty.openpty).
#      The master file descriptor is kept for reading output and writing input.
#   3. A poll loop (_poll_pty) runs every 20ms, reading any new output from
#      the PTY and feeding it through pyte's ANSI parser. Dirty lines trigger
#      a widget refresh.
#   4. Keyboard input is captured in on_key() and translated to the correct
#      escape sequences (arrow keys, function keys, ctrl combos) before being
#      written to the PTY master fd.
#   5. The terminal supports:
#      - Full ANSI color (256-color via xterm-256color TERM)
#      - Alternate screen buffer (for programs like vim, less, htop)
#      - Scrollback history (Shift+PageUp / Shift+PageDown / mouse wheel)
#      - Dynamic resize when the widget size changes
#      - Cursor rendering (reverse video on the focused cell)
#      - Wide character (CJK) support
#
# Focus behavior:
#   - When focused (click or press 't'), the terminal captures ALL keyboard
#     input — including keys that would normally be Textual bindings (q, r, d,
#     1-8). This is correct: the user is typing in the shell.
#   - Press Escape then a binding key to interact with the TUI while the
#     terminal is focused, or click outside the terminal to blur it.
#   - The border changes color to indicate focus state.
#
# Platform notes:
#   - Requires Unix (pty, fcntl, termios). Does not work on native Windows.
#   - The shell defaults to the user's SHELL env var, falling back to "bash".
# ═══════════════════════════════════════════════════════════════════════════════

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
        bracketed = self._pty_screen and (2004 in self._pty_screen.mode)
        payload = text.encode("utf-8")
        if bracketed:
            self._write_bytes(b"\x1b[200~" + payload + b"\x1b[201~")
        else:
            self._write_bytes(payload)
        event.prevent_default()
        event.stop()

    # ── Clipboard: Mouse selection & Copy ─────────────────────────────────

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


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION PARSER
# ═══════════════════════════════════════════════════════════════════════════════
#
# The SessionParser reads markdown and JSON files from the game's session/,
# settings/, and game/ directories, extracting structured data via regex.
#
# CUSTOMIZATION: Replace or add parse_*() methods to match your game's session
# file schema. Each method should return a dict (or list[dict]) and handle
# missing files gracefully (return empty dict/list, never crash).
# ═══════════════════════════════════════════════════════════════════════════════

class SessionParser:
    """Parses all session files from an agentic game directory.

    Subclass or modify this to match your game's specific file layout and
    markdown patterns. Each parse_*() method corresponds to one session file.
    """

    def __init__(self, game_dir: str):
        self.game_dir = Path(game_dir)
        self.session_dir = self.game_dir / "session"
        self.settings_dir = self.game_dir / "settings"
        self.game_data_dir = self.game_dir / "game"
        self.tools_dir = self.game_dir / "tools"

    def _read(self, path: Path) -> str:
        """Read a file, returning empty string if missing or unreadable."""
        try:
            return path.read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError):
            return ""

    # ── Player / Character ────────────────────────────────────────────────
    # CUSTOMIZE: Parse your game's player/character session file.
    # Common patterns to extract:
    #   **Key:** Value         -> key-value pairs
    #   | col1 | col2 |       -> table rows
    #   - [x] Item / - [ ]    -> checklists
    #   ## Section             -> section splitting
    def parse_player(self) -> dict:
        text = self._read(self.session_dir / "player.md")
        if not text:
            return {}
        p = {}
        # Example: extract name from "# Player: <name>"
        m = re.search(r"# Player:\s*(.+)", text)
        p["name"] = m.group(1).strip() if m else "Unknown"
        # Example: extract class from "**Class:** <class>"
        m = re.search(r"\*\*Class:\*\*\s*(.+)", text)
        p["class"] = m.group(1).strip() if m else "Unknown"
        # Example: extract stats from a markdown table
        # | Stat | Base | Current |
        # | HP   | 100  | 73      |
        p["stats"] = {}
        for m in re.finditer(r"\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", text):
            p["stats"][m.group(1)] = {"base": int(m.group(2)), "current": int(m.group(3))}
        # Example: extract turn counter
        m = re.search(r"\*\*Turns Elapsed:\*\*\s*(\d+)", text)
        p["turns"] = int(m.group(1)) if m else 0
        return p

    # ── World State ───────────────────────────────────────────────────────
    # CUSTOMIZE: Parse global state, threat meters, region statuses, etc.
    def parse_world_state(self) -> dict:
        text = self._read(self.session_dir / "world_state.md")
        if not text:
            return {}
        w = {}
        # Example: threat percentage
        m = re.search(r"\*\*(?:Threat|Corruption).*?:\*\*\s*(\d+)%", text)
        w["threat_pct"] = int(m.group(1)) if m else 0
        return w

    # ── Location ──────────────────────────────────────────────────────────
    # CUSTOMIZE: Parse current location, exits, points of interest.
    def parse_location(self) -> dict:
        text = self._read(self.session_dir / "location.md")
        if not text:
            return {}
        loc = {}
        m = re.search(r"\*\*(?:Location|Area):\*\*\s*(.+)", text)
        loc["name"] = m.group(1).strip() if m else "Unknown"
        # Extract exits from a bulleted list under "## Exits"
        loc["exits"] = []
        in_exits = False
        for line in text.split("\n"):
            if "## Exits" in line:
                in_exits = True
                continue
            if in_exits and line.startswith("## "):
                break
            if in_exits and line.startswith("- "):
                loc["exits"].append(line.lstrip("- ").strip())
        return loc

    # ── Inventory ─────────────────────────────────────────────────────────
    # CUSTOMIZE: Parse items, currency, slot usage.
    def parse_inventory(self) -> dict:
        text = self._read(self.session_dir / "inventory.md")
        if not text:
            return {}
        inv = {}
        m = re.search(r"\*\*(?:Gold|Currency):\*\*\s*(\d+)", text)
        inv["currency"] = int(m.group(1)) if m else 0
        return inv

    # ── Companions ────────────────────────────────────────────────────────
    # CUSTOMIZE: Parse party members, their stats, disposition.
    def parse_companions(self) -> dict:
        text = self._read(self.session_dir / "companions.md")
        if not text:
            return {}
        return {"companions": []}

    # ── NPCs ──────────────────────────────────────────────────────────────
    # CUSTOMIZE: Parse encountered NPCs with disposition, location, quest ties.
    def parse_npcs(self) -> list[dict]:
        text = self._read(self.session_dir / "npcs.md")
        if not text:
            return []
        return []

    # ── Quests ────────────────────────────────────────────────────────────
    # CUSTOMIZE: Parse active and completed quests.
    def parse_quests(self) -> dict:
        text = self._read(self.session_dir / "quests.md")
        if not text:
            return {"active": [], "completed": []}
        return {"active": [], "completed": []}

    # ── Log ───────────────────────────────────────────────────────────────
    # CUSTOMIZE: Parse session log entries (turn-by-turn events).
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

    # ── Full parse ────────────────────────────────────────────────────────
    # CUSTOMIZE: Update this to call all your parse methods.
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


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def bar(current: int, maximum: int, width: int = 20, fill_color: str = "green",
        empty_color: str = "grey37", label: str = "") -> Text:
    """Render a progress bar as Rich Text.

    Use for any bounded numeric resource: HP, MP, stamina, fuel, morale, etc.
    Color by threshold: green > 50%, yellow > 25%, red <= 25%.
    """
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


def threat_bar(pct: int, width: int = 30, label: str = "THREAT") -> Text:
    """Render a game-wide threat/progress percentage bar.

    Color shifts with severity: green (0-25%) -> yellow (26-50%) ->
    orange (51-75%) -> red (76-100%).
    """
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
    t.append(f"{label} ", style="bold magenta")
    t.append("█" * filled, style=color)
    t.append("░" * empty, style="grey23")
    t.append(f" {pct}%", style=f"bold {color}")
    return t


# Disposition colors for NPC attitudes / relationship levels.
# CUSTOMIZE: Rename levels to match your game's system.
DISPOSITION_COLORS = {
    "hostile": "red",
    "wary": "dark_orange",
    "neutral": "yellow",
    "friendly": "green",
    "devoted": "bright_magenta",
    "unknown": "grey50",
}

# Status severity colors for regions, systems, threat levels.
# CUSTOMIZE: Rename levels to match your game's system.
STATUS_COLORS = {
    "safe": "green", "stable": "green", "intact": "green",
    "caution": "yellow", "damaged": "yellow", "declining": "yellow",
    "danger": "dark_orange", "critical": "dark_orange",
    "lost": "bright_red", "destroyed": "bright_red", "catastrophic": "bright_red",
}


# ═══════════════════════════════════════════════════════════════════════════════
# PANEL WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════
#
# Each tab in the TUI corresponds to one panel widget. Panels inherit from
# textual.widgets.Static and override render() to return a rich.console.Group.
#
# CUSTOMIZATION: Replace the render() methods with your game's specific display
# logic. Add new panel classes for game-specific tabs (Factions, Crafting, etc).
# ═══════════════════════════════════════════════════════════════════════════════

class CharacterPanel(Static):
    """Displays player character info: name, class, resource bars, stats."""

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
        title.append(f"  {p.get('name', '?')}  ", style="bold white on dark_blue")
        title.append(f"  {p.get('class', '?')}  ", style="italic cyan")
        parts.append(title)
        parts.append(Text())

        # Resource bars — CUSTOMIZE: add bars for your game's resources
        stats = p.get("stats", {})
        hp = stats.get("HP", {})
        if hp:
            hp_cur, hp_max = hp.get("current", 0), hp.get("base", 100)
            hp_color = "green" if hp_cur > hp_max * 0.5 else ("yellow" if hp_cur > hp_max * 0.25 else "red")
            parts.append(bar(hp_cur, hp_max, 25, hp_color, label="HP"))

        mp = stats.get("MP", {})
        if mp:
            parts.append(bar(mp.get("current", 0), mp.get("base", 50), 25, "dodger_blue1", label="MP"))

        parts.append(Text())

        # Stat line — CUSTOMIZE: show your game's attributes
        stat_line = Text()
        for stat_name in ["STR", "INT", "AGI", "DEX", "WIS", "CHA"]:
            s = stats.get(stat_name, {})
            if s:
                val = s.get("current", 0)
                mod = (val - 10) // 2
                sign = "+" if mod >= 0 else ""
                stat_line.append(f"  {stat_name} ", style="bold")
                stat_line.append(f"{val}", style="bold cyan")
                stat_line.append(f" ({sign}{mod})  ", style="dim")
        if stat_line.plain:
            parts.append(stat_line)
            parts.append(Text())

        # Turn counter
        turn_line = Text()
        turn_line.append("  Turn: ", style="bold")
        turn_line.append(f"{p.get('turns', 0)}", style="bold yellow")
        parts.append(turn_line)

        return Group(*parts)


class WorldPanel(Static):
    """Displays global game state: threat meter, region statuses."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        w = self.data.get("world", {})
        if not w:
            return Group(Text("No world data found.", style="dim"))

        parts = []

        # Threat/corruption bar — CUSTOMIZE: label and source field
        pct = w.get("threat_pct", 0)
        parts.append(threat_bar(pct))
        parts.append(Text())

        return Group(*parts)


class LocationPanel(Static):
    """Displays current location: name, description, exits, POI."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        loc = self.data.get("location", {})
        if not loc:
            return Group(Text("No location data found.", style="dim"))

        parts = []

        header = Text()
        header.append(f"  {loc.get('name', '?')}", style="bold bright_green")
        parts.append(header)
        parts.append(Text())

        exits = loc.get("exits", [])
        if exits:
            parts.append(Text("  Exits:", style="bold"))
            for e in exits:
                parts.append(Text(f"    -> {e}", style="cyan"))
            parts.append(Text())

        return Group(*parts)


class InventoryPanel(Static):
    """Displays inventory: currency, items, slot usage."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        inv = self.data.get("inventory", {})
        if not inv:
            return Group(Text("No inventory data found.", style="dim"))

        parts = []
        parts.append(Text(f"  Currency: {inv.get('currency', 0)}", style="bold yellow"))
        # CUSTOMIZE: Add item tables for your game's categories
        return Group(*parts)


class CompanionsPanel(Static):
    """Displays party members with resource bars, abilities, status."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        comp = self.data.get("companions", {})
        companions = comp.get("companions", []) if isinstance(comp, dict) else []
        if not companions:
            return Group(Text("No companions yet.", style="dim italic"))

        parts = []
        # CUSTOMIZE: Render each companion with bars and status
        for c in companions:
            parts.append(Text(f"  {c.get('name', '?')}", style="bold bright_yellow"))
        return Group(*parts)


class QuestsPanel(Static):
    """Displays active and completed quests."""

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
        parts.append(Text("  ACTIVE QUESTS", style="bold bright_yellow underline"))
        parts.append(Text())
        if active:
            for q in active:
                parts.append(Text(f"  > {q.get('title', '?')}", style="bold"))
                if q.get("objective"):
                    parts.append(Text(f"    Objective: {q['objective']}", style="white"))
                parts.append(Text())
        else:
            parts.append(Text("    No active quests.", style="dim italic"))
            parts.append(Text())

        # Completed quests
        completed = quests.get("completed", [])
        parts.append(Text("  COMPLETED QUESTS", style="bold green underline"))
        parts.append(Text())
        if completed:
            for q in completed:
                parts.append(Text(f"  [done] {q.get('title', '?')}", style="bold green"))
                parts.append(Text())
        else:
            parts.append(Text("    No completed quests.", style="dim italic"))

        return Group(*parts)


class NPCPanel(Static):
    """Displays encountered NPCs with disposition and location."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        npcs = self.data.get("npcs", [])
        if not npcs:
            return Group(Text("No NPC data found.", style="dim"))

        parts = []
        for npc in npcs:
            parts.append(Text(f"  {npc.get('name', '?')}", style="bold"))
            disp = npc.get("disposition", "unknown").lower()
            dc = DISPOSITION_COLORS.get(disp, "white")
            parts.append(Text(f"    Disposition: {npc.get('disposition', '?')}", style=f"bold {dc}"))
            parts.append(Text(f"    Location: {npc.get('location', '?')}", style="dim"))
            parts.append(Text())

        return Group(*parts)


class LogPanel(Static):
    """Displays session log entries, most recent first."""

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
            header.append(f"-- {entry.get('title', '?')}", style="bold")
            parts.append(header)
            parts.append(Text(f"  {entry.get('text', '')}", style="italic dim"))
            parts.append(Text())

        return Group(*parts)


class SettingsPanel(Static):
    """Displays current game configuration."""

    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def render(self) -> Group:
        settings = self.data.get("settings", {})
        if not settings:
            return Group(Text("No settings found.", style="dim"))

        parts = []
        # CUSTOMIZE: Display your game's settings structure
        game = settings.get("game", {})
        if game:
            parts.append(Text(f"  {game.get('title', 'Unknown Game')}", style="bold bright_cyan"))
            parts.append(Text(f"  Version: {game.get('version', '?')}", style="dim"))
            parts.append(Text())

        diff = settings.get("difficulty", {})
        if diff:
            mode = diff.get("mode", "normal")
            mode_colors = {"easy": "green", "normal": "yellow", "hard": "dark_orange", "nightmare": "red"}
            parts.append(Text("  Difficulty", style="bold underline"))
            parts.append(Text(f"    Mode: ", style="dim") + Text(mode.upper(), style=f"bold {mode_colors.get(mode, 'white')}"))
            parts.append(Text())

        return Group(*parts)


class ToolPanel(Static):
    """Interactive tool runner (dice roller, etc).

    CUSTOMIZE: Adapt the tool path and expression parsing for your game's tools.
    """

    def __init__(self, game_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.game_dir = game_dir

    def compose(self) -> ComposeResult:
        yield Static(Text("  Tool Runner", style="bold bright_yellow underline"), id="tool-title")
        yield Static(Text("  Type a command and press Enter", style="dim"), id="tool-help")
        yield Static(Text("  Examples: d20, 2d6+3, d20 --advantage", style="dim"), id="tool-examples")
        yield Input(placeholder="d20+5", id="tool-input")
        yield Static("", id="tool-result")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
#
# Layout modes:
#   --terminal true  (default): Split-screen with PTY terminal on the left
#                                and tabbed game panels on the right.
#   --terminal false:           Full-width tabbed game panels, no terminal.
#
# The terminal panel is useful when the player wants to interact with their AI
# agent (e.g. Claude Code running in the shell) while viewing game state. When
# running the TUI purely as a read-only dashboard, --terminal false gives more
# screen real estate to the game panels.
# ═══════════════════════════════════════════════════════════════════════════════

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

#tool-input {
    margin: 1 2;
    width: 40;
}

#tool-result {
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


class GameTUI(App):
    """Generic Agentic Game Session Viewer.

    CUSTOMIZE:
    - TITLE / SUB_TITLE: Set your game's name.
    - BINDINGS: Add or remove tab shortcuts to match your tab set.
    - compose(): Add or remove TabPanes to match your game's data.
    - _make_top_bar(): Choose the 4-6 most critical at-a-glance values.
    """

    TITLE = "Agentic Game Session Viewer"
    SUB_TITLE = "Game Title Here"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "focus_tools", "Tools"),
        Binding("t", "focus_terminal", "Terminal"),
        Binding("1", "tab_1", "Tab 1", show=False),
        Binding("2", "tab_2", "Tab 2", show=False),
        Binding("3", "tab_3", "Tab 3", show=False),
        Binding("4", "tab_4", "Tab 4", show=False),
        Binding("5", "tab_5", "Tab 5", show=False),
        Binding("6", "tab_6", "Tab 6", show=False),
        Binding("7", "tab_7", "Tab 7", show=False),
        Binding("8", "tab_8", "Tab 8", show=False),
    ]

    def __init__(self, game_dir: str, with_terminal: bool = True, auto_refresh: float = 5.0):
        super().__init__()
        self.game_dir = game_dir
        self.with_terminal = with_terminal
        self.auto_refresh_interval = auto_refresh
        self.parser = SessionParser(game_dir)
        self.session_data = {}
        # Dynamic CSS based on terminal mode
        self.CSS = make_css(with_terminal)

    def compose(self) -> ComposeResult:
        self.session_data = self.parser.parse_all()
        player = self.session_data.get("player", {})
        world = self.session_data.get("world", {})

        # Top status bar — always visible regardless of active tab
        yield Static(self._make_top_bar(player, world), id="top-bar")
        yield Header()

        # CUSTOMIZE: Add or remove TabPanes below to match your game.
        # The tab IDs must match the action_tab_N methods.
        tabs_content = TabbedContent(
            "Character", "World", "Location", "Inventory",
            "Quests", "NPCs", "Companions", "Log", "Tools", "Settings",
        )

        if self.with_terminal:
            # Split layout: terminal on left, tabs on right
            with Horizontal(id="split-view"):
                with Vertical(id="terminal-panel"):
                    yield PtyTerminal(id="game-terminal")
                with Vertical(id="main-content"):
                    with tabs_content:
                        yield from self._compose_tab_panes()
        else:
            # Full-width layout: tabs only
            with Vertical(id="main-content"):
                with tabs_content:
                    yield from self._compose_tab_panes()

        yield Footer()

    def _compose_tab_panes(self) -> ComposeResult:
        """Yield all tab panes. CUSTOMIZE: add/remove/rename tabs here."""
        with TabPane("Character", id="tab-1"):
            with VerticalScroll():
                yield CharacterPanel(self.session_data)

        with TabPane("World", id="tab-2"):
            with VerticalScroll():
                yield WorldPanel(self.session_data)

        with TabPane("Location", id="tab-3"):
            with VerticalScroll():
                yield LocationPanel(self.session_data)

        with TabPane("Inventory", id="tab-4"):
            with VerticalScroll():
                yield InventoryPanel(self.session_data)

        with TabPane("Quests", id="tab-5"):
            with VerticalScroll():
                yield QuestsPanel(self.session_data)

        with TabPane("NPCs", id="tab-6"):
            with VerticalScroll():
                yield NPCPanel(self.session_data)

        with TabPane("Companions", id="tab-7"):
            with VerticalScroll():
                yield CompanionsPanel(self.session_data)

        with TabPane("Log", id="tab-8"):
            with VerticalScroll():
                yield LogPanel(self.session_data)

        with TabPane("Tools", id="tab-tools"):
            with VerticalScroll():
                yield ToolPanel(self.game_dir)

        with TabPane("Settings", id="tab-settings"):
            with VerticalScroll():
                yield SettingsPanel(self.session_data)

    def _make_top_bar(self, player: dict, world: dict) -> Text:
        """Build the persistent top status bar.

        CUSTOMIZE: Choose the 4-6 most critical at-a-glance values for your game.
        This bar is visible regardless of which tab is active.
        """
        t = Text()
        name = player.get("name", "No Active Session")
        cls = player.get("class", "")

        t.append("  ", style="bold")
        t.append(name, style="bold white")
        if cls:
            t.append(f" ({cls})", style="dim cyan")

        stats = player.get("stats", {})
        hp = stats.get("HP", {})
        if hp:
            t.append("   HP:", style="bold")
            t.append(f"{hp.get('current', '?')}/{hp.get('base', '?')}", style="green")

        mp = stats.get("MP", {})
        if mp:
            t.append("  MP:", style="bold")
            t.append(f"{mp.get('current', '?')}/{mp.get('base', '?')}", style="dodger_blue1")

        threat = world.get("threat_pct", 0)
        tc = "green" if threat <= 25 else "yellow" if threat <= 50 else "dark_orange" if threat <= 75 else "red"
        t.append("   THREAT:", style="bold")
        t.append(f"{threat}%", style=f"bold {tc}")

        turn = player.get("turns", 0)
        t.append(f"   Turn:{turn}", style="dim")

        return t

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        """Start the terminal process and auto-refresh timer after the app is mounted."""
        if self.with_terminal:
            try:
                terminal = self.query_one("#game-terminal", PtyTerminal)
                terminal.start()
            except NoMatches:
                pass
        # Start auto-refresh timer if enabled
        if self.auto_refresh_interval > 0:
            self.set_interval(self.auto_refresh_interval, self._periodic_refresh)

    def on_unmount(self) -> None:
        """Clean up the terminal process on exit."""
        if self.with_terminal:
            try:
                terminal = self.query_one("#game-terminal", PtyTerminal)
                terminal.cleanup()
            except NoMatches:
                pass

    # ── Actions ───────────────────────────────────────────────────────────

    def action_focus_terminal(self) -> None:
        """Focus the integrated terminal (only if enabled)."""
        if not self.with_terminal:
            self.notify("Terminal is disabled. Restart with --terminal true to enable.")
            return
        try:
            self.query_one("#game-terminal", PtyTerminal).focus()
        except NoMatches:
            pass

    def action_focus_tools(self) -> None:
        """Focus the tool input widget."""
        try:
            self.query_one("#tool-input", Input).focus()
        except NoMatches:
            pass

    def action_refresh(self) -> None:
        """Re-read all session files and update every panel widget.

        IMPORTANT: Re-parsing alone is not enough. Each panel widget stores its
        own reference to the data dict. The refresh handler must:
        1. Re-parse all session data.
        2. Update each panel widget's .data attribute to point to the new data.
        3. Call .refresh(layout=True) on each widget to trigger a re-render
           AND recalculate layout (so VerticalScroll parents resize correctly
           when content grows/shrinks, e.g. new log entries).
        4. Update the top status bar separately.
        """
        self.session_data = self.parser.parse_all()
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
        """Silent auto-refresh — same as action_refresh but without the notification toast.

        CUSTOMIZE: Update the widget query selector to match your game's panel classes.
        """
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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle tool input submission."""
        if event.input.id == "tool-input":
            expr = event.value.strip()
            if not expr:
                return
            # CUSTOMIZE: Change the tool path to match your game's tools
            tool_path = Path(self.game_dir) / "tools" / "dice.py"
            venv_python = Path(self.game_dir) / ".venv" / "bin" / "python"
            python_cmd = str(venv_python) if venv_python.exists() else "python3"
            try:
                args = [python_cmd, str(tool_path)] + expr.split()
                result = subprocess.run(args, capture_output=True, text=True, timeout=5)
                output = result.stdout.strip() or result.stderr.strip() or "No output"
            except FileNotFoundError:
                output = f"Tool not found: {tool_path}"
            except Exception as e:
                output = f"Error: {e}"

            try:
                result_widget = self.query_one("#tool-result", Static)
                result_text = Text()
                result_text.append(f"\n  {output}\n", style="bold bright_yellow")
                result_widget.update(result_text)
            except NoMatches:
                pass
            event.input.value = ""

    # ── Tab switching ─────────────────────────────────────────────────────

    def _switch_tab(self, tab_id: str) -> None:
        try:
            tc = self.query_one(TabbedContent)
            tc.active = tab_id
        except NoMatches:
            pass

    def action_tab_1(self) -> None:
        self._switch_tab("tab-1")
    def action_tab_2(self) -> None:
        self._switch_tab("tab-2")
    def action_tab_3(self) -> None:
        self._switch_tab("tab-3")
    def action_tab_4(self) -> None:
        self._switch_tab("tab-4")
    def action_tab_5(self) -> None:
        self._switch_tab("tab-5")
    def action_tab_6(self) -> None:
        self._switch_tab("tab-6")
    def action_tab_7(self) -> None:
        self._switch_tab("tab-7")
    def action_tab_8(self) -> None:
        self._switch_tab("tab-8")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Agentic Game TUI Viewer — a Textual-based dashboard for agentic game sessions.",
        epilog="Launch from the game root: .venv/bin/python tui/tui_viewer.py . --terminal true",
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
        help="Enable or disable the integrated PTY terminal panel (default: true). "
             "When true, a live shell is embedded on the left half of the screen. "
             "When false, game panels take the full width.",
    )
    parser.add_argument(
        "--refresh",
        type=float,
        default=5.0,
        help="Auto-refresh interval in seconds (default: 5). Set to 0 to disable auto-refresh.",
    )
    args = parser.parse_args()

    # Resolve game directory
    if args.game_dir:
        game_dir = args.game_dir
    else:
        cwd = Path(os.getcwd())
        if cwd.name == "tui" and (cwd.parent / "session").exists():
            game_dir = str(cwd.parent)
        elif (cwd / "session").exists():
            game_dir = str(cwd)
        else:
            game_dir = str(Path(__file__).resolve().parent.parent)

    # Verify session directory exists
    session_path = Path(game_dir) / "session"
    if not session_path.exists():
        print(f"Warning: No session/ directory found in {game_dir}")
        print("The TUI will show empty panels. Start a game first to populate session data.")

    with_terminal = args.terminal == "true"
    app = GameTUI(game_dir, with_terminal=with_terminal, auto_refresh=args.refresh)
    app.run()


if __name__ == "__main__":
    main()
