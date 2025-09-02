"""Hook handling functionality for Yadon Desktop Pet"""

import os
import subprocess
from config import HOOK_FILE_PATTERNS, HOOK_RESPONSES, DEBUG_LOG


class HookHandler:
    def __init__(self, tmux_session):
        self.tmux_session = tmux_session
        self.last_hook_file = None
        self.last_hook_time = 0
    
    def check_hook_messages(self):
        """Check for hook messages (tmux-aware) in temp files"""
        try:
            # Look for hook files specific to this tool PID
            hook_locations = []
            
            # If we have a specific tmux session, check session-specific files first
            if self.tmux_session:
                for pattern in HOOK_FILE_PATTERNS:
                    if '{session}' in pattern:
                        hook_locations.append(pattern.format(session=self.tmux_session))
                    else:
                        # Add non-PID patterns as-is
                        if pattern.startswith('~'):
                            hook_locations.append(os.path.expanduser(pattern))
                        else:
                            hook_locations.append(pattern)
            else:
                # No session, just check generic files
                for pattern in HOOK_FILE_PATTERNS:
                    if '{session}' not in pattern:
                        if pattern.startswith('~'):
                            hook_locations.append(os.path.expanduser(pattern))
                        else:
                            hook_locations.append(pattern)
            
            # Log to file for debugging
            self._debug_log(f"Yadon PID {os.getpid()} checking hooks for tmux session {self.tmux_session}")
            
            for hook_file in hook_locations:
                if os.path.exists(hook_file):
                    # Read file content first
                    with open(hook_file, 'r') as f:
                        hook_message = f.read().strip()
                    
                    # Only process if there's content
                    if hook_message:
                        self._debug_log(f"Found hook file: {hook_file}")
                        self._debug_log(f"Hook message: {hook_message}")
                        
                        # For generic hook files, only the first Yadon responds
                        if self._should_respond_to_generic_hook(hook_file):
                            response = self._get_hook_response(hook_message)
                            # Clear the hook file after processing
                            with open(hook_file, 'w') as f:
                                f.write('')
                            return response
                        elif self.tmux_session and f'_{self.tmux_session}' in hook_file:
                            # PID-specific hook, always respond
                            response = self._get_hook_response(hook_message)
                            # Clear the hook file after processing
                            with open(hook_file, 'w') as f:
                                f.write('')
                            return response
                        
        except Exception as e:
            self._debug_log(f"Error in check_hook_messages: {e}")
        
        return None
    
    def _should_respond_to_generic_hook(self, hook_file):
        """Check if this Yadon instance should respond to generic hooks"""
        # For generic hook files, only the first Yadon responds
        if 'yadon_hook.txt' in hook_file or 'tmux_hook.txt' in hook_file:
            if '{session}' not in hook_file:  # Make sure it's really generic
                # Check if we're the first by having the lowest PID
                try:
                    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    lines = result.stdout.strip().split('\n')
                    yadon_pids = []
                    for line in lines:
                        if 'yadon_pet.py' in line and 'grep' not in line:
                            parts = line.split()
                            yadon_pids.append(int(parts[1]))
                    
                    # Only respond if we're the first (lowest PID) Yadon
                    return yadon_pids and os.getpid() == min(yadon_pids)
                except Exception:
                    pass
        return False
    
    def _get_hook_response(self, hook_message):
        """Get appropriate response for a hook message"""
        self._debug_log(f"get_hook_response called with: {hook_message}")
        
        # Split message by colon to get type and optional detail
        if ':' in hook_message:
            hook_type, detail = hook_message.split(':', 1)
            self._debug_log(f"hook_type: {hook_type}, detail: {detail}")
            
            # Try to find a response for the type with colon
            for keyword, response in HOOK_RESPONSES.items():
                if keyword == f"{hook_type}:" or keyword == hook_type:
                    # If detail is provided and it's Japanese, use it
                    if detail and any(ord(c) > 127 for c in detail):
                        if detail.endswith('やぁん'):
                            response = detail  # Already has やぁん
                        else:
                            response = f"{detail}やぁん"
                        self._debug_log(f"Using detail as response: {response}")
                    else:
                        self._debug_log(f"Using default response: {response}")
                    return ('hook', response)  # Return type and message
        
        # Fallback: Check for keywords in hook message
        message_lower = hook_message.lower()
        for keyword, response in HOOK_RESPONSES.items():
            if keyword.rstrip(':') in message_lower:
                return ('hook', response)
        
        # If no specific response found, return the message itself with やぁん
        if hook_message:
            return ('hook', f"{hook_message}やぁん")
        
        return None
    
    def _debug_log(self, message):
        """Write debug message to log file"""
        try:
            with open(DEBUG_LOG, 'a') as log:
                log.write(f"{message}\n")
        except Exception:
            pass
