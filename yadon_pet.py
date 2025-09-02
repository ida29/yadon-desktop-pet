#!/usr/bin/env python3
import sys
import random
import signal
import subprocess
import os
import fcntl
import sys as _sys
import ctypes
import shutil
from PyQt6.QtWidgets import QApplication, QWidget, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QRect, QEvent
from PyQt6.QtGui import QPainter, QColor, QMouseEvent, QFont, QCursor

from config import (
    COLOR_SCHEMES, RANDOM_MESSAGES, WELCOME_MESSAGES, GOODBYE_MESSAGES,
    PIXEL_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT,
    FACE_ANIMATION_INTERVAL, RANDOM_ACTION_MIN_INTERVAL, RANDOM_ACTION_MAX_INTERVAL,
    CLAUDE_CHECK_INTERVAL, MOVEMENT_DURATION,
    TINY_MOVEMENT_RANGE, SMALL_MOVEMENT_RANGE, TINY_MOVEMENT_PROBABILITY,
    BUBBLE_DISPLAY_TIME, PID_FONT_FAMILY, PID_FONT_SIZE,
    VARIANT_ORDER, MAX_YADON_COUNT,
    TMUX_CLI_NAMES, ACTIVITY_CHECK_INTERVAL_MS, OUTPUT_IDLE_THRESHOLD_SEC,
    IDLE_HINT_MESSAGES,
    IDLE_SOFT_THRESHOLD_SEC, IDLE_FORCE_THRESHOLD_SEC,
    YARUKI_SWITCH_MODE, YARUKI_SEND_KEYS,
    FACE_ANIMATION_INTERVAL_FAST,
    FRIENDLY_TOOL_NAMES
)
from speech_bubble import SpeechBubble
from process_monitor import ProcessMonitor, count_tmux_sessions, get_tmux_sessions, find_tmux_session
# Hook handling removed (hooks are no longer used)
from pixel_data import build_pixel_data
from config import DEBUG_LOG

def _log_debug(msg: str):
    try:
        with open(DEBUG_LOG, 'a') as f:
            f.write(f"[yadon_pet] {msg}\n")
    except Exception:
        pass


def _mac_set_top_nonactivating(widget: QWidget):
    """macOS: force window to status/floating level without stealing focus."""
    try:
        if _sys.platform != 'darwin':
            return
        view_ptr = int(widget.winId())
        if not view_ptr:
            return
        objc = ctypes.cdll.LoadLibrary('/usr/lib/libobjc.A.dylib')
        cg = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')

        # selectors
        sel_registerName = objc.sel_registerName
        sel_registerName.restype = ctypes.c_void_p
        sel = lambda name: sel_registerName(name)

        objc.objc_msgSend.restype = ctypes.c_void_p
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        # NSView -> NSWindow
        window = objc.objc_msgSend(ctypes.c_void_p(view_ptr), sel(b'window'))
        if not window:
            return

        # Get a high window level; try multiple keys and pick the highest
        cg.CGWindowLevelForKey.argtypes = [ctypes.c_int]
        cg.CGWindowLevelForKey.restype = ctypes.c_int
        KEYS = {
            'floating': 3,      # kCGFloatingWindowLevelKey
            'modal': 8,         # kCGModalPanelWindowLevelKey
            'status': 18,       # kCGStatusWindowLevelKey
            'popup': 101        # kCGPopUpMenuWindowLevelKey
        }
        levels = {name: int(cg.CGWindowLevelForKey(ctypes.c_int(val))) for name, val in KEYS.items()}
        level = max(levels.values())
        _log_debug(f"macOS levels: {levels}, chosen={level}")

        # setLevel:
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
        objc.objc_msgSend(window, sel(b'setLevel:'), ctypes.c_long(int(level)))

        # Avoid focus with Qt-side flags; do not call non-existent setters.

        # Join all spaces to remain visible across desktops (optional)
        try:
            # NSWindowCollectionBehaviorCanJoinAllSpaces = 1 << 0
            behavior = ctypes.c_ulong(1)
            objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
            objc.objc_msgSend(window, sel(b'setCollectionBehavior:'), behavior)
        except Exception:
            pass

        _log_debug(f"macOS: elevated window level to {level}")
    except Exception as e:
        _log_debug(f"macOS elevate failed: {e}")

class YadonPet(QWidget):
    def __init__(self, tmux_session=None, variant='normal'):
        super().__init__()
        self.tmux_session = tmux_session if tmux_session else find_tmux_session()
        self.variant = variant
        
        # Build pixel data with variant colors
        self.pixel_data = build_pixel_data(variant)
        
        self.face_offset = 0
        self.animation_direction = 1
        self.drag_position = None
        
        self.bubble = None
        self.prefer_edges = True  # Prefer screen edges where text is less likely
        
        # tmux session detection
        self.tmux_active = False
        
        # Activity monitoring state per tmux pane
        self.pane_state = {}  # pane_id -> {last_hash, last_change_ts, soft_notified, force_done, name}
        # Motivation switch (toggle via right-click menu)
        self.yaruki_switch_mode = bool(YARUKI_SWITCH_MODE)
        # Tmux status text cache ("session window pane")
        self.tmux_status_text = self.tmux_session or 'N/A'
        
        self.init_ui()
        self.setup_animation()
        self.setup_random_actions()
        self.setup_tmux_monitor()
        self.setup_activity_monitor()
        self.setup_status_updater()
    
    def closeEvent(self, event):
        """Clean up when closing the widget"""
        # Clean up bubble
        if self.bubble:
            self.bubble.close()
            self.bubble = None
        # Stop all timers
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'action_timer'):
            self.action_timer.stop()
        if hasattr(self, 'monitor_timer'):
            self.monitor_timer.stop()
        # hook_timer removed (hooks are not used)
        super().closeEvent(event)
    
    def init_ui(self):
        self.setWindowTitle('Yadon Desktop Pet')
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # Add space for PID display
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # Do not activate or take focus when shown
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        # Always stack on top at the Qt level
        if hasattr(Qt.WidgetAttribute, 'WA_AlwaysStackOnTop'):
            self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Always-on-top, frameless, and avoid focus stealing if available
        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Window
        )
        # Some Qt builds expose WindowDoesNotAcceptFocus; use it if available
        if hasattr(Qt.WindowType, 'WindowDoesNotAcceptFocus'):
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus
        self.setWindowFlags(flags)
        
        # Don't set position here - it will be set in main()
        self.show()
        self.raise_()
        # Apply mac top-most non-activating level after show, and keep asserting
        QTimer.singleShot(0, lambda: _mac_set_top_nonactivating(self))
        self._top_keepalive = QTimer(self)
        self._top_keepalive.timeout.connect(lambda: _mac_set_top_nonactivating(self))
        self._top_keepalive.start(5000)
        
    def setup_animation(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_face)
        self.update_animation_speed()

    def update_animation_speed(self):
        interval = FACE_ANIMATION_INTERVAL_FAST if self.yaruki_switch_mode else FACE_ANIMATION_INTERVAL
        if hasattr(self, 'timer') and self.timer is not None:
            if self.timer.isActive():
                self.timer.stop()
            self.timer.start(interval)
    
    def setup_random_actions(self):
        self.action_timer = QTimer()
        self.action_timer.timeout.connect(self.random_action)
        self.action_timer.start(random.randint(RANDOM_ACTION_MIN_INTERVAL, RANDOM_ACTION_MAX_INTERVAL))
    
    def setup_tmux_monitor(self):
        """Monitor tmux sessions"""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_tmux)
        self.monitor_timer.start(CLAUDE_CHECK_INTERVAL)
        # Initial check
        self.check_tmux()

    def setup_activity_monitor(self):
        """Monitor tmux panes for CLI output activity and notify on idle."""
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self.check_cli_activity)
        self.activity_timer.start(ACTIVITY_CHECK_INTERVAL_MS)

    def setup_status_updater(self):
        """Refresh tmux status text (session window pane) periodically."""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_tmux_status)
        self.status_timer.start(1000)

    def update_tmux_status(self):
        try:
            if not self.tmux_session:
                self.tmux_status_text = 'N/A'
                return
            # Format similar to tmux left-bottom: session, window(tab), pane
            fmt = '#S #W #P'
            res = self._tmux_run(['display-message', '-p', '-t', str(self.tmux_session), fmt])
            if res and res.returncode == 0:
                txt = res.stdout.strip()
                if txt:
                    self.tmux_status_text = txt
                    self.update()
        except Exception as e:
            _log_debug(f"update_tmux_status error: {e}")
    
    def animate_face(self):
        self.face_offset += self.animation_direction
        if self.face_offset >= 1:
            self.animation_direction = -1
        elif self.face_offset <= -1:
            self.animation_direction = 1
        self.update()
    
    def paintEvent(self, event):
        if not self.pixel_data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # Clear background with transparency
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        pixel_size = PIXEL_SIZE
        
        for y in range(16):
            for x in range(16):
                color_hex = self.pixel_data[y][x]
                
                # Apply face offset only to face rows (top 10 rows)
                # Move only by 1 pixel, not 1 block
                if y < 10:
                    draw_x = x * pixel_size + self.face_offset
                else:
                    draw_x = x * pixel_size
                
                draw_y = y * pixel_size
                
                # Draw non-white pixels
                if color_hex != "#FFFFFF":
                    color = QColor(color_hex)
                    painter.fillRect(draw_x, draw_y, pixel_size, pixel_size, color)
        
        # Draw tmux status (session window pane) below Yadon with white background
        session_text = f"{self.tmux_status_text if self.tmux_status_text else (self.tmux_session or 'N/A')}"
        font = QFont(PID_FONT_FAMILY, PID_FONT_SIZE)
        font.setBold(True)
        painter.setFont(font)
        
        # Calculate text size
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(session_text)
        text_height = metrics.height()
        
        # Draw white background for PID
        bg_rect = QRect((self.width() - text_width - 4) // 2, 66, text_width + 4, text_height + 2)
        painter.fillRect(bg_rect, QColor(255, 255, 255, 200))  # Semi-transparent white
        painter.setPen(QColor(0, 0, 0))  # Black border
        painter.drawRect(bg_rect)
        
        # Draw session text
        painter.setPen(QColor(0, 0, 0))  # Black text
        painter.drawText(self.rect().adjusted(0, 68, 0, 0), Qt.AlignmentFlag.AlignHCenter, session_text)

    def _tmux_run(self, args):
        try:
            # Resolve tmux path quickly
            tmux_path = shutil.which('tmux') or '/opt/homebrew/bin/tmux'
            result = subprocess.run([tmux_path] + args, capture_output=True, text=True)
            return result
        except Exception as e:
            _log_debug(f"tmux run error: {e}")
            return None

    def _list_relevant_panes(self):
        """Return list of panes in this session that run target CLIs."""
        panes = []
        if not self.tmux_session:
            return panes
        try:
            # Get pane id, pid, current command with safe delimiter
            res = self._tmux_run(['list-panes', '-t', str(self.tmux_session), '-F', '#{pane_id}::#{pane_pid}::#{pane_current_command}'])
            if not res or res.returncode != 0:
                return panes
            lines = [l for l in res.stdout.strip().split('\n') if l.strip()]
            for line in lines:
                parts = line.split('::')
                if len(parts) != 3:
                    continue
                pane_id, pane_pid, cmd = parts
                cmd_l = cmd.lower().strip()
                relevant = any(name in cmd_l for name in TMUX_CLI_NAMES)
                if not relevant:
                    # Try to detect child processes of the pane pid containing target names
                    try:
                        ps = subprocess.run(['ps', 'ax', '-o', 'pid=,ppid=,command='], capture_output=True, text=True)
                        if ps.returncode == 0:
                            for pl in ps.stdout.splitlines():
                                try:
                                    ppid = int(pl.split(None, 2)[1])
                                    if str(ppid) == pane_pid:
                                        cmdline = pl.split(None, 2)[2].lower()
                                        if any(name in cmdline for name in TMUX_CLI_NAMES):
                                            relevant = True
                                            cmd_l = cmdline
                                            break
                                except Exception:
                                    continue
                    except Exception:
                        pass
                if relevant:
                    panes.append({'pane_id': pane_id, 'pane_pid': pane_pid, 'cmd': cmd_l})
            return panes
        except Exception as e:
            _log_debug(f"list panes error: {e}")
            return []

    def _capture_pane_tail(self, pane_id, lines=200):
        res = self._tmux_run(['capture-pane', '-p', '-J', '-t', pane_id, '-S', f'-{lines}'])
        if not res or res.returncode != 0:
            return ''
        return res.stdout[-2000:]  # limit

    def _friendly_cli_name(self, name: str) -> str:
        try:
            s = (name or '').lower()
            # Mapping by configured friendly names
            for key, label in FRIENDLY_TOOL_NAMES.items():
                if key.lower() in s:
                    return label
            # Fall back to known CLI tokens
            for key in TMUX_CLI_NAMES:
                if key in s:
                    return key
            return name
        except Exception:
            return name

    def check_cli_activity(self):
        try:
            import time
            now = time.time()
            panes = self._list_relevant_panes()
            for pane in panes:
                pid = pane['pane_pid']
                pane_id = pane['pane_id']
                name = pane['cmd']
                content = self._capture_pane_tail(pane_id)
                h = hash(content)
                st = self.pane_state.get(pane_id, {'last_hash': None, 'last_change_ts': now, 'soft_notified': False, 'force_done': False, 'name': name})
                # Detect change
                if st['last_hash'] != h:
                    st['last_hash'] = h
                    st['last_change_ts'] = now
                    st['soft_notified'] = False
                    st['force_done'] = False
                    st['name'] = name
                else:
                    idle = now - st['last_change_ts']
                    # First stage: soft hint
                    if idle >= IDLE_SOFT_THRESHOLD_SEC and not st.get('soft_notified'):
                        # Show blue bubble (gentle)
                        friendly = self._friendly_cli_name(name)
                        try:
                            tmpl = random.choice(IDLE_HINT_MESSAGES)
                            msg = tmpl.format(name=friendly)
                        except Exception:
                            msg = f"{friendly}……　いまは　しずか　みたい　やぁん……"
                        if self.bubble:
                            self.bubble.close()
                            self.bubble = None
                        self.bubble = SpeechBubble(msg, self, bubble_type='hook')
                        self.bubble.show()
                        st['soft_notified'] = True
                    # Second stage: force if enabled
                    if idle >= IDLE_FORCE_THRESHOLD_SEC and not st.get('force_done'):
                        if self.yaruki_switch_mode:
                            self._yaruki_force(pane_id)
                            # Optional feedback bubble
                            friendly = self._friendly_cli_name(name)
                            hard_msg = f"{friendly}……　やるきスイッチ　いれた　やぁん！"
                            if self.bubble:
                                self.bubble.close()
                                self.bubble = None
                            self.bubble = SpeechBubble(hard_msg, self, bubble_type='hook')
                            self.bubble.show()
                        st['force_done'] = True
                self.pane_state[pane_id] = st
            # Cleanup state for panes that disappeared
            existing_ids = set(p['pane_id'] for p in panes)
            for key in list(self.pane_state.keys()):
                if key not in existing_ids:
                    del self.pane_state[key]
        except Exception as e:
            _log_debug(f"check_cli_activity error: {e}")

    def _tmux_send_keys(self, pane_id, keys):
        try:
            if not keys:
                return
            # send-keys can take multiple keys in one call
            self._tmux_run(['send-keys', '-t', pane_id] + list(keys))
        except Exception as e:
            _log_debug(f"send_keys error: {e}")

    def _yaruki_force(self, pane_id):
        try:
            keys = YARUKI_SEND_KEYS or []
            self._tmux_send_keys(pane_id, keys)
            _log_debug(f"yaruki: sent keys {keys} to {pane_id}")
        except Exception as e:
            _log_debug(f"yaruki_force error: {e}")
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            # Ensure we don't take focus from the active app
            try:
                QApplication.setActiveWindow(None)
            except Exception:
                pass
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Show context menu to toggle やるきスイッチ
            self.show_context_menu(event.globalPosition().toPoint())
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            event.accept()

    def focusInEvent(self, event):
        # Immediately relinquish any accidental focus
        try:
            self.clearFocus()
            QApplication.setActiveWindow(None)
        except Exception:
            pass
        event.ignore()

    def event(self, e):
        # Prevent activation on various focus/activation events
        if e.type() in (QEvent.Type.WindowActivate, QEvent.Type.ActivationChange, QEvent.Type.FocusIn):
            try:
                self.clearFocus()
                QApplication.setActiveWindow(None)
            except Exception:
                pass
            return True
        return super().event(e)

    def show_context_menu(self, global_pos):
        menu = QMenu()
        # Avoid stealing focus
        menu.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        act_toggle = menu.addAction('やるきスイッチ: ON' if self.yaruki_switch_mode else 'やるきスイッチ: OFF')
        def toggle():
            self.yaruki_switch_mode = not self.yaruki_switch_mode
            # Update animation speed when toggled
            self.update_animation_speed()
            # Small confirmation bubble
            name = 'やるきスイッチ: ON' if self.yaruki_switch_mode else 'やるきスイッチ: OFF'
            try:
                if self.bubble:
                    self.bubble.close()
                    self.bubble = None
                self.bubble = SpeechBubble(name, self, bubble_type='hook')
                self.bubble.show()
            except Exception:
                pass
        act_toggle.triggered.connect(toggle)
        menu.exec(global_pos)
    
    def random_action(self):
        # Yadon mostly does nothing or speaks, rarely moves
        action = random.choice(['nothing', 'nothing', 'nothing', 'speak', 'speak', 'move', 'move_and_speak'])
        
        if action in ['move', 'move_and_speak']:
            self.random_move()
        
        if action in ['speak', 'move_and_speak']:
            self.show_message()
        
        # Reset timer with new random interval (very long intervals)
        self.action_timer.stop()
        self.action_timer.start(random.randint(RANDOM_ACTION_MIN_INTERVAL, RANDOM_ACTION_MAX_INTERVAL))
    
    def random_move(self):
        screen = QApplication.primaryScreen().geometry()
        current_pos = self.pos()
        
        # Yadon moves very little - just tiny movements
        # 95% chance to move just a tiny bit, 5% chance for slightly larger move
        if random.random() < TINY_MOVEMENT_PROBABILITY:
            # Tiny movement - Yadon barely moves
            new_x = current_pos.x() + random.randint(-TINY_MOVEMENT_RANGE, TINY_MOVEMENT_RANGE)
            new_y = current_pos.y() + random.randint(-TINY_MOVEMENT_RANGE, TINY_MOVEMENT_RANGE)
        else:
            # Occasionally move a bit more (but still not much)
            new_x = current_pos.x() + random.randint(-SMALL_MOVEMENT_RANGE, SMALL_MOVEMENT_RANGE)
            new_y = current_pos.y() + random.randint(-SMALL_MOVEMENT_RANGE, SMALL_MOVEMENT_RANGE)
        
        # Keep within screen bounds
        new_x = max(0, min(new_x, screen.width() - self.width()))
        new_y = max(0, min(new_y, screen.height() - self.height()))
        
        # Animate movement - extremely slow like Yadon
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(MOVEMENT_DURATION)
        self.animation.setStartValue(current_pos)
        self.animation.setEndValue(QPoint(int(new_x), int(new_y)))
        self.animation.start()
    
    def show_message(self):
        if self.bubble:
            self.bubble.close()
            self.bubble = None
        
        message = random.choice(RANDOM_MESSAGES)
        self.bubble = SpeechBubble(message, self, bubble_type='normal')  # Normal bubble
        self.bubble.show()
        
        # Hide bubble after 5 seconds
        def close_bubble():
            if self.bubble:
                self.bubble.close()
                self.bubble = None
        QTimer.singleShot(BUBBLE_DISPLAY_TIME, close_bubble)
    
    def moveEvent(self, event):
        """Update bubble position when Yadon moves"""
        super().moveEvent(event)
        if self.bubble and self.bubble.isVisible():
            self.bubble.update_position()
    
    
    def check_tmux(self):
        """Check if any tmux session is running"""
        try:
            tmux_running = count_tmux_sessions() > 0

            if tmux_running and not self.tmux_active:
                # tmux just started
                self.tmux_active = True
                self.show_welcome_message()
                self.show()
            elif not tmux_running and self.tmux_active:
                # tmux stopped
                self.tmux_active = False
                self.show_goodbye_message()
                # Don't hide when tool stops
                # QTimer.singleShot(5000, self.hide)  # Hide after goodbye message

            # Hook messages are now checked by separate timer

        except Exception as e:
            print(f"Error checking tmux status: {e}")
    
    # check_hook_messages removed (hooks not used)
    
    
    def show_welcome_message(self):
        """Show message when tmux sessions appear"""
        message = random.choice(WELCOME_MESSAGES)
        if self.bubble:
            self.bubble.close()
            self.bubble = None
        self.bubble = SpeechBubble(message, self, bubble_type='normal')  # Normal bubble
        self.bubble.show()
        def close_bubble():
            if self.bubble:
                self.bubble.close()
                self.bubble = None
        QTimer.singleShot(BUBBLE_DISPLAY_TIME, close_bubble)
    
    def show_goodbye_message(self):
        """Show message when no tmux sessions remain"""
        message = random.choice(GOODBYE_MESSAGES)
        if self.bubble:
            self.bubble.close()
            self.bubble = None
        self.bubble = SpeechBubble(message, self, bubble_type='normal')  # Normal bubble
        self.bubble.show()
        def close_bubble():
            if self.bubble:
                self.bubble.close()
                self.bubble = None
        QTimer.singleShot(BUBBLE_DISPLAY_TIME, close_bubble)


def signal_handler(sig, frame):
    """Clean exit on Ctrl+C"""
    QApplication.quit()
    sys.exit(0)


def main():
    # Check for existing instance
    lockfile_path = '/tmp/yadon_pet.lock'
    lockfile = None
    
    try:
        # Try to create/open lock file
        lockfile = open(lockfile_path, 'w')
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lockfile.write(str(os.getpid()))
        lockfile.flush()
    except (IOError, OSError):
        # Another instance is running, kill it first
        try:
            # Kill all existing yadon_pet.py processes
            subprocess.run(['pkill', '-f', 'yadon_pet.py'], check=False)
            # Wait a bit for processes to die
            import time
            time.sleep(0.5)
            # Try to acquire lock again
            if lockfile:
                lockfile.close()
            lockfile = open(lockfile_path, 'w')
            fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lockfile.write(str(os.getpid()))
            lockfile.flush()
        except:
            print("Failed to start Yadon - another instance may be running")
            sys.exit(1)
    
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    
    app = QApplication(sys.argv)
    
    # Also handle Ctrl+C in Qt event loop
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Dummy timer to process events
    timer.start(500)
    
    # Create Yadon pets based on number of tmux sessions
    pets = []
    tmux_count = count_tmux_sessions()
    
    # Create one Yadon for each tmux session (up to 4)
    num_pets = min(tmux_count, MAX_YADON_COUNT) if tmux_count > 0 else 0
    
    # Prefer screen under cursor to improve discoverability
    screen_obj = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
    screen = screen_obj.geometry()
    
    # Get tmux session names
    sessions = get_tmux_sessions()
    _log_debug(f"startup: tmux_count={tmux_count}, sessions={sessions}")
    
    # Calculate positions for bottom-right alignment
    # Stack them horizontally from right to left at the bottom
    margin = 20  # Margin from screen edges
    spacing = 10  # Space between Yadons
    
    for i in range(num_pets):
        # Pass specific tmux session to each Yadon
        session_name = sessions[i] if i < len(sessions) else None
        # Randomly select variant with equal probability
        variant = random.choice(VARIANT_ORDER)
        pet = YadonPet(tmux_session=session_name, variant=variant)
        _log_debug(f"created pet for session={session_name} variant={variant}")
        
        # Position in bottom-right, stacking from right to left
        x_pos = screen.width() - margin - (WINDOW_WIDTH + spacing) * (i + 1)
        y_pos = screen.height() - margin - WINDOW_HEIGHT
        pet.move(x_pos, y_pos)
        _log_debug(f"moved pet to ({x_pos},{y_pos})")
        
        pets.append(pet)
    
    # Monitor for changes in tmux sessions
    monitor = ProcessMonitor(pets)
    monitor.start()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        # Clean up lock file
        if lockfile:
            try:
                fcntl.flock(lockfile, fcntl.LOCK_UN)
                lockfile.close()
                os.unlink(lockfile_path)
            except:
                pass

if __name__ == '__main__':
    main()
