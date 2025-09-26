"""Configuration file for Yadon Desktop Pet"""

# =====================================================================
# APPEARANCE CONFIGURATION
# =====================================================================

# Color schemes for different Yadon variants
COLOR_SCHEMES = {
    'normal': {  # Normal Kantonian Yadon (pink)
        'body': '#F3D599',  # Original yellow-cream color
        'head': '#D32A38',  # Original red color for head/ears
        'accent': '#F3D599'
    },
    'shiny': {  # Shiny Kantonian Yadon (lighter/paler pink)
        'body': '#FFCCFF',  # Very light pink/purple
        'head': '#FF99CC',  # Light pink for head
        'accent': '#FFCCFF'
    },
    'galarian': {  # Galarian Yadon (pink with yellow accents)
        'body': '#F3D599',  # Keep cream body
        'head': '#D32A38',  # Red head
        'accent': '#FFD700'  # Gold/yellow for forehead accents
    },
    'galarian_shiny': {  # Shiny Galarian Yadon (gold/yellow)
        'body': '#FFD700',  # Gold body
        'head': '#FFA500',  # Orange head
        'accent': '#FFD700'  # Gold accents
    }
}

# =====================================================================
# MESSAGE CONFIGURATION
# =====================================================================

# Messages that Yadon can say randomly
RANDOM_MESSAGES = [
    "おつかれさま　やぁん",
    "きょうは　なんようび　やぁん……？",
    "うどん　たべる　やぁん……？",
]

# Welcome messages when development tool starts (Claude/Codex)
WELCOME_MESSAGES = [
    "おてつだい　する　やぁん",
    "がんばる　やぁん",
    "よろしく　やぁん",
    "なにか　つくる　やぁん",
    "きょうも　がんばる　やぁん"
]

# Goodbye messages when development tool stops (Claude/Codex)
GOODBYE_MESSAGES = [
    "やぁん！",
]

# Soft idle hint messages for CLI output pause (Pokemon vibe)
IDLE_HINT_MESSAGES = [
    "{name}……　そっと　みまもる　やぁん……",
]

# やるきスイッチ related messages
YARUKI_SWITCH_ON_MESSAGE = 'やるきスイッチ　ＯＮ'
YARUKI_SWITCH_OFF_MESSAGE = 'やるきスイッチ　ＯＦＦ'
YARUKI_FORCE_MESSAGE = "{name}……　やるきスイッチ　いれた　やぁん！"
YARUKI_MENU_ON_TEXT = 'やるきスイッチ　ＯＮにする'
YARUKI_MENU_OFF_TEXT = 'やるきスイッチ　ＯＦＦにする'

# =====================================================================
# WINDOW & UI CONFIGURATION
# =====================================================================

# Window dimensions
PIXEL_SIZE = 4
WINDOW_WIDTH = 16 * PIXEL_SIZE
WINDOW_HEIGHT = 16 * PIXEL_SIZE + 20  # Extra space for PID display

# Speech bubble settings
BUBBLE_MAX_WIDTH = 320
BUBBLE_MIN_WIDTH = 250
BUBBLE_HEIGHT = 80
BUBBLE_PADDING = 20
BUBBLE_DISPLAY_TIME = 4000  # milliseconds

# Font settings
BUBBLE_FONT_FAMILY = "Monaco"
BUBBLE_FONT_SIZE = 14
PID_FONT_FAMILY = "Arial"
PID_FONT_SIZE = 12

# =====================================================================
# ANIMATION & TIMING CONFIGURATION
# =====================================================================

# Animation intervals
FACE_ANIMATION_INTERVAL = 500  # milliseconds (normal speed)
FACE_ANIMATION_INTERVAL_FAST = 250  # milliseconds (やる気スイッチ ON)

# Random action intervals (how often Yadon does something)
RANDOM_ACTION_MIN_INTERVAL = 3000000  # 50 minutes
RANDOM_ACTION_MAX_INTERVAL = 4200000  # 70 minutes (average ~1 hour)

# Movement settings
MOVEMENT_DURATION = 15000  # 15 seconds (slow movement)
TINY_MOVEMENT_RANGE = 20  # pixels
SMALL_MOVEMENT_RANGE = 80  # pixels
TINY_MOVEMENT_PROBABILITY = 0.95  # 95% chance of tiny movements

# =====================================================================
# YADON INSTANCES CONFIGURATION
# =====================================================================

# Variant order for multiple Yadons
VARIANT_ORDER = ['normal', 'shiny', 'galarian', 'galarian_shiny']

# Maximum number of Yadon instances
MAX_YADON_COUNT = 4

# =====================================================================
# TMUX & CLI MONITORING CONFIGURATION
# =====================================================================

# CLI names to monitor for output activity within tmux panes
TMUX_CLI_NAMES = [
    'claude',
    'codex',
    'codex-cli',
    'gemini'
]

# Friendly display names for tools (match by substring, case-insensitive)
FRIENDLY_TOOL_NAMES = {
    'codex': 'コダック',
    'codex-cli': 'コダック',
    'claude': 'クロバット',
    'gemini': 'シェイミ'
}

# Monitoring intervals
CLAUDE_CHECK_INTERVAL = 5000  # 5 seconds (check tmux sessions)
ACTIVITY_CHECK_INTERVAL_MS = 10000  # 10 seconds (check CLI activity)
OUTPUT_IDLE_THRESHOLD_SEC = 60  # 60 seconds of no output -> notify (legacy)

# Two-stage idle thresholds
IDLE_SOFT_THRESHOLD_SEC = 10  # First gentle nudge
IDLE_FORCE_THRESHOLD_SEC = 30  # 30 seconds for strong action

# =====================================================================
# やるきスイッチ (MOTIVATION SWITCH) CONFIGURATION
# =====================================================================

# Motivation Switch mode: auto input when force threshold reached
YARUKI_SWITCH_MODE = False

# Keys to send to tmux pane when forcing continuation (e.g., rerun last command)
YARUKI_SEND_KEYS = ['Up', 'Enter']

# =====================================================================
# SYSTEM CONFIGURATION
# =====================================================================

# Debug log location
DEBUG_LOG = '/tmp/yadon_debug.log'
