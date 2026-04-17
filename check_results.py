import requests
import time
import random
import os
import json
import sys

# ---------- Telegram ----------
def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        return resp.ok
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

# ---------- Main search ----------
def try_roll_numbers(prefix="26102", dob="11/05/2010", year="2026",
                     doctype="SSCER", delay=1.0, start_from=None, random_order=False,
                     telegram_bot_token=None, telegram_chat_id=None):
    url = "https://results.digilocker.gov.in/api/cbse/sscer/results"
    
    # Realistic headers to avoid 403
    base_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://results.digilocker.gov.in",
        "Referer": "https://results.digilocker.gov.in/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Connection": "keep-alive",
    }
    
    # Generate suffixes 000..999 (3 digits)
    all_suffixes = [f"{s:03d}" for s in range(1000)]
    
    if random_order:
        random.shuffle(all_suffixes)
        print("Random order enabled")
    elif start_from is not None:
        start_idx = start_from
        all_suffixes = all_suffixes[start_idx:] + all_suffixes[:start_idx]
        print(f"Starting from suffix {start_idx:03d}")
    else:
        print("Starting from 000")
    
    session = requests.Session()
    session.headers.update(base_headers)
    
    for suffix in all_suffixes:
        roll_number = prefix + suffix
        payload = {
            "rroll": roll_number,
            "doctype": doctype,
            "dob": dob,
            "year": year
        }
        
        print(f"Trying: {roll_number}")
        sys.stdout.flush()  # Force output in GitHub Actions
        
        try:
            response = session.post(url, data=payload, timeout=15)
            print(f"  HTTP {response.status_code}")
            
            if response.status_code == 403:
                print("  ! 403 Forbidden – trying with fresh headers and longer delay")
                time.sleep(5)
                # Rotate user agent
                new_ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                session.headers.update({"User-Agent": new_ua})
                continue
                
            if response.status_code != 200:
                print(f"  Skipping (HTTP {response.status_code})")
                time.sleep(delay)
                continue
            
            # Parse JSON
            try:
                data = response.json()
            except:
                data = {}
            
            data_str = json.dumps(data).lower()
            
            # Success detection – adjust based on actual API response
            success = False
            if isinstance(data, dict):
                if data.get("statusCode") == "SUCCESS":
                    success = True
                elif "result" in data and data["result"]:
                    success = True
                elif "marks" in data_str or "name" in data_str:
                    success = True
            
            if success:
                print(f"\n*** SUCCESS! Roll number: {roll_number} ***")
                print("Response preview:", json.dumps(data, indent=2)[:500])
                
                with open("valid_result.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                
                if telegram_bot_token and telegram_chat_id:
                    msg = (f"✅ CBSE Result Found!\n"
                           f"Roll: {roll_number}\n"
                           f"DOB: {dob}\n"
                           f"Year: {year}")
                    send_telegram_message(telegram_bot_token, telegram_chat_id, msg)
                    print("Telegram notification sent")
                else:
                    print("Telegram credentials missing – no notification")
                
                return roll_number, data
            else:
                # Normal "not found" – do nothing
                pass
                
        except requests.exceptions.RequestException as e:
            print(f"  Request error: {e}")
        
        time.sleep(delay)
    
    print("No valid roll found in 000-999")
    return None, None

# ---------- Main entry ----------
if __name__ == "__main__":
    PREFIX = "26102"          # as you want
    DOB = "29/10/2010"        # your DOB
    YEAR = "2026"
    DOCTYPE = "SSCER"
    DELAY = 1.0               # seconds between tries (be polite)
    START_FROM = None         # e.g., 500 to start from 500
    RANDOM_ORDER = False
    
    # Read Telegram secrets from environment
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not set – will not send notifications")
    
    roll, data = try_roll_numbers(
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
        print(f"\n✅ SUCCESS: {roll}")
    else:
        print("\n❌ Failed to find roll number")
