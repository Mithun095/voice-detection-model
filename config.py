"""
Configuration settings for the Keyword Detector application.

This module centralizes all configurable parameters for easy modification
without touching the main application logic.

TUNING GUIDE:
- Lower SPEAKER_MIN_SIMILARITY for more lenient speaker verification
- Increase SPEAKER_CHECK_INTERVAL to reduce CPU usage
- Adjust BLOCK_SIZE for responsiveness vs accuracy tradeoff
"""

from typing import List

# ===========================================
# PATHS
# ===========================================
VOSK_MODEL_PATH: str = "modelins"
REFERENCE_EMBEDDING_PATH: str = "public/reference_embedding.npy"
REFERENCE_WAV_PATH: str = "public/reference.wav"
SESSION_LOG_PATH: str = "logs/session_log.jsonl"
PUBLIC_DIR: str = "public"

# ===========================================
# AUDIO SETTINGS
# ===========================================
SAMPLE_RATE: int = 16000
BLOCK_SIZE: int = 4000  # Smaller = more responsive, larger = more accurate
CHANNELS: int = 1
AUDIO_DTYPE: str = "int16"

# ===========================================
# SPEAKER VERIFICATION
# ===========================================
# Cosine similarity threshold for speaker verification.
# Range: 0.0 to 1.0 (higher = stricter)
#
# Recommended values:
#   0.50 - 0.55: Very lenient (may accept similar voices)
#   0.55 - 0.65: Balanced (recommended for most environments)
#   0.65 - 0.75: Strict (quieter environment needed)
#   0.75+: Very strict (may reject valid speech)
SPEAKER_MIN_SIMILARITY: float = 0.55  # Lowered for better accuracy

# Time interval (seconds) between speaker verification checks
# Lower = more responsive verification, higher = less CPU usage
SPEAKER_CHECK_INTERVAL: float = 1.5

# Minimum audio samples required for speaker embedding
# At 16kHz: 16000 = 1 second, 24000 = 1.5 seconds
MIN_SAMPLES_FOR_EMBEDDING: int = 16000  # Reduced for faster verification

# ===========================================
# KEYWORDS
# ===========================================
# List of keywords the detector will recognize
# These are constrained in the Vosk grammar for better accuracy
KEYWORDS: List[str] = [
    "yes",
    "no",
    "left",
    "right",
    "up",
    "down",
    "next",
    "cancel",
    "back",
    "start",
    "stop",
    "exit",
]

# Special keywords that trigger specific actions
STOP_KEYWORDS: List[str] = ["stop"]

# ===========================================
# RECORDING SETTINGS
# ===========================================
# Default duration for reference voice recording (seconds)
RECORDING_DURATION: int = 60  # Reduced for faster setup

# Countdown before recording starts (seconds)
RECORDING_COUNTDOWN: int = 3

# ===========================================
# FLASK SERVER
# ===========================================
FLASK_HOST: str = "0.0.0.0"
FLASK_PORT: int = 5000
FLASK_DEBUG: bool = True
