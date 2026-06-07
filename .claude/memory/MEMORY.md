# Project Memory

> Layer 3: Tacit Knowledge - Patterns, preferences, lessons learned about how we work.

## Working Memory

<!-- Temporary notes for current work session - move to knowledge/ when durable -->

## Project Conventions

### Code Style
<!-- Add your project's code style conventions here -->
_Add conventions as discovered._

### Debugging Practices
<!-- Add common debugging approaches for this project -->
_Add practices as discovered._

### Memory System Conventions
- Claude Code hooks written in Python
- Context hook filters trivial prompts (<10 chars or greetings)
- Stop hook checks `stop_hook_active` flag to prevent double-writes
- All hooks must `sys.exit(0)` to never block user actions

### Communication Preferences
_Add preferences as discovered._

## Weekly Maintenance Reminder

> **Every Sunday**: Run `/memory-maintain` to synthesize learnings and update summaries.

---
*Last maintained: 2026-06-07*
