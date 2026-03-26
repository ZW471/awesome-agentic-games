"""
Signal Lost — TUI Menu Screens

StartScreen, NewGameScreen, LoadGameScreen, ProviderScreen, SaveScreen.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Input, Label, OptionList, Select, Static
from textual.widgets.option_list import Option
from rich.text import Text

# ---------------------------------------------------------------------------
# Paths — resolved relative to this file
# ---------------------------------------------------------------------------

_COMPILED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GAME_ROOT = os.path.abspath(os.path.join(_COMPILED_DIR, ".."))
DEFAULT_SESSION_DIR = os.path.join(GAME_ROOT, "session")
SAVES_DIR = os.path.join(GAME_ROOT, "saves")
SETTINGS_DIR = os.path.join(GAME_ROOT, "settings")
ENV_PATH = os.path.join(GAME_ROOT, ".env")
PROVIDER_CONFIG_PATH = os.path.join(SETTINGS_DIR, "provider.json")

# ---------------------------------------------------------------------------
# .env helpers
# ---------------------------------------------------------------------------

def _load_env(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    if not os.path.isfile(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def _save_env(path: str, key: str, value: str) -> None:
    env = _load_env(path)
    env[key] = value
    with open(path, "w", encoding="utf-8") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")


def _load_provider_config() -> dict:
    try:
        with open(PROVIDER_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_provider_config(provider: str, model: str) -> None:
    os.makedirs(os.path.dirname(PROVIDER_CONFIG_PATH), exist_ok=True)
    with open(PROVIDER_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"provider": provider, "model": model}, f, indent=2)


# ---------------------------------------------------------------------------
# Default models per provider
# ---------------------------------------------------------------------------

DEFAULT_MODELS = {
    "openai": "gpt-5.4",
    "anthropic": "claude-sonnet-4-20250514",
}

ENV_KEY_NAMES = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


# =============================================================================
# START SCREEN
# =============================================================================

START_CSS = """
StartScreen {
    align: center middle;
    background: #0a0a0f;
}

#start-container {
    width: 60;
    height: auto;
    padding: 2 4;
    border: heavy #ff00ff;
    background: #0d0d1a;
}

#title-art {
    text-align: center;
    color: #ff00ff;
    text-style: bold;
    margin-bottom: 1;
}

#subtitle {
    text-align: center;
    color: #00ffff;
    margin-bottom: 2;
}

.menu-btn {
    width: 100%;
    margin: 1 0;
}

#btn-new {
    background: #1a0033;
    color: #ff00ff;
}

#btn-load {
    background: #001a33;
    color: #00bfff;
}

#btn-resume {
    background: #0d1a00;
    color: #00ff41;
}

#btn-quit {
    background: #1a0000;
    color: #ff3333;
}
"""


class StartScreen(Screen):
    DEFAULT_CSS = START_CSS

    BINDINGS = [
        Binding("q", "quit_app", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="start-container"):
                yield Static(
                    "███████╗██╗ ██████╗ ███╗   ██╗ █████╗ ██╗\n"
                    "██╔════╝██║██╔════╝ ████╗  ██║██╔══██╗██║\n"
                    "███████╗██║██║  ███╗██╔██╗ ██║███████║██║\n"
                    "╚════██║██║██║   ██║██║╚██╗██║██╔══██║██║\n"
                    "███████║██║╚██████╔╝██║ ╚████║██║  ██║███████╗\n"
                    "╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝\n"
                    "      ██╗      ██████╗ ███████╗████████╗\n"
                    "      ██║     ██╔═══██╗██╔════╝╚══██╔══╝\n"
                    "      ██║     ██║   ██║███████╗   ██║\n"
                    "      ██║     ██║   ██║╚════██║   ██║\n"
                    "      ███████╗╚██████╔╝███████║   ██║\n"
                    "      ╚══════╝ ╚═════╝ ╚══════╝   ╚═╝",
                    id="title-art",
                )
                yield Static("信 号 遗 失", id="subtitle")
                yield Button("NEW GAME", id="btn-new", classes="menu-btn")
                yield Button("LOAD GAME", id="btn-load", classes="menu-btn")
                yield Button("RESUME", id="btn-resume", classes="menu-btn")
                yield Button("QUIT", id="btn-quit", classes="menu-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new":
            self.app.push_screen(NewGameScreen())
        elif event.button.id == "btn-load":
            self.app.push_screen(LoadGameScreen())
        elif event.button.id == "btn-resume":
            player_path = os.path.join(DEFAULT_SESSION_DIR, "player.json")
            if os.path.isfile(player_path):
                self.app.push_screen(ProviderScreen(mode="resume"))
            else:
                self.notify("No active session found. Start a new game or load a save.", severity="error", timeout=4)
        elif event.button.id == "btn-quit":
            self.app.exit()

    def action_quit_app(self) -> None:
        self.app.exit()


# =============================================================================
# NEW GAME SCREEN
# =============================================================================

NEW_GAME_CSS = """
NewGameScreen {
    align: center middle;
    background: #0a0a0f;
}

#newgame-container {
    width: 70;
    height: auto;
    max-height: 90%;
    padding: 2 4;
    border: heavy #00ffff;
    background: #0d0d1a;
}

#newgame-title {
    text-align: center;
    color: #00ffff;
    text-style: bold;
    margin-bottom: 1;
}

.form-label {
    color: #ff00ff;
    margin-top: 1;
}

.form-desc {
    color: #666688;
    margin-bottom: 0;
}

#btn-begin {
    margin-top: 2;
    width: 100%;
    background: #1a0033;
    color: #ff00ff;
}

#btn-newgame-back {
    margin-top: 1;
    width: 100%;
    background: #1a0000;
    color: #ff3333;
}
"""


class NewGameScreen(Screen):
    DEFAULT_CSS = NEW_GAME_CSS

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Center():
            with VerticalScroll(id="newgame-container"):
                yield Static("CHARACTER CREATION / 角色创建", id="newgame-title")

                yield Label("Name / 姓名", classes="form-label")
                yield Input(placeholder="What is your name?", id="input-name")

                yield Label("Alias / 化名", classes="form-label")
                yield Input(placeholder="What do they call you on the street?", id="input-alias")

                yield Label("Background / 背景", classes="form-label")
                yield Select(
                    [
                        ("Street Runner / 街头行者 — You know the alleys and back doors", "street_runner"),
                        ("Corporate Exile / 企业流亡者 — You fled from the towers", "corporate_exile"),
                        ("Netrunner / 网行者 — You lived in data once", "netrunner"),
                    ],
                    value="street_runner",
                    id="select-background",
                )

                yield Label("Difficulty / 难度", classes="form-label")
                yield Select(
                    [
                        ("Paranoid / 偏执 — Merciful (Integrity: 4, hints)", "paranoid"),
                        ("Cautious / 谨慎 — Careful (Integrity: 3, subtle hints)", "cautious"),
                        ("Standard / 标准 — No safety net (Integrity: 3)", "standard"),
                        ("Reckless / 鲁莽 — Already dead (Integrity: 2)", "reckless"),
                    ],
                    value="standard",
                    id="select-difficulty",
                )

                yield Label("Language / 语言", classes="form-label")
                yield Select(
                    [
                        ("English", "en"),
                        ("中文", "zh"),
                    ],
                    value="en",
                    id="select-language",
                )

                yield Button("BEGIN / 开始", id="btn-begin")
                yield Button("BACK", id="btn-newgame-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-begin":
            name = self.query_one("#input-name", Input).value.strip()
            alias = self.query_one("#input-alias", Input).value.strip()
            if not name:
                self.notify("Name cannot be empty.", severity="error", timeout=3)
                return
            if not alias:
                alias = name

            self.app.new_game_config = {
                "name": name,
                "alias": alias,
                "background": self.query_one("#select-background", Select).value,
                "difficulty": self.query_one("#select-difficulty", Select).value,
                "language": self.query_one("#select-language", Select).value,
            }
            self.app.push_screen(ProviderScreen(mode="new_game"))
        elif event.button.id == "btn-newgame-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        self.app.pop_screen()


# =============================================================================
# LOAD GAME SCREEN
# =============================================================================

LOAD_GAME_CSS = """
LoadGameScreen {
    align: center middle;
    background: #0a0a0f;
}

#load-container {
    width: 70;
    height: auto;
    max-height: 80%;
    padding: 2 4;
    border: heavy #00bfff;
    background: #0d0d1a;
}

#load-title {
    text-align: center;
    color: #00bfff;
    text-style: bold;
    margin-bottom: 1;
}

#save-list {
    height: auto;
    max-height: 20;
    margin: 1 0;
}

#no-saves {
    text-align: center;
    color: #666688;
    margin: 2 0;
}

#btn-load-back {
    margin-top: 1;
    width: 100%;
    background: #1a0000;
    color: #ff3333;
}
"""


def _read_json_safe(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


class LoadGameScreen(Screen):
    DEFAULT_CSS = LOAD_GAME_CSS

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._save_dirs: list[str] = []

    def compose(self) -> ComposeResult:
        saves: list[tuple[str, str]] = []  # (display_text, save_dir_path)

        if os.path.isdir(SAVES_DIR):
            for entry in sorted(os.listdir(SAVES_DIR)):
                save_path = os.path.join(SAVES_DIR, entry)
                if not os.path.isdir(save_path):
                    continue
                player = _read_json_safe(os.path.join(save_path, "player.json"))
                world = _read_json_safe(os.path.join(save_path, "world_state.json"))
                traces = _read_json_safe(os.path.join(save_path, "traces.json"))

                alias = player.get("alias", player.get("name", "???"))
                bg = player.get("background", "?")
                turn = player.get("turn", "?")
                integrity = player.get("integrity", {})
                int_str = f"{integrity.get('current', '?')}/{integrity.get('max', '?')}"
                alert = world.get("nexus_alert", {})
                alert_val = alert.get("current", alert) if isinstance(alert, dict) else alert
                total_traces = traces.get("total_discovered", "?")

                line = f"{entry}  |  {alias} ({bg})  |  Turn {turn}  |  HP {int_str}  |  Alert {alert_val}%  |  Traces {total_traces}"
                saves.append((line, save_path))

        with Center():
            with Vertical(id="load-container"):
                yield Static("LOAD GAME / 读取存档", id="load-title")
                if saves:
                    options = []
                    for display, path in saves:
                        options.append(Option(display, id=path))
                        self._save_dirs.append(path)
                    yield OptionList(*options, id="save-list")
                else:
                    yield Static("No saves found. Start a new game first.", id="no-saves")
                yield Button("BACK", id="btn-load-back")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        idx = event.option_index
        if 0 <= idx < len(self._save_dirs):
            self.app.load_save_path = self._save_dirs[idx]
            self.app.push_screen(ProviderScreen(mode="load_game"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-load-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        self.app.pop_screen()


# =============================================================================
# PROVIDER SCREEN
# =============================================================================

PROVIDER_CSS = """
ProviderScreen {
    align: center middle;
    background: #0a0a0f;
}

#provider-container {
    width: 65;
    height: auto;
    padding: 2 4;
    border: heavy #ffbf00;
    background: #0d0d1a;
}

#provider-title {
    text-align: center;
    color: #ffbf00;
    text-style: bold;
    margin-bottom: 1;
}

.prov-label {
    color: #ff00ff;
    margin-top: 1;
}

.prov-hint {
    color: #444466;
}

#btn-launch {
    margin-top: 2;
    width: 100%;
    background: #1a0033;
    color: #ff00ff;
}

#btn-provider-back {
    margin-top: 1;
    width: 100%;
    background: #1a0000;
    color: #ff3333;
}

#api-key-row {
    height: auto;
}
"""


class ProviderScreen(Screen):
    DEFAULT_CSS = PROVIDER_CSS

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(self, mode: str, **kwargs):
        super().__init__(**kwargs)
        self.mode = mode

    def compose(self) -> ComposeResult:
        cfg = _load_provider_config()
        saved_provider = cfg.get("provider", "openai")
        saved_model = cfg.get("model", DEFAULT_MODELS.get(saved_provider, "gpt-5.4"))

        env = _load_env(ENV_PATH)
        env_key_name = ENV_KEY_NAMES.get(saved_provider, "")
        has_key = bool(env.get(env_key_name, "") or os.environ.get(env_key_name, ""))

        with Center():
            with Vertical(id="provider-container"):
                yield Static("LLM CONFIGURATION", id="provider-title")

                yield Label("Provider", classes="prov-label")
                yield Select(
                    [
                        ("OpenAI", "openai"),
                        ("Anthropic", "anthropic"),
                    ],
                    value=saved_provider,
                    id="select-provider",
                )

                yield Label("Model", classes="prov-label")
                yield Input(value=saved_model, placeholder="Model name", id="input-model")

                yield Label("API Key", classes="prov-label", id="label-api-key")
                yield Static("(loaded from .env)", classes="prov-hint", id="api-key-hint")
                yield Input(
                    placeholder="Paste your API key",
                    password=True,
                    id="input-api-key",
                )

                yield Label("Temperature", classes="prov-label")
                yield Input(value="0.7", placeholder="0.0 - 1.0", id="input-temperature")

                yield Button("LAUNCH GAME / 启动游戏", id="btn-launch")
                yield Button("BACK", id="btn-provider-back")

        # Schedule post-mount visibility update
        self.set_timer(0.05, self._update_key_visibility)

    def _update_key_visibility(self) -> None:
        provider = self.query_one("#select-provider", Select).value
        env_key_name = ENV_KEY_NAMES.get(provider, "")
        env = _load_env(ENV_PATH)
        has_key = bool(env.get(env_key_name, "") or os.environ.get(env_key_name, ""))

        try:
            key_input = self.query_one("#input-api-key", Input)
            hint = self.query_one("#api-key-hint", Static)
            label = self.query_one("#label-api-key", Label)
            if has_key:
                key_input.display = False
                hint.display = True
                hint.update("(loaded from .env)")
            else:
                key_input.display = True
                hint.display = False
        except Exception:
            pass

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "select-provider":
            provider = event.value
            model_input = self.query_one("#input-model", Input)
            model_input.value = DEFAULT_MODELS.get(provider, "")
            self._update_key_visibility()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-launch":
            self._launch()
        elif event.button.id == "btn-provider-back":
            self.action_go_back()

    def _launch(self) -> None:
        provider = self.query_one("#select-provider", Select).value
        model = self.query_one("#input-model", Input).value.strip()
        api_key = self.query_one("#input-api-key", Input).value.strip()
        temperature_str = self.query_one("#input-temperature", Input).value.strip()

        if not model:
            self.notify("Model name cannot be empty.", severity="error", timeout=3)
            return

        try:
            temperature = float(temperature_str)
        except ValueError:
            self.notify("Invalid temperature value.", severity="error", timeout=3)
            return

        # Resolve API key
        env_key_name = ENV_KEY_NAMES.get(provider, "")
        env = _load_env(ENV_PATH)
        existing_key = env.get(env_key_name, "") or os.environ.get(env_key_name, "")

        if api_key:
            # User provided a new key — save to .env
            _save_env(ENV_PATH, env_key_name, api_key)
            os.environ[env_key_name] = api_key
        elif existing_key:
            os.environ[env_key_name] = existing_key
        else:
            self.notify("API key is required. Paste it above or set it in .env.", severity="error", timeout=4)
            return

        # Persist provider + model globally
        _save_provider_config(provider, model)

        # Delegate to the app
        self.app.launch_game(self.mode, provider, model, temperature)

    def action_go_back(self) -> None:
        self.app.pop_screen()


# =============================================================================
# SAVE SCREEN (modal during gameplay)
# =============================================================================

SAVE_CSS = """
SaveScreen {
    align: center middle;
}

#save-modal {
    width: 50;
    height: auto;
    padding: 2 4;
    border: heavy #00ff41;
    background: #0d0d1a;
}

#save-title {
    text-align: center;
    color: #00ff41;
    text-style: bold;
    margin-bottom: 1;
}

#btn-save-confirm {
    margin-top: 1;
    width: 100%;
    background: #0d1a00;
    color: #00ff41;
}

#btn-save-cancel {
    margin-top: 1;
    width: 100%;
    background: #1a0000;
    color: #ff3333;
}
"""


class SaveScreen(ModalScreen[str | None]):
    DEFAULT_CSS = SAVE_CSS

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, default_name: str = "save", session_dir: str = "", **kwargs):
        super().__init__(**kwargs)
        self.default_name = default_name
        self.session_dir = session_dir

    def compose(self) -> ComposeResult:
        with Vertical(id="save-modal"):
            yield Static("SAVE GAME / 保存游戏", id="save-title")
            yield Label("Save name:", classes="prov-label")
            yield Input(value=self.default_name, placeholder="Save name", id="input-save-name")
            yield Button("SAVE", id="btn-save-confirm")
            yield Button("CANCEL", id="btn-save-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save-confirm":
            self._do_save()
        elif event.button.id == "btn-save-cancel":
            self.dismiss(None)

    def _do_save(self) -> None:
        from state import save_game_to_slot

        name = self.query_one("#input-save-name", Input).value.strip()
        name = re.sub(r"[^\w\-]", "_", name)
        if not name:
            self.notify("Save name cannot be empty.", severity="error", timeout=3)
            return

        try:
            save_game_to_slot(self.session_dir, name, SAVES_DIR)
            self.dismiss(name)
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error", timeout=4)

    def action_cancel(self) -> None:
        self.dismiss(None)
