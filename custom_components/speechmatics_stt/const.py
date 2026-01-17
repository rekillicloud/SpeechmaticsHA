"""Constants for Speechmatics STT integration."""

DOMAIN = "speechmatics_stt"

DEFAULT_LANGUAGE = "en"
DEFAULT_OPERATING_POINT = "enhanced"
DEFAULT_MAX_DELAY = 0.8
DEFAULT_CHUNK_SIZE = 4096

SUPPORTED_LANGUAGES = [
    "en",
    "ru",
    "de",
    "fr",
    "es",
    "it",
    "pt",
    "pl",
    "tr",
    "nl",
    "cs",
    "ar",
    "zh",
    "ja",
    "hi",
    "th",
    "vi",
    "ko",
]

OPERATING_POINTS = ["standard", "enhanced"]

CONF_API_KEY = "api_key"
CONF_LANGUAGE = "language"
CONF_OPERATING_POINT = "operating_point"
CONF_MAX_DELAY = "max_delay"
