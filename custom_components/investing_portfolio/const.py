"""Constants for the Investing Portfolio integration."""

DOMAIN = "investing_portfolio"

# Default headers
DEFAULT_X_APP_VER = "1408"
DEFAULT_X_META_VER = "14"

# API Configuration
API_BASE_URL = "https://aappapi.investing.com"
API_URL = (
    "https://aappapi.investing.com/portfolio_api.php"
    "?data=%7B%22action%22%3A%22get_portfolio_positions%22%2C%22bring_sums%22%3Afalse"
    "%2C%22include_pair_attr%22%3Afalse%2C%22pair_id%22%3A0%2C%22portfolioid%22%3A{portfolio_id}"
    "%2C%22positionType%22%3A%22summary%22%7D&lang_ID=4&time_utc_offset=3600&skinID=2"
)

# Configuration keys (stored in config entry data)
CONF_EMAIL = "email"
CONF_X_TOKEN = "x_token"
CONF_X_UDID = "x_udid"
CONF_PORTFOLIO_ID = "portfolio_id"
CONF_PORTFOLIO_NAME = "portfolio_name"

# Options keys (configurable update schedule)
CONF_UPDATE_WEEKDAY_INTERVAL = "update_weekday_interval"
CONF_UPDATE_WEEKDAY_START = "update_weekday_start"
CONF_UPDATE_WEEKDAY_END = "update_weekday_end"
CONF_UPDATE_NIGHT_TIME = "update_night_time"
CONF_UPDATE_MORNING_TIME = "update_morning_time"

# Default values
DEFAULT_PORTFOLIO_ID = 0
DEFAULT_UPDATE_WEEKDAY_INTERVAL = 15  # minutes
DEFAULT_UPDATE_WEEKDAY_START = 9  # hour
DEFAULT_UPDATE_WEEKDAY_END = 21  # hour
DEFAULT_UPDATE_NIGHT_TIME = "22:05"
DEFAULT_UPDATE_MORNING_TIME = "04:00"

# Error codes from API
ERROR_TOKEN_EXPIRED = "1001"  # x-token or x-udid invalid
ERROR_INVALID_PORTFOLIO = "203"  # Invalid portfolio ID

# Notification service (for error alerts)
NOTIFICATION_TITLE = "Investing Portfolio"

