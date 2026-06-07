# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A PyQt6 desktop overlay that connects to a TikTok Live stream via the bundled `TikTokLive` library and surfaces stream events (comments, gifts, joins, follows, viewer count) as a frameless, always-on-top, draggable/resizable feed. Events can play sound effects (`pygame`) and be read aloud via Edge TTS.

## Common Commands

This project uses `uv` (see `uv.lock`, `pyproject.toml`, Python `>=3.13`). `requirements.txt` is kept for the older pip flow.

```powershell
# Install deps (preferred)
uv sync

# Run the overlay
uv run python run_overlay.py
# or after `uv sync`:
python run_overlay.py

# Run from src directly (run_overlay.py is just a thin launcher)
python src/main.py

# Smoke-test TTS in isolation
python test_tts.py
```

There is no test runner, linter, or formatter configured — `test_tts.py` is a manual smoke script, not a pytest suite.

## Architecture

Entry point is `run_overlay.py` → `src/minimal_overlay.py:main` *(note: file is missing from `src/` at the time of writing; `src/main.py` contains the actual `MainWindow` used during development — confirm which launcher is current before changing the entry path).*

### Async / Qt integration

Qt and asyncio are bridged with **`qasync`** — `QApplication` is wrapped in `qasync.QEventLoop` and `loop.run_forever()` drives both. The `TikTokLiveClient` is `await`ed inside `asyncio.create_task(...)` from Qt slots. Don't call `asyncio.run` or spawn a second loop; always schedule via `asyncio.create_task` from within the Qt thread.

### Module layout

- `src/main.py` — `MainWindow` (`DraggableMainWindow` subclass): owns the `TikTokLiveClient`, instantiates `AudioManager` and `TextToSpeechManager`, wires widget signals, and registers `@client.on(...)` handlers in `_setup_*_handler` methods.
- `src/widgets/`
  - `live_connect_widget.py` — username input + connect button + retry state machine (`STATE_DISCONNECTED/CONNECTING/CONNECTED`) with exponential-backoff retries. Emits `connection_toggled`, `retry_attempt`, `settings_toggled`, `streamer_mode_toggled`, `opacity_changed`.
  - `live_feed_widget.py` — read-only `QTextEdit` feed. `add_message(text, MessageType, say_outloud=False)` is the single ingress; styling comes from `MessageConfig` (color/size/bold) per `MessageType` (`DEFAULT`/`ALERT`/`WARNING`). When `say_outloud=True`, it forwards to its injected `TextToSpeechManager`.
  - `settings_widget.py` — UI for toggling events and editing message/event configs. Lives in a separate `DraggableMainWindow` opened from the connect bar.
- `src/event_config.py` — `EventConfig` (enabled flag, message template, optional `chime_audio_file`, `MessageType`) and `TikTokEventSettings` (one config per event: `connect`, `comments`, `gifts`, `joins`, `viewer_count`, `follows`). Templates use `str.format` with event-specific keys (e.g. `{nickname}`, `{comment}`, `{gift_name}`, `{count}`, `{unique_id}`, `{room_id}`).
- `src/audio_manager.py` — `pygame.mixer`-based SFX player. `AudioPlaybackMode` = `STOP_EARLIEST` / `SKIP` / `QUEUE`. Has its own daemon queue-processor thread guarded by `self._lock`.
- `src/tts_manager.py` — Edge TTS wrapper that synthesises to bytes, plays via `pygame.mixer.Channel`, and has its own daemon queue thread. `TTSPlaybackMode` = `QUEUE` / `OVERRIDE` / `CUT`. Voice defaults to `en-US-AriaNeural`; change via `set_voice`.

Both managers initialise `pygame.mixer` — they share the same mixer instance (the second `init()` is a no-op since `pygame.mixer.get_init()` is checked in TTS). Always call `shutdown()` on both before exit (handled in `MainWindow.closeEvent`).

### Event flow

1. `LiveConnectWidget` emits `connection_toggled(True)` → `MainWindow.start_client()` builds a `TikTokLiveClient(unique_id=...)` and calls `setup_event_handlers()`.
2. Each `_setup_<event>_handler` reads its config dynamically from `self.event_settings` inside the coroutine, so toggles take effect without re-registering handlers.
3. Handler renders the template, calls `live_feed_widget.add_message(...)`, then `play_event_audio(config)` for any configured chime. Comments additionally pass `say_outloud=True` so the TTS manager reads them.
4. `GiftEvent` handler uses `event.gift.streakable` + `event.streaking` to coalesce streaks — only emits on the **final** repeat (`repeat_count`) for streakable gifts, count=1 for non-streakable, and skips intermediate streak updates.

### TikTokLive submodule

`lib/TikTokLive` is a git submodule pinned to a fork of `isaackogan/TikTokLive` and is currently shown as `m`-modified in `git status`. The `pyproject.toml` still depends on the PyPI `TikTokLive>=6.3.1,<6.4.0`, so the imported package is the installed one — not the submodule — unless you `pip install -e lib/TikTokLive`. Check which is active before debugging library internals. `docs/events.md` is a reference catalogue of every `TikTokLive` event class.

### Visuals

- Frameless + always-on-top is set via `Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint`.
- "Streamer mode" toggles `WA_TranslucentBackground` + `WA_NoSystemBackground` on the main window via `toggle_translucent_background()`.
- Dragging is implemented in `DraggableMainWindow` (mouse press/move/release on the window itself, not a custom title bar).

## Project Memory System

**Memory operations are skill-based - Claude decides when to use them.**

**Proactive memory use:**
- Before implementing features or fixing bugs: `/memory-search` for relevant gotchas/patterns
- After resolving difficult bugs or making decisions: `/memory-write` to persist learnings
- After complex debugging or architectural discussions: `/memory-remember` to extract all learnings
- When user asks "didn't we...", "what did we decide...": `/memory-search`
- Before git commit or context compaction: `/memory-remember` to capture session learnings

**Don't wait to be asked** - if you learned something valuable, write it to memory.

**Structure:**
```
.claude/memory/
├── MEMORY.md              # Layer 3: Tacit knowledge (preferences, conventions)
├── sessions/<username>/   # Layer 2: Daily session notes (YYYY-MM-DD.md)
└── knowledge/             # Layer 1: Knowledge graph
    ├── gotchas/           # Pitfalls & lessons (facts.json + summary.md)
    ├── patterns/          # Reusable code patterns
    └── decisions/         # Architectural decisions (ADRs)
```

**Available skills:**
| Skill | When to Use |
|-------|-------------|
| `/memory-search [query]` | Search for relevant gotchas, patterns, or decisions |
| `/memory-write [category] [desc]` | Persist a gotcha, pattern, or decision |
| `/memory-remember` | Extract learnings from current conversation |
| `/memory-maintain` | Periodic maintenance (weekly recommended) |
