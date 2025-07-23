import os

# Secrets
akm_endpoint = None
akm_secret = None
use_akm = os.environ.get("F42_USE_AKM")
if use_akm == "1":
    akm_endpoint = os.environ.get("F42_AKM_ENDPOINT")
    akm_secret = os.environ.get("F42_AKM_SECRET")

    assert akm_endpoint is not None
    assert akm_secret is not None

    import requests

    req = requests.put(akm_endpoint, data=akm_secret)
    if req.status_code != 200:
        print(f"failed to fetch secrets: [{req.status_code}] {req.text}")
        exit(1)
    secret = req.text
else:
    secret = os.environ.get("F42_CLIENT_SECRET")
key = os.environ.get("F42_CLIENT_ID")
bocal_token = os.environ.get("F42_BOCAL_KEY")
update_key = os.environ.get("F42_UPDATE_KEY")

# Configuration
db_path = os.environ.get("F42_DB", default="database.db")
domain = os.environ.get("F42_DOMAIN")
proxy_domain = os.environ.get("F42_PROXY_DOMAIN", default=domain)
redirect_url = f"http://{domain}:{os.environ.get('F42_PORT')}/auth"
if use_akm == "1":
    redirect_url  = f"https://{domain}/auth"
auth_link = f"https://api.intra.42.fr/oauth/authorize?client_id={key}&redirect_uri={redirect_url}&response_type=code&scope=public"
redis_host = os.environ.get("F42_REDIS_HOST")
redis_port = os.environ.get("F42_REDIS_PORT")
campuses_to_update = [1]
sentry_traces_sample_rate = 0.4
sentry_profiles_sample_rate = 0.4
