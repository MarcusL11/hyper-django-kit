"""
Common constants used across the application.
"""

# Maximum filename base length (conservative for cross-platform compatibility)
# Used by sanitize_filename() for safe file naming across filesystems and APIs
MAX_FILENAME_BASE_LENGTH = 50
