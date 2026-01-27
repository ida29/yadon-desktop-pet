# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yadon Desktop Pet is a macOS desktop pet application that monitors tmux sessions. It displays pixel-art Yadon (Slowpoke) characters that track CLI activity and show speech bubbles when panes go idle.

## Commands

```bash
# Run the application
python3 yadon_pet.py

# Install for auto-start (macOS launchd)
./install.sh

# Syntax check
python3 -m py_compile yadon_pet.py config.py process_monitor.py

# View debug logs
tail -f /tmp/yadon_debug.log
```

## Architecture

### Core Files

- **yadon_pet.py**: Main application entry point and `YadonPet` widget class. Handles window rendering, mouse events, tmux monitoring, and idle detection.
- **process_monitor.py**: `ProcessMonitor` class that watches tmux session count changes and spawns/removes YadonPet instances accordingly.
- **config.py**: All configuration constants (timings, colors, messages, thresholds).

### UI Components

- **speech_bubble.py**: Pokemon-style speech bubble widget with auto-positioning.
- **pokemon_menu.py**: Retro Pokemon Red/Blue style right-click context menu.
- **pixel_data.py**: Builds 16x16 pixel art data for different Yadon variants (normal, shiny, galarian).

### Utilities

- **utils.py**: Shared functions (`log_debug`, `run_tmux`, `get_tmux_binary`).

## Key Concepts

### Tmux Integration

The app monitors tmux via direct `tmux` CLI calls (resolved via `get_tmux_binary()`). Each YadonPet instance tracks one tmux session and displays active window/pane indices (`session window pane`).

### Idle Detection (Two-Stage)

1. **Soft threshold** (`IDLE_SOFT_THRESHOLD_SEC`): Shows gentle blue bubble notification
2. **Force threshold** (`IDLE_FORCE_THRESHOLD_SEC`): With "yaruki switch" ON, auto-sends keys to resume

### Yaruki Switch (Motivation Switch)

Right-click menu toggle that enables automatic input when idle threshold is reached (e.g., answering y/n prompts, re-running last command).

## Configuration

All tunable values are in `config.py`:
- `TMUX_CLI_NAMES`: CLI process names to monitor
- `IDLE_SOFT_THRESHOLD_SEC` / `IDLE_FORCE_THRESHOLD_SEC`: Idle detection timings
- `VARIANT_ORDER`: Color schemes for multiple Yadon instances
- `*_MESSAGES`: Various speech bubble message templates
