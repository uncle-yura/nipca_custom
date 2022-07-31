DOMAIN = "nipca_custom"
DEFAULT_NAME = "NIPCA Custom"
SCAN_INTERVAL = 10
ASYNC_TIMEOUT = 10

DATA_NIPCA = "nipca.{}"

COMMON_INFO = "{}/common/info.cgi"
STREAM_INFO = "{}/config/stream_info.cgi"
MOTION_INFO = [
    "{}/config/motion.cgi",
    "{}/motion.cgi",  # Some D-Links has only this one working
]
STILL_IMAGE = "{}/image/jpeg.cgi"
NOTIFY_STREAM = "{}/config/notify_stream.cgi"

STEP_CONFIG = "config"
