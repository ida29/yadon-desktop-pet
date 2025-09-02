#!/usr/bin/env python3
import sys
import random
import signal
import subprocess
import os
import fcntl
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QRect
from PyQt6.QtGui import QPainter, QColor, QMouseEvent, QFont

from config import (
    COLOR_SCHEMES, RANDOM_MESSAGES, WELCOME_MESSAGES, GOODBYE_MESSAGES,
    PIXEL_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT,
    FACE_ANIMATION_INTERVAL, RANDOM_ACTION_MIN_INTERVAL, RANDOM_ACTION_MAX_INTERVAL,
    CLAUDE_CHECK_INTERVAL, HOOK_CHECK_INTERVAL, MOVEMENT_DURATION,
    TINY_MOVEMENT_RANGE, SMALL_MOVEMENT_RANGE, TINY_MOVEMENT_PROBABILITY,
    BUBBLE_DISPLAY_TIME, PID_FONT_FAMILY, PID_FONT_SIZE,
    VARIANT_ORDER, MAX_YADON_COUNT
)
from speech_bubble import SpeechBubble
from process_monitor import ProcessMonitor, count_claude_processes, get_claude_pids, find_claude_pid
from hook_handler import HookHandler
from pixel_data import build_pixel_data

class YadonPet(QWidget):
    def __init__(self, claude_pid=None, variant='normal'):
        super().__init__()
        self.claude_pid = claude_pid if claude_pid else find_claude_pid()
        self.variant = variant
        
        # Build pixel data with variant colors
        self.pixel_data = build_pixel_data(variant)
        
        self.face_offset = 0
        self.animation_direction = 1
        self.drag_position = None
        
        self.bubble = None
        self.prefer_edges = True  # Prefer screen edges where text is less likely
        
        # Claude Code detection
        self.claude_code_active = False
        
        # Hook handler
        self.hook_handler = HookHandler(self.claude_pid)
        
        self.init_ui()
        self.setup_animation()
        self.setup_random_actions()
        self.setup_claude_code_monitor()
    
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
        if hasattr(self, 'hook_timer'):
            self.hook_timer.stop()
        super().closeEvent(event)
    
    def init_ui(self):
        self.setWindowTitle('Yadon Desktop Pet')
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # Add space for PID display
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        
        # Don't set position here - it will be set in main()
        self.show()
        self.raise_()
        self.activateWindow()
        
    def setup_animation(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_face)
        self.timer.start(FACE_ANIMATION_INTERVAL)
    
    def setup_random_actions(self):
        self.action_timer = QTimer()
        self.action_timer.timeout.connect(self.random_action)
        self.action_timer.start(random.randint(RANDOM_ACTION_MIN_INTERVAL, RANDOM_ACTION_MAX_INTERVAL))
    
    def setup_claude_code_monitor(self):
        """Monitor Claude Code process and hook files"""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_claude_code)
        self.monitor_timer.start(CLAUDE_CHECK_INTERVAL)
        
        # Setup separate hook monitor with faster interval
        self.hook_timer = QTimer()
        self.hook_timer.timeout.connect(self.check_hook_messages)
        self.hook_timer.start(HOOK_CHECK_INTERVAL)
        
        # Initial check
        self.check_claude_code()
    
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
        
        # Draw PID below Yadon with white background
        pid_text = f"{self.claude_pid if self.claude_pid else 'N/A'}"
        font = QFont(PID_FONT_FAMILY, PID_FONT_SIZE)
        font.setBold(True)
        painter.setFont(font)
        
        # Calculate text size
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(pid_text)
        text_height = metrics.height()
        
        # Draw white background for PID
        bg_rect = QRect((self.width() - text_width - 4) // 2, 66, text_width + 4, text_height + 2)
        painter.fillRect(bg_rect, QColor(255, 255, 255, 200))  # Semi-transparent white
        painter.setPen(QColor(0, 0, 0))  # Black border
        painter.drawRect(bg_rect)
        
        # Draw PID text
        painter.setPen(QColor(0, 0, 0))  # Black text
        painter.drawText(self.rect().adjusted(0, 68, 0, 0), Qt.AlignmentFlag.AlignHCenter, pid_text)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            event.accept()
    
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
    
    
    def check_claude_code(self):
        """Check if Claude Code is running"""
        try:
            # Check for Claude Code process (actual claude, not yadon)
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            claude_running = False
            for line in lines:
                if 'claude' in line and 'yadon' not in line and 'node' not in line and 'grep' not in line:
                    claude_running = True
                    break
            
            if claude_running and not self.claude_code_active:
                # Claude Code just started
                self.claude_code_active = True
                self.show_welcome_message()
                self.show()
            elif not claude_running and self.claude_code_active:
                # Claude Code stopped
                self.claude_code_active = False
                self.show_goodbye_message()
                # Don't hide when Claude Code stops
                # QTimer.singleShot(5000, self.hide)  # Hide after goodbye message
            
            # Hook messages are now checked by separate timer
                
        except Exception as e:
            print(f"Error checking Claude Code: {e}")
    
    def check_hook_messages(self):
        """Check for Claude Code hook messages in temp files"""
        result = self.hook_handler.check_hook_messages()
        if result:
            bubble_type, message = result
            if self.bubble:
                self.bubble.close()
                self.bubble = None
            self.bubble = SpeechBubble(message, self, bubble_type=bubble_type)
            self.bubble.show()
            def close_bubble():
                if self.bubble:
                    self.bubble.close()
                    self.bubble = None
            QTimer.singleShot(BUBBLE_DISPLAY_TIME, close_bubble)
    
    
    def show_welcome_message(self):
        """Show message when Claude Code starts"""
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
        """Show message when Claude Code stops"""
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
    
    # Create Yadon pets based on number of Claude Code processes
    pets = []
    claude_count = count_claude_processes()
    
    # Create one Yadon for each Claude Code process (up to 4)
    num_pets = min(claude_count, MAX_YADON_COUNT) if claude_count > 0 else 1
    
    screen = QApplication.primaryScreen().geometry()
    
    # Get Claude process PIDs (actual claude processes only)
    claude_pids = get_claude_pids()
    
    # Calculate positions for bottom-right alignment
    # Stack them horizontally from right to left at the bottom
    margin = 20  # Margin from screen edges
    spacing = 10  # Space between Yadons
    
    for i in range(num_pets):
        # Pass specific Claude PID to each Yadon
        claude_pid = claude_pids[i] if i < len(claude_pids) else None
        # Randomly select variant with equal probability
        variant = random.choice(VARIANT_ORDER)
        pet = YadonPet(claude_pid=claude_pid, variant=variant)
        
        # Position in bottom-right, stacking from right to left
        x_pos = screen.width() - margin - (WINDOW_WIDTH + spacing) * (i + 1)
        y_pos = screen.height() - margin - WINDOW_HEIGHT
        pet.move(x_pos, y_pos)
        
        pets.append(pet)
    
    # Monitor for changes in Claude Code processes
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