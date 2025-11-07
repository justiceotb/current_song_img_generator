"""Configuration for the Current Song Image Generator"""

# Image settings
IMAGE_WIDTH = 250
IMAGE_HEIGHT = 122
COLOR_MODE = "monochrome"  # Options: "monochrome", "grayscale", "7color"

# Radio station settings
STATION = "doublej"
POLL_INTERVAL = 30  # seconds between API checks
PREFERRED_ARTWORK_HEIGHT = 300  # Preferred artwork height in pixels (will select closest match)
DISPLAY_TIMEZONE = "Australia/Sydney"  # Timezone for displaying play times (e.g., "Australia/Sydney" for AEDT/AEST)

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080
OUTPUT_DIR = "output"  # Directory where images and hash will be saved

# File paths (relative to OUTPUT_DIR)
IMAGE_FILENAME = "current_song.png"
HASH_FILENAME = "current_song_hash.txt"

# Layout settings
ARTWORK_SIZE = 122  # Square artwork (height of image)
TEXT_MARGIN = 10  # Pixels between artwork and text
LINE_SPACING = 5  # Pixels between text lines

# Font settings (None will use default PIL font)
FONT_PATH = None  # e.g., "/path/to/font.ttf" or None for default
FONT_SIZE_TITLE = 16
FONT_SIZE_ARTIST = 14
FONT_SIZE_ALBUM = 12

# Dithering settings (for grayscale and 7color modes)
DITHER_METHOD = "floyd-steinberg"  # Options: "floyd-steinberg", "none"
