# set-time-by-ip

A small tool that detects your public IP, resolves the correct IANA timezone for that IP, and optionally applies the timezone to your operating system.

The script runs in dry-run mode by default. Use `--apply` to make actual changes. On Linux you may need sudo. On Windows you must run in an elevated command prompt.

## Features

- Detect public IP
- Resolve IANA timezone from IP using external APIs
- Optional fallback using Selenium and proxy6.net
- Automatic caching to avoid API rate limits
- Safe dry-run mode
- Windows timezone application via `tzutil`
- Linux timezone application via `timedatectl`

## Installation

git clone <your-repo-url>
cd set-time-by-ip
python -m venv venv
venv\Scripts\activate # Windows

or

source venv/bin/activate # Linux/macOS

pip install -r requirements.txt


## Usage

Dry run:

python set_time_by_ip.py

Apply timezone:

python set_time_by_ip.py --apply

Apply without confirmation:




## Files

- `set_time_by_ip.py` – main script
- `settings.py` – configuration and mappings
- `selenium_fallback.py` – alternative timezone detection via proxy6.net
- `requirements.txt` – dependencies
- `.gitignore` – ignored files
- `LICENSE` – MIT license

## Notes

- On Windows, timezone application requires an administrator shell.
- On Linux, timezone application may require sudo.
- Actual system time is not modified by this script; only timezone.
