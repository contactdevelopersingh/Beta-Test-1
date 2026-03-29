import requests

def test_generate_indian_signal():
    base_url = "http://127.0.0.1:8000/api"
    # Login as admin
    login_resp = requests.post(f"{base_url}/auth/login", data={"username": "admin@titantrade.com", "password": "adminpassword"})
    if login_resp.status_code != 200:
        print("Login failed")
        return
    token = login_resp.json()["access_token"]
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
    res = requests.post(f"{base_url}/signals/generate", json=payload, headers=headers)
    print(res.status_code)
    try:
        print(res.json())
    except:
        print(res.text)

if __name__ == "__main__":
    test_generate_indian_signal()
