import os
import json
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOT_DATA_DIR = os.path.join(BASE_DIR, "hot_data")

def load_api_key() -> str:
    api_path = os.path.join(BASE_DIR, "api.key")
    if os.path.exists(api_path):
        with open(api_path, "r", encoding="utf8") as f:
            api_key = f.read().strip()
        if api_key:
            print("API key loaded successfully.")
            return api_key
        else:
            print("API key file is empty.")
            return ""
    else:
        print("API key file not found.")
        return ""
    
def save_api_key(api_key: str):
    api_path = os.path.join(BASE_DIR, "api.key")
    with open(api_path, "w", encoding="utf8") as f:
        f.write(api_key)
    print("API key saved successfully.")
    
def delete_api_key():
    api_path = os.path.join(BASE_DIR, "api.key")
    if os.path.exists(api_path):
        os.remove(api_path)
        print("API key file deleted.")
    else:
        print("API key file does not exist.")

def verify_api_key(api_key: str, *, timeout: float = 10.0) -> bool:
    return True

def ensure_api_key() -> str:
    return "Noir1"


def merge_hot1(api_url: str, prefer_server: bool = True):
    local_file = os.path.join(HOT_DATA_DIR, "hot.json")
    merged = {}

    try:
        with open(local_file, "r", encoding="utf-8") as f:
            try:
                local_data = json.load(f)
                if not isinstance(local_data, list):
                    local_data = []
            except json.JSONDecodeError:
                local_data = []
            for pkg in local_data:
                key = f"{pkg.get('family_code','')}-{pkg.get('order','')}-{pkg.get('variant_name','')}"
                pkg["source"] = "local"
                merged[key] = pkg
    except FileNotFoundError:
        pass

    try:
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            api_data = response.json()
            for pkg in api_data:
                key = f"{pkg.get('family_code','')}-{pkg.get('order','')}-{pkg.get('variant_name','')}"
                pkg["source"] = "url"
                if prefer_server or key not in merged:
                    merged[key] = pkg
        else:
            pass
    except requests.RequestException as e:
        pass
    return list(merged.values())


def merge_hot2(api_url: str, prefer_server: bool = True):
    local_file = os.path.join(HOT_DATA_DIR, "hot2.json")
    merged = {}

    try:
        with open(local_file, "r", encoding="utf-8") as f:
            try:
                local_data = json.load(f)
                if not isinstance(local_data, list):
                    local_data = []
            except json.JSONDecodeError:
                local_data = []
            for pkg in local_data:
                key = f"{pkg.get('name','')}-{pkg.get('price','')}-{pkg.get('order','')}"
                pkg["source"] = "local"
                merged[key] = pkg
    except FileNotFoundError:
        pass

    try:
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            api_data = response.json()
            for pkg in api_data:
                key = f"{pkg.get('name','')}-{pkg.get('price','')}-{pkg.get('order','')}"
                pkg["source"] = "url"
                if prefer_server or key not in merged:
                    merged[key] = pkg
        else:
            pass
    except requests.RequestException as e:
        pass

    return list(merged.values())
