import requests
import time

def main():
    # Login as admin to get token
    res = requests.post("http://127.0.0.1:8000/api/auth/login", data={"username": "admin@titantrade.com", "password": "adminpassword"})
    if res.status_code != 200:
        print("Login failed")
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate custom Indian stock signal
    payload = {
        "asset_id": "NSE:TATASTEEL",
        "asset_name": "TATASTEEL",
        "asset_type": "indian",
        "timeframe": "1H",
        "timeframes": ["1H", "4H", "1D"],
        "strategy": "elliott_wave",
        "trading_mode": "swing",
        "num_tp_levels": 3
    }

    print("Testing custom Indian signal generation...")
    res = requests.post("http://127.0.0.1:8000/api/signals/generate", json=payload, headers=headers)

    # We might get an error because the server is not running, let's start it first.
    print(res.status_code)
    try:
        print(res.json())
    except:
        print(res.text)

if __name__ == "__main__":
    main()
