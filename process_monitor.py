"""Tmux session monitoring functionality for Yadon Desktop Pet"""

import os
import shutil
import subprocess
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from config import VARIANT_ORDER, MAX_YADON_COUNT, DEBUG_LOG


def _log_debug(message: str):
    try:
        with open(DEBUG_LOG, 'a') as log:
            log.write(f"[process_monitor] {message}\n")
    except Exception:
        pass


def _tmux_bin() -> str:
    """Resolve tmux binary path robustly."""
    # Try environment PATH first
    path = shutil.which('tmux')
    if path:
        return path
    # Common Homebrew paths
    for candidate in ('/opt/homebrew/bin/tmux', '/usr/local/bin/tmux', '/usr/bin/tmux'):
        if os.path.exists(candidate):
            return candidate
    # Fallback to plain name
    return 'tmux'


def _run_tmux(args):
    """Run tmux with resolved binary, return CompletedProcess or None."""
    cmd = [_tmux_bin()] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            _log_debug(f"tmux call failed: {' '.join(cmd)} | rc={result.returncode} | err={result.stderr.strip()}")
        return result
    except Exception as e:
        _log_debug(f"tmux invoke error: {e}")
        return None


class ProcessMonitor(QTimer):
    """Monitor tmux sessions and manage Yadon instances"""
    def __init__(self, initial_pets):
        super().__init__()
        self.pets = initial_pets
        self.last_count = len(initial_pets)
        self.timeout.connect(self.check_processes)
        self.setInterval(5000)  # Check every 5 seconds
    
    def check_processes(self):
        current_count = count_tmux_sessions()
        _log_debug(f"check_processes: last_count={self.last_count}, current_count={current_count}")
        current_count = min(current_count, MAX_YADON_COUNT) if current_count > 0 else 0
        
        if current_count != self.last_count:
            # Process count changed, update Yadon instances
            if current_count > self.last_count:
                # Add more Yadons
                # Prefer the screen under the cursor to place new pets visibly
                from PyQt6.QtGui import QCursor
                screen_obj = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
                screen = screen_obj.geometry()
                
                # Calculate positions for bottom-right alignment
                margin = 20  # Margin from screen edges
                spacing = 10  # Space between Yadons
                
                # Get current tmux session names
                sessions = get_tmux_sessions()
                _log_debug(f"adding pets for sessions={sessions}")
                
                for i in range(self.last_count, current_count):
                    # Import here to avoid circular import
                    from yadon_pet import YadonPet
                    import random
                    
                    session_name = sessions[i] if i < len(sessions) else None
                    # Randomly select variant with equal probability
                    variant = random.choice(VARIANT_ORDER)
                    pet = YadonPet(tmux_session=session_name, variant=variant)
                    
                    # Position in bottom-right, stacking from right to left
                    from config import WINDOW_WIDTH, WINDOW_HEIGHT
                    x_pos = screen.width() - margin - (WINDOW_WIDTH + spacing) * (len(self.pets) + 1)
                    y_pos = screen.height() - margin - WINDOW_HEIGHT
                    _log_debug(f"moving pet for session={session_name} to ({x_pos},{y_pos})")
                    pet.move(x_pos, y_pos)
                    
                    self.pets.append(pet)
                    pet.show()
            elif current_count < self.last_count:
                # Remove excess Yadons - properly clean up
                while len(self.pets) > max(current_count, 0):
                    pet = self.pets.pop()
                    # Close any open speech bubbles first
                    if hasattr(pet, 'bubble') and pet.bubble:
                        pet.bubble.close()
                    # Stop all timers
                    if hasattr(pet, 'timer'):
                        pet.timer.stop()
                    if hasattr(pet, 'action_timer'):
                        pet.action_timer.stop()
                    if hasattr(pet, 'monitor_timer'):
                        pet.monitor_timer.stop()
                    if hasattr(pet, 'hook_timer'):
                        pet.hook_timer.stop()
                    # Close the widget
                    pet.close()
                    pet.deleteLater()  # Ensure proper cleanup
            
            self.last_count = current_count

def count_tmux_sessions():
    """Count the number of tmux sessions"""
    try:
        result = _run_tmux(['list-sessions', '-F', '#{session_name}'])
        if result is None or result.returncode != 0:
            return 0
        output = result.stdout.strip()
        if not output:
            return 0
        sessions = [line.strip() for line in output.split('\n') if line.strip()]
        return len(sessions)
    except Exception:
        return 0


def get_tmux_sessions():
    """Get list of tmux session names"""
    try:
        result = _run_tmux(['list-sessions', '-F', '#{session_name}'])
        if result is None or result.returncode != 0:
            return []
        sessions = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        return sessions
    except Exception:
        return []


def find_tmux_session():
    """Find a tmux session name (first one)"""
    try:
        sessions = get_tmux_sessions()
        return sessions[0] if sessions else None
    except Exception:
        return None
