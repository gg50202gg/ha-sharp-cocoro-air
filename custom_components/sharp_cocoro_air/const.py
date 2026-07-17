"""Constants for the SHARP COCORO AIR integration."""

from datetime import timedelta

DOMAIN = "sharp_cocoro_air"
PLATFORMS = ["fan", "sensor"]

CONF_APP_SECRET = "app_secret"
CONF_TERMINAL_APP_ID = "terminal_app_id"
CONF_BOX_ID = "box_id"
CONF_DEVICE_ID = "device_id"
CONF_ECHONET_NODE = "echonet_node"
CONF_ECHONET_OBJECT = "echonet_object"
CONF_BASE_URL = "base_url"
CONF_USER_AGENT = "user_agent"

DEFAULT_BASE_URL = "https://tw-hms.cloudlabs.sharp.co.jp/hems/pfApi/ta"
DEFAULT_ECHONET_OBJECT = "013501"
DEFAULT_NAME = "SHARP 空氣清淨機"
DEFAULT_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 15)"
SCAN_INTERVAL = timedelta(seconds=60)

POWER_ON = "30"
POWER_OFF = "31"
MODE_AUTO = "20"
MODE_POLLEN = "13"
MODE_SLEEP = "11"
MODE_FEEL = "40"
MODE_QUIET = "14"
MODE_MEDIUM = "15"
MODE_STRONG = "16"
PRESET_TO_CODE = {
    "auto": MODE_AUTO,
    "pollen": MODE_POLLEN,
    "sleep": MODE_SLEEP,
    "feel": MODE_FEEL,
    "quiet": MODE_QUIET,
    "medium": MODE_MEDIUM,
    "strong": MODE_STRONG,
}
CODE_TO_PRESET = {value: key for key, value in PRESET_TO_CODE.items()}
