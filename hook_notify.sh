#!/bin/bash
# tmux-focused notification hook
# Usage from tmux hooks (recommended):
#   set-hook -g some-event "run-shell '/path/to/hook_notify.sh #{session_name}'"

SESSION_NAME="$1"

# If not provided, attempt to resolve from current client (best-effort)
if [ -z "$SESSION_NAME" ]; then
  SESSION_NAME=$(tmux display-message -p '#{session_name}' 2>/dev/null)
fi

if [ -n "$SESSION_NAME" ]; then
  echo "notification:" > "/tmp/tmux_hook_${SESSION_NAME}.txt"
  echo "[$(date)] Notification hook called, tmux session: $SESSION_NAME" >> /tmp/hook_debug.log
else
  # Fallback to generic file
  echo "notification:" > /tmp/tmux_hook.txt
  echo "[$(date)] Notification hook called, generic (no session)" >> /tmp/hook_debug.log
fi
