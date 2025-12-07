from pathlib import Path

IPIFY_URL = "https://api.ipify.org?format=text"
IPAPI_TZ_BY_IP = "https://ipapi.co/{ip}/timezone/"
WORLDTIMEAPI_BY_IP = "http://worldtimeapi.org/api/ip/{ip}"

DRY_RUN = True
FORCE_APPLY = False
USE_SELENIUM_FALLBACK = True # change to True if ipapi is being gay wait is it already true??
VERBOSE = True

IANA_TO_WINDOWS = {
    "Asia/Kolkata": "India Standard Time",
    "America/New_York": "Eastern Standard Time",
    "Europe/London": "GMT Standard Time",
    "Asia/Tokyo": "Tokyo Standard Time",
}

REQUEST_TIMEOUT = 6
MAX_RETRIES = 3
BACKOFF_BASE = 1.0

CACHE_DIR = Path.home() / ".set_time_by_ip"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "ip_tz_cache.json"
