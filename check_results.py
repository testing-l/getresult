import requests
import time
import random
import os
import json
import sys

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        return resp.ok
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def try_roll_numbers(prefix="26102", dob="29/10/2010", year="2026",
                     doctype="SSCER", delay=2.0, start_from=None, random_order=False,
                     telegram_bot_token=None, telegram_chat_id=None,
                     proxy=None):
    url = "https://results.digilocker.gov.in/api/cbse/sscer/results"
    
    # Realistic browser headers
    headers_template = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://results.digilocker.gov.in",
        "Referer": "https://results.digilocker.gov.in/cbse/sscer/results",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Connection": "keep-alive",
    }
    
    all_suffixes = [f"{s:03d}" for s in range(1000)]
    if random_order:
        random.shuffle(all_suffixes)
        print("Random order enabled")
    elif start_from is not None:
        all_suffixes = all_suffixes[start_from:] + all_suffixes[:start_from]
        print(f"Starting from suffix {start_from:03d}")
    else:
        print("Starting from 000")
    
    session = requests.Session()
    session.headers.update(headers_template)
    
    # Optional proxy
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    for suffix in all_suffixes:
        roll_number = prefix + suffix
        payload = {
            "rroll": roll_number,
            "doctype": doctype,
            "dob": dob,
            "year": year
        }
        
        print(f"Trying: {roll_number}")
        sys.stdout.flush()
        
        # Random jitter between 1-3 seconds to avoid pattern detection
        sleep_time = delay + random.uniform(0, 1)
        
        try:
            response = session.post(url, data=payload, proxies=proxies, timeout=20)
            print(f"  HTTP {response.status_code}")
            
            if response.status_code == 403:
                print("  ! 403 Forbidden – server blocking this IP. Trying with different User-Agent.")
                # Rotate user agent
                ua_list = [
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
                ]
                session.headers.update({"User-Agent": random.choice(ua_list)})
                time.sleep(5)
                continue
                
            if response.status_code != 200:
                print(f"  Skipping (HTTP {response.status_code})")
                time.sleep(sleep_time)
                continue
            
            # Parse response
            try:
                data = response.json()
            except:
                data = {}
            
            data_str = json.dumps(data).lower()
            
            # Success detection
            success = False
            if isinstance(data, dict):
                if data.get("statusCode") == "SUCCESS":
                    success = True
                elif "result" in data and data["result"]:
                    success = True
                elif "student_name" in data_str or "marks" in data_str:
                    success = True
            
            if success:
                print(f"\n*** SUCCESS! Roll number: {roll_number} ***")
                print("Response preview:", json.dumps(data, indent=2)[:500])
                with open("valid_result.json", "w") as f:
                    json.dump(data, f, indent=2)
                if telegram_bot_token and telegram_chat_id:
                    msg = f"✅ CBSE Result Found!\nRoll: {roll_number}\nDOB: {dob}\nYear: {year}"
                    send_telegram_message(telegram_bot_token, telegram_chat_id, msg)
                    print("Telegram notification sent")
                return roll_number, data
            else:
                # Normal not found – no extra print to keep logs clean
                pass
                
        except requests.exceptions.RequestException as e:
            print(f"  Request error: {e}")
        
        time.sleep(sleep_time)
    
    print("No valid roll found in 000-999")
    return None, None

if __name__ == "__main__":
    PREFIX = "26102"
    DOB = "29/10/2010"     # your DOB
    YEAR = "2026"
    DOCTYPE = "SSCER"
    DELAY = 2.0            # base delay (adds random jitter)
    START_FROM = None
    RANDOM_ORDER = False
    
    # Proxy (optional) – if you have a residential proxy, set it here
    PROXY = None  # e.g., "http://user:pass@proxy:port"
    
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing – no notifications")
    
    roll, data = try_roll_numbers(
        prefix=PREFIX,
        dob=DOB,
        year=YEAR,
        doctype=DOCTYPE,
        delay=DELAY,
        start_from=START_FROM,
        random_order=RANDOM_ORDER,
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID,
        proxy=PROXY
    )
    
    if roll:
        print(f"\n✅ SUCCESS: {roll}")
    else:
        print("\n❌ No match found")
