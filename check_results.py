import requests
import time
import random
import os
import json

def send_telegram_message(bot_token, chat_id, message):
    """Send a message to Telegram chat"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
        return response.ok
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False

def try_roll_numbers(prefix="2610", dob="11/05/2010", year="2026", 
                     doctype="SSCER", delay=0.5, start_from=None, random_order=False,
                     telegram_bot_token=None, telegram_chat_id=None):
    """
    Try roll number suffixes from 0000 to 9999.
    prefix + 4-digit suffix = full roll number.
    """
    url = "https://results.digilocker.gov.in/api/cbse/sscer/results"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Generate all 4-digit suffixes from 0000 to 9999
    all_suffixes = [f"{s:04d}" for s in range(10000)]  # 0000, 0001, ..., 9999

    if random_order:
        random.shuffle(all_suffixes)
        print("Trying suffixes in random order (10,000 combinations).")
    elif start_from is not None:
        if 0 <= start_from <= 9999:
            start_idx = start_from
            all_suffixes = all_suffixes[start_idx:] + all_suffixes[:start_idx]
            print(f"Starting from suffix {start_idx:04d} and continuing sequentially.")
        else:
            print(f"Invalid start_from {start_from}, must be 0-9999. Starting from 0000.")
    else:
        print("Starting from 0000 sequentially.")

    for suffix in all_suffixes:
        roll_number = prefix + suffix
        payload = {
            "rroll": roll_number,
            "doctype": doctype,
            "dob": dob,
            "year": year
        }

        print(f"Trying roll number: {roll_number}")

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            try:
                data = response.json()
            except:
                data = {}

            if response.status_code == 200:
                # Check for success indicators (customize if needed)
                data_str = json.dumps(data).lower()
                if (isinstance(data, dict) and 
                    (data.get("statusCode") == "SUCCESS" or 
                     "result" in data or 
                     "marks" in data_str or
                     "name" in data_str)):
                    print(f"\n*** SUCCESS! Valid roll number: {roll_number} ***")
                    print("Response:", json.dumps(data, indent=2)[:500])
                    
                    # Save locally
                    with open("valid_result.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    
                    # Send Telegram notification
                    if telegram_bot_token and telegram_chat_id:
                        msg = (f"✅ CBSE Result Found!\n"
                               f"Roll Number: {roll_number}\n"
                               f"DOB: {dob}\n"
                               f"Year: {year}\n"
                               f"Full response saved in valid_result.json")
                        send_telegram_message(telegram_bot_token, telegram_chat_id, msg)
                        print("Telegram notification sent.")
                    else:
                        print("Telegram credentials missing, skipping notification.")
                    
                    return roll_number, data
                else:
                    # Normal "not found" response
                    error_indicators = ["not found", "invalid", "error", "no record"]
                    if any(ind in data_str for ind in error_indicators):
                        print(f"  -> No result")
                    else:
                        print(f"  -> Probably no result")
            else:
                print(f"  -> HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"  -> Request failed: {e}")

        time.sleep(delay)

    print("No valid roll number found in range 0000-9999.")
    return None, None

if __name__ == "__main__":
    # ========== CONFIGURATION ==========
    PREFIX = "2610"            # Fixed prefix (4 digits)
    DOB = "11/05/2010"
    YEAR = "2026"
    DOCTYPE = "SSCER"
    DELAY = 0.5                # Seconds between requests
    START_FROM = None          # e.g., 5000, or None to start from 0000
    RANDOM_ORDER = False       # Set True to randomise order

    # ========== TELEGRAM SECRETS ==========
    # Read from environment variables (Replit/Streamlit/GitHub secrets)
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ WARNING: Telegram credentials not found in environment variables.")
        print("   No notifications will be sent. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
    else:
        print("✅ Telegram credentials loaded.")
    
    # Run the search
    roll, response_data = try_roll_numbers(
        prefix=PREFIX,
        dob=DOB,
        year=YEAR,
        doctype=DOCTYPE,
        delay=DELAY,
        start_from=START_FROM,
        random_order=RANDOM_ORDER,
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID
    )
    
    if roll:
        print(f"\n🎉 Success! Roll number: {roll}")
    else:
        print("\n❌ No match found in 10,000 attempts.")        except:
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
