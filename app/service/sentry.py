import os
import sys
import json
import threading
import requests
from datetime import datetime
from time import sleep

from app2.client.engsel import send_api_request
from app.service.auth import AuthInstance


def enter_sentry_mode():
    api_key = AuthInstance.api_key
    active_user = AuthInstance.get_active_user()
    if active_user is None:
        return None

    tokens = active_user["tokens"]

    if not os.path.exists("sentry"):
        os.makedirs("sentry")

    file_name = os.path.join(
        "sentry",
        f"sentry_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    )

    stop_flag = {"stop": False}

    # Background listener for "q"
    def listen_for_quit():
        while True:
            user_input = sys.stdin.readline()
            if not user_input:
                continue
            if user_input.strip().lower() == "q":
                stop_flag["stop"] = True
                break

    listener_thread = threading.Thread(target=listen_for_quit, daemon=True)
    listener_thread.start()

    id_token = tokens.get("id_token")
    path = "api/v8/packages/quota-details"
    payload = {"is_enterprise": False, "lang": "en", "family_member_id": ""}

    try:
        with open(file_name, "a", encoding="utf-8") as f:
            while not stop_flag["stop"]:
                sleep(1)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    res = send_api_request(api_key, path, payload, id_token, "POST")
                    if res.get("status") != "SUCCESS":
                        return None

                    quotas = res["data"]["quotas"]
                    data_point = {"time": timestamp, "quotas": quotas}

                    f.write(json.dumps(data_point) + "\n")
                    f.flush()

                except Exception:
                    continue

    except KeyboardInterrupt:
        pass

    return file_name
