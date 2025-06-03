import requests
from bs4 import BeautifulSoup
import time
import os

clusters = [
    "f0",
    "f1",
    "f1b",
    "f2",
    "f4",
    "f6",
]
cookie = os.environ.get("SCRAPER_COOKIE")
port = os.environ.get("F42_PORT", default=80)
update_token = os.environ.get("F42_UPDATE_KEY")
headers = {"user-agent": "FFT-Issue/0.1"}
all_issues = {}

for cluster in clusters:
    try:
        doc = requests.get(
            f"https://friends.42paris.fr/?cluster={cluster}",
            cookies={"token": cookie},
            headers=headers,
        )
        soup = BeautifulSoup(doc.text, "html.parser")
        dead = soup.find_all("td", class_="dead")
        issue = soup.find_all("td", class_="attention")

        for e in dead:
            all_issues[e.attrs["data-pos"]] = 1
        for e in issue:
            all_issues[e.attrs["data-pos"]] = 2
        print(f"Got {len(dead) + len(issue)} issues on cluster {cluster}")
    except:
        print(f"Failed to get page for {cluster}")
    time.sleep(2)

print(f"Sending {len(all_issues)} to instence")
for pc, ty in all_issues.items():
    requests.get(f"http://127.0.0.1:{port}/addissue/{update_token}/{pc}/{ty}")
    time.sleep(0.1)
print("Done")
