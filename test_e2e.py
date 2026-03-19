import urllib.request
import urllib.error
import json
import time

BASE_URL = 'http://127.0.0.1:5000'

def test_flow():
    print("Testing Nightly Check-In...")
    checkin_payload = {
        "target_bedtime": "23:00",
        "tiktok_hours": 1.5,
        "youtube_hours": 1.0,
        "other_socials_hours": 0.5,
        "gaming_hours": 0.0,
        "academic_hours_after_bedtime": 1.0,
        "pickups_after_bedtime": 5,
        "caffeine_type": "Coffee",
        "caffeine_time": "18:00",
        "caffeine_modifiers": True
    }
    
    req = urllib.request.Request(
        f"{BASE_URL}/checkin", 
        data=json.dumps(checkin_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        r = urllib.request.urlopen(req)
        print(f"Checkin Status: {r.getcode()}")
        print(f"Checkin Response: {r.read().decode('utf-8')}")
    except urllib.error.HTTPError as e:
        print(f"Checkin ERROR: {e.code}")
        print(e.read().decode('utf-8'))
        return
    
    time.sleep(1)

    print("\nTesting Morning Check-In...")
    morning_payload = {
        "time_to_fall_asleep_mins": 45,
        "morning_grogginess_score": 8
    }
    req_m = urllib.request.Request(
        f"{BASE_URL}/api/morning_feedback", 
        data=json.dumps(morning_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        r_m = urllib.request.urlopen(req_m)
        print(f"Morning Status: {r_m.getcode()}")
        resp = r_m.read().decode('utf-8')
        print(f"Morning Response: {resp}")
    except urllib.error.HTTPError as e:
        print(f"Morning ERROR: {e.code}")
        print(e.read().decode('utf-8'))

if __name__ == "__main__":
    test_flow()
