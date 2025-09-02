#!/bin/bash
# tmux-focused stop hook
# Usage from tmux hooks (recommended):
#   set-hook -g some-event "run-shell '/path/to/hook_stop.sh #{session_name}'"

SESSION_NAME="$1"

# If not provided, attempt to resolve from current client (best-effort)
if [ -z "$SESSION_NAME" ]; then
  SESSION_NAME=$(tmux display-message -p '#{session_name}' 2>/dev/null)
fi

if [ -n "$SESSION_NAME" ]; then
  echo "stop:" > "/tmp/tmux_hook_${SESSION_NAME}.txt"
  echo "[$(date)] Stop hook called, tmux session: $SESSION_NAME" >> /tmp/hook_debug.log
else
  # Fallback to generic file
  echo "stop:" > /tmp/tmux_hook.txt
  echo "[$(date)] Stop hook called, generic (no session)" >> /tmp/hook_debug.log
fi
