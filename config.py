"""Configuration file for Yadon Desktop Pet"""

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

# Messages that Yadon can say randomly
RANDOM_MESSAGES = [
    "ヤドンの　きょうも　がんばってる　やぁん！",
    "やぁん……　おつかれさま　やぁん",
    "ヤドンは　すごい　みたい　やぁん！",
    "きょうは　なんようび　やぁん……？",
    "あっ！　おしごと　してる　やぁん！",
    "ねむくない　やぁん？　ヤドンは　ねむい　やぁん……",
    "たまには　きゅうけい　する　やぁん！",
    "がんばってる　みたい　やぁん！　なにかは　わからない　やぁん……",
    "えらい　やぁん！　……たぶん　やぁん！",
    "その　ボタン　おす　やぁん？　どれかは　しらない　やぁん……",
    "コーヒー　のむ　やぁん？　いれかた　しらない　やぁん……",
    "しゅうちゅう　してる　みたい　やぁん！",
    "いい　てんき　やぁん！　まど　ないけど　やぁん……",
    "ヤドン　ねむい　やぁん……　いつも　ねむい　やぁん……",
    "ファイト　やぁん！　なにと　たたかうか　しらない　やぁん……"
]

# Welcome messages when development tool starts (Claude/Codex)
WELCOME_MESSAGES = [
    "おっ！　きた　やぁん！　おてつだい　する　やぁん！",
    "おしごと　やぁん？　ヤドン　がんばる　やぁん！",
    "いっしょに　いる　やぁん！　よろしく　やぁん！",
    "なにか　つくる　やぁん……　むずかしそう　やぁん……",
    "きょうも　がんばる　やぁん！　おうえん　する　やぁん！"
]

# Goodbye messages when development tool stops (Claude/Codex)
GOODBYE_MESSAGES = [
    "しゅうりょう　やぁん……　またね　やぁん！",
    "おつかれさま　やぁん……　ヤドン　ねる　やぁん……",
    "バイバイ　やぁん！　また　あとで　やぁん！",
    "きょうも　おつかれ　やぁん！　ゆっくり　やすむ　やぁん！",
    "また　あそぼう　やぁん！　まってる　やぁん！"
]

# Hook responses
HOOK_RESPONSES = {
    'stop:': "ひとやすみ　する　やぁん！",
    'notification:': "びびっと　きた　やぁん！"
}

# UI Constants
PIXEL_SIZE = 4
WINDOW_WIDTH = 16 * PIXEL_SIZE
WINDOW_HEIGHT = 16 * PIXEL_SIZE + 20  # Extra space for PID display

# Animation Constants
FACE_ANIMATION_INTERVAL = 500  # milliseconds
RANDOM_ACTION_MIN_INTERVAL = 45000  # 45 seconds
RANDOM_ACTION_MAX_INTERVAL = 90000  # 90 seconds
CLAUDE_CHECK_INTERVAL = 5000  # 5 seconds
HOOK_CHECK_INTERVAL = 1000  # 1 second
MOVEMENT_DURATION = 15000  # 15 seconds (slow movement)

# Movement Constants
TINY_MOVEMENT_RANGE = 20  # pixels
SMALL_MOVEMENT_RANGE = 80  # pixels
TINY_MOVEMENT_PROBABILITY = 0.95

# Speech Bubble Constants
BUBBLE_MAX_WIDTH = 320
BUBBLE_MIN_WIDTH = 250
BUBBLE_HEIGHT = 80
BUBBLE_PADDING = 20
BUBBLE_DISPLAY_TIME = 5000  # milliseconds

# Font Settings
BUBBLE_FONT_FAMILY = "Monaco"
BUBBLE_FONT_SIZE = 14
PID_FONT_FAMILY = "Arial"
PID_FONT_SIZE = 12

# Variant order for multiple Yadons
VARIANT_ORDER = ['normal', 'shiny', 'galarian', 'galarian_shiny']

# Maximum number of Yadon instances
MAX_YADON_COUNT = 4

# Hook file locations (tmux focused)
HOOK_FILE_PATTERNS = [
    # Session-specific
    '/tmp/yadon_hook_{session}.txt',
    '/tmp/tmux_hook_{session}.txt',
    # Generic (first Yadon responds)
    '/tmp/yadon_hook.txt',
    '/tmp/tmux_hook.txt'
]

# Debug log location
DEBUG_LOG = '/tmp/yadon_debug.log'
