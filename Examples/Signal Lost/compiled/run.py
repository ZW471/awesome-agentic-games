#!/usr/bin/env python3
"""
Signal Lost — Compiled Game Entry Point

Launches a full-screen Textual TUI with:
  - Start menu (New Game / Load Game / Resume)
  - LLM provider + model configuration
  - Interactive game screen with chat and state panels

Usage:
    python run.py
"""

from __future__ import annotations

import os
import sys

# Add compiled dir to path
sys.path.insert(0, os.path.dirname(__file__))

from textual.app import App

from graph import compile_graph, set_llm
from state import (
    copy_save_to_session,
    create_new_session,
    initial_state,
)
from tui.screens import (
    DEFAULT_SESSION_DIR,
    ENV_PATH,
    GAME_ROOT,
    StartScreen,
    _load_env,
)
from tui.tui_viewer import GameScreen


SETTINGS_DIR = os.path.join(GAME_ROOT, "settings")


def create_llm(provider: str, model: str, **kwargs):
    """Create an LLM instance based on provider."""
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, **kwargs)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'anthropic' or 'openai'.")


class SignalLostApp(App):
    """Main application shell — manages screen transitions."""

    TITLE = "Signal Lost / \u4fe1\u53f7\u9057\u5931"

    CSS = """
    Screen {
        background: #0a0a0f;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.new_game_config: dict | None = None
        self.load_save_path: str | None = None

    def on_mount(self) -> None:
        # Load any .env keys into the process environment
        env = _load_env(ENV_PATH)
        for k, v in env.items():
            if k not in os.environ:
                os.environ[k] = v

        self.push_screen(StartScreen())

    def launch_game(self, mode: str, provider: str, model: str, temperature: float) -> None:
        """Called by ProviderScreen to set up the LLM and switch to the game."""
        # Create LLM
        llm = create_llm(provider, model, temperature=temperature)
        set_llm(llm)

        # Prepare session directory based on mode
        if mode == "new_game":
            cfg = self.new_game_config or {}
            # Update language in custom.json
            self._update_language_setting(cfg.get("language", "en"))
            # Update difficulty in custom.json
            self._update_difficulty_setting(cfg.get("difficulty", "standard"))
            create_new_session(
                session_dir=DEFAULT_SESSION_DIR,
                name=cfg.get("name", "Unknown"),
                alias=cfg.get("alias", "Unknown"),
                background=cfg.get("background", "street_runner"),
                difficulty=cfg.get("difficulty", "standard"),
                language=cfg.get("language", "en"),
            )
        elif mode == "load_game" and self.load_save_path:
            copy_save_to_session(self.load_save_path, DEFAULT_SESSION_DIR)
        # mode == "resume": session dir already has files

        # Compile graph and load state
        app_graph = compile_graph()
        state = initial_state(DEFAULT_SESSION_DIR)

        # Switch to game screen (replaces entire screen stack)
        self.switch_screen(GameScreen(
            session_dir=DEFAULT_SESSION_DIR,
            graph=app_graph,
            state=state,
            mode=mode,
        ))

    def _update_language_setting(self, language: str) -> None:
        """Update language in settings/custom.json."""
        import json
        custom_path = os.path.join(SETTINGS_DIR, "custom.json")
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {}

        if "language" not in settings:
            settings["language"] = {}
        settings["language"]["display"] = language
        settings["language"]["tui"] = language

        os.makedirs(os.path.dirname(custom_path), exist_ok=True)
        with open(custom_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def _update_difficulty_setting(self, difficulty: str) -> None:
        """Update difficulty mode in settings/custom.json."""
        import json
        custom_path = os.path.join(SETTINGS_DIR, "custom.json")
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {}

        if "difficulty" not in settings:
            settings["difficulty"] = {}
        settings["difficulty"]["mode"] = difficulty

        with open(custom_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)


def main():
    app = SignalLostApp()
    app.run()


if __name__ == "__main__":
    main()
