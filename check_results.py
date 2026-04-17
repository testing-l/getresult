import requests
import time
import json
import os
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def send_telegram(message):
    """Send a message to your Telegram chat using environment variables."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram credentials missing – skipping notification")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
        if resp.status_code != 200:
            print(f"Telegram send failed: {resp.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

def load_state():
    """Read the last checked suffix from state.json."""
    state_file = Path("state.json")
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                data = json.load(f)
                return data.get("last_suffix", -1)
        except:
            return -1
    return -1

def save_state(suffix):
    """Store the last checked suffix (integer 0-9999)."""
    with open("state.json", "w") as f:
        json.dump({"last_suffix": suffix}, f)

def try_roll_numbers(base_roll_prefix="2610", dob="11/05/2010", year="2026",
                     doctype="SSCER", delay=0.5):
    url = "https://results.digilocker.gov.in/api/cbse/sscer/results"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # All suffixes from 0000 to 9999
    all_suffixes = [f"{s:04d}" for s in range(10000)]
    last_checked = load_state()
    start_idx = last_checked + 1 if last_checked >= 0 else 0

    if start_idx >= 10000:
        print(f"{Colors.YELLOW}Already checked all 10,000 suffixes. Resetting from 0000.{Colors.RESET}")
        start_idx = 0
        save_state(-1)  # reset state

    print(f"{Colors.CYAN}Resuming from suffix index {start_idx} ({all_suffixes[start_idx]}){Colors.RESET}")

    for i in range(start_idx, len(all_suffixes)):
        roll_suffix = all_suffixes[i]
        roll_number = base_roll_prefix + roll_suffix
        payload = {
            "rroll": roll_number,
            "doctype": doctype,
            "dob": dob,
            "year": year
        }

        print(f"Trying roll number: {roll_number}", end="", flush=True)

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            try:
                data = response.json()
            except:
                data = {}

            if response.status_code == 200:
                print(f"\n{Colors.GREEN}*** MATCH FOUND! Valid roll number: {roll_number} ***{Colors.RESET}")
                # Send Telegram notification with roll number and raw API data
                message = f"✅ *Match Found!*\nRoll Number: `{roll_number}`\n\nRaw Data:\n```json\n{json.dumps(data, indent=2)}\n```"
                send_telegram(message)
                # Also print to console
                print(f"{Colors.YELLOW}Data: {json.dumps(data, indent=2)}{Colors.RESET}")
            elif response.status_code == 400:
                print(f"  {Colors.RED}-> HTTP 400 (Invalid / Not Found){Colors.RESET}")
            else:
                print(f"  {Colors.YELLOW}-> HTTP {response.status_code} - Unexpected{Colors.RESET}")

        except requests.exceptions.RequestException as e:
            print(f"  {Colors.RED}-> Request failed: {e}{Colors.RESET}")

        # Save progress after each attempt (so we can resume if interrupted)
        save_state(i)

        # Respectful delay
        time.sleep(delay)

    print(f"{Colors.CYAN}Finished checking all suffixes.{Colors.RESET}")
    # Reset state after full scan so next run starts fresh
    save_state(-1)

if __name__ == "__main__":
    BASE_ROLL_PREFIX = "2610"
    DOB = "11/05/2010"
    YEAR = "2026"
    DOCTYPE = "SSCER"
    DELAY = 0.5   # seconds between requests

    try_roll_numbers(
        base_roll_prefix=BASE_ROLL_PREFIX,
        dob=DOB,
        year=YEAR,
        doctype=DOCTYPE,
        delay=DELAY
    )
