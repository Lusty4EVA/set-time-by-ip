
"""
set_time_by_ip.py

Detect the your pc's public IP resolve its IANA timezone and optionally apply
that timezone to the host OS (Linux via timedatectl, Windows via tzutil).

IMPORTANT read below


Safety & usage:
 - This script can change your system timezone By default it runs in DRY-RUN mode.
 - To actually apply changes pass `--apply`. To skip the interactive prompt pass `--force`.
 - On Linux you will likely need `sudo` to run timedatectl.
 - On Windows you must run the script in an elevated (Administrator) prompt to run tzutil.
 - The script caches ip timezone mappings to avoid repeatedly hitting free API limits.
 - Configure behavior in 'settings.py' (project scaffold includes a settings file).
 - Settings are expected to exist in settings.py in the same directory.
Example:
  python set_time_by_ip.py                          # dry-run (default)
  python set_time_by_ip.py --apply                  # actually apply (will ask confirmation) yes or no
  python set_time_by_ip.py --apply --force          # apply without confirmation
"""



# import gay
import re
import sys
import platform
import subprocess
import json
import time as time_module
from pathlib import Path
import requests
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


try:
        from settings import (
        IPIFY_URL,
        IPAPI_TZ_BY_IP,
        WORLDTIMEAPI_BY_IP,
        DRY_RUN,
        FORCE_APPLY,
        IANA_TO_WINDOWS,
        REQUEST_TIMEOUT,
        MAX_RETRIES,
        BACKOFF_BASE,
        CACHE_FILE,
        VERBOSE,
        USE_SELENIUM_FALLBACK,
    )

except Exception as e:
    print("Failed to load settings.py. Make sure a settings.py exists in the same folder.")
    raise

# --------------------------- Utilities ---------------------------------


def looks_like_iana(tz: str) -> bool:
    if not tz or not isinstance(tz, str):
        return False
    return bool(re.match(r'^[A-Za-z_]+\/[A-Za-z_+\-]+', tz))


def verbose_print(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


def load_cache() -> dict:
    try:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        verbose_print("Failed to load cache:", exc)
    return {}


def save_cache(d: dict):
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        verbose_print("Failed to save cache:", exc)



def get_public_ip(timeout=REQUEST_TIMEOUT) -> str or None:
    try:
        r = requests.get(IPIFY_URL, timeout=timeout)
        r.raise_for_status()
        return r.text.strip()
    except Exception as e:
        verbose_print("Failed to get public IP:", e)
        return None



def _fetch_with_retries(url: str, timeout: int = REQUEST_TIMEOUT, max_retries: int = MAX_RETRIES):
    backoff = BACKOFF_BASE
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code == 429:
                verbose_print(f"Rate limited (429) for {url}; backing off {backoff}s (attempt {attempt})")
                time_module.sleep(backoff)
                backoff *= 2
                continue
           
            return r
        except Exception as e:
            last_exc = e
            verbose_print(f"Network error for {url}: {e}; retrying in {backoff}s")
            time_module.sleep(backoff)
            backoff *= 2
            continue
    if last_exc:
        raise last_exc
    return None



def get_iana_timezone_for_ip(ip: str) -> str or None:
    """Try ipapi then worldtimeapi fallback. Return IANA tz or None."""
    if not ip:
        return None

    cache = load_cache()
    if ip in cache:
        verbose_print("Cache hit for IP", ip)
        return cache[ip]

    url_ipapi = IPAPI_TZ_BY_IP.format(ip=ip)
    try:
        r = _fetch_with_retries(url_ipapi)
        if r and r.status_code == 200:
            tz = r.text.strip()
            if tz:
                cache[ip] = tz
                save_cache(cache)
                return tz
    except Exception as e:
        verbose_print("ipapi fetch error:", e)



    try:
        url_wt = WORLDTIMEAPI_BY_IP.format(ip=ip)
        r2 = _fetch_with_retries(url_wt)
        if r2 and r2.status_code == 200:
            try:
                data = r2.json()
                tz2 = data.get("timezone")
                if tz2:
                    cache[ip] = tz2
                    save_cache(cache)
                    return tz2
            except Exception:
                verbose_print("worldtimeapi json parse failed")
    except Exception as e:
        verbose_print("worldtimeapi fetch error:", e)


    if USE_SELENIUM_FALLBACK:
        try:
            verbose_print("Attempting Selenium fallback (proxy6.net)...")
            from selenium_fallback import get_timezone_by_selenium
            tz3 = get_timezone_by_selenium()
            if tz3:
                cache[ip] = tz3
                save_cache(cache)
                return tz3
            verbose_print("Selenium fallback returned nothing.")
        except Exception as e:
            verbose_print("Selenium fallback failed:", e)

    return None





def set_timezone_linux(iana_tz: str) -> bool:
    """Set timezone on Linux using timedatectl. Requires sudo."""
    try:
        try:
            ZoneInfo(iana_tz)
        except ZoneInfoNotFoundError:
            raise RuntimeError(
                f"IANA timezone '{iana_tz}' not found locally. Install tzdata or `pip install tzdata`."
            )

        subprocess.run(["timedatectl", "set-timezone", iana_tz], check=True)
        return True
    except subprocess.CalledProcessError as e:
        verbose_print("timedatectl failed:", e)
        return False


def set_timezone_windows(iana_tz: str) -> bool:
    """Map IANA -> Windows and set timezone via tzutil (requires admin)."""
    win_name = IANA_TO_WINDOWS.get(iana_tz)
    if not win_name:
        verbose_print("No Windows mapping for IANA tz", iana_tz)
        return False
    try:
        subprocess.run(["tzutil", "/s", win_name], check=True, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        verbose_print("tzutil failed:", e)
        return False




def main(argv: list) -> int:
    dry_run = DRY_RUN
    force = FORCE_APPLY

    if "--apply" in argv:
        dry_run = False
    if "--force" in argv:
        force = True

    ip = get_public_ip()
    if not ip:
        print("Could not detect public IP. Aborting.")
        return 1
    print("Public IP:", ip)

    tz = get_iana_timezone_for_ip(ip)
    if not tz:
        print("Could not determine IANA timezone for IP. Aborting.")
        return 2
    print("Detected IANA timezone:", tz)

    os_name = platform.system()
    print("Platform:", os_name)

    if dry_run:
        print("DRY RUN: nothing will be changed. Use --apply to actually change system timezone.")

    if not dry_run and not force:
        ans = input(f"Apply timezone '{tz}' to this machine? Type YES to proceed: ")
        if ans.strip() != "YES":
            print("Aborted by user.")
            return 0

    success = False
    if os_name == "Linux":
        if dry_run:
            print(f"Would run: timedatectl set-timezone {tz}")
            success = True
        else:
            success = set_timezone_linux(tz)
    elif os_name == "Windows":
        if dry_run:
            mapped = IANA_TO_WINDOWS.get(tz)
            print(f"Would run: tzutil /s <mapped-name-for-{tz}>")
            print("Mapped Windows name:", mapped)
            success = bool(mapped)
        else:
            success = set_timezone_windows(tz)
    else:
        print("Unsupported OS:", os_name)
        return 3

    if success:
        print("Operation succeeded (or dry-run reported success).")
        return 0
    else:
        print("Operation failed.")
        return 4


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
