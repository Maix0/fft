#!/usr/bin/python3

import sys
import os
import json
from db import Db


def anonymise_messages(messages: list):
    final_messages = []
    for message in messages:
        if message["anonymous"] != 0:
            message["author"] = -1
        final_messages.append(message)
    return final_messages


def main(login: str):
    data = {}
    with Db() as db:
        user = db.get_user_profile(login)
        if user is None:
            print("User does not exists")
            exit(1)
        user_id = user["id"]
        data["user"] = user
        data["friends"] = db.get_friends(user_id)
        data["cookies"] = db.get_user_all_cookies(user_id)
        data["dead_pc"] = db.get_issues_by_user(user_id)
        data["telegram"] = db.has_notifications(user_id)
        data["theme"] = db.get_theme(user_id)
        data["mates"] = db.get_mates_by_user(user_id)
        data["messages"] = anonymise_messages(db.get_raw_messages(user_id))
    os.makedirs("./data_exports", exist_ok=True)
    with open(f"data_exports/{login}.json", "w") as f:
        f.write(json.dumps(data, indent=2))
    print(f"Export completed for {login}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[1]} login")
        exit(1)
    main(sys.argv[1])
