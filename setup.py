import requests

# --- CONFIGURATION ---
MOBIUS_URL = "http://localhost:7579/Mobius"
HEADERS_AE = {
    'X-M2M-RI': '12345',
    'X-M2M-Origin': 'S',
    'Content-Type': 'application/vnd.onem2m-res+json; ty=2'
}
HEADERS_CNT = {
    'X-M2M-RI': '12345',
    'X-M2M-Origin': 'S',
    'Content-Type': 'application/vnd.onem2m-res+json; ty=3'
}

def create_database():
    print("--- REBUILDING MOBIUS DATABASE ---")

    # 1. Create the Main Folder (AE: SmartLock)
    payload_ae = {
        "m2m:ae": {
            "rn": "SmartLock",
            "api": "N.SmartLock",
            "rr": True
        }
    }
    r1 = requests.post(MOBIUS_URL, headers=HEADERS_AE, json=payload_ae)
    if r1.status_code == 201:
        print("✅ Created 'SmartLock' folder.")
    elif r1.status_code == 409:
        print("⚠️ 'SmartLock' folder already exists.")
    else:
        print(f"❌ Failed to create SmartLock. Error: {r1.status_code}")

    # 2. Create the Data Folder (CNT: data)
    payload_cnt = {
        "m2m:cnt": {
            "rn": "data",
            "mni": 100  # Store last 100 items
        }
    }
    r2 = requests.post(MOBIUS_URL + "/SmartLock", headers=HEADERS_CNT, json=payload_cnt)
    if r2.status_code == 201:
        print("✅ Created 'data' folder.")
    elif r2.status_code == 409:
        print("⚠️ 'data' folder already exists.")
    else:
        print(f"❌ Failed to create data folder. Error: {r2.status_code}")

if __name__ == "__main__":
    create_database()