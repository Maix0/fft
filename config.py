import os
# Secrets
secret = os.environ.get("F42_CLIENT_SECRET")
key = os.environ.get("F42_CLIENT_ID") 
bocal_token = os.environ.get("F42_BOCAL_KEY")
update_key = os.environ.get("F42_UPDATE_KEY")
telegram_token = ""
sentry = ""

# Configuration
redirect_url = "https://{current_domain}/auth"
auth_link = f"https://api.intra.42.fr/oauth/authorize?client_id={key}&redirect_uri={redirect_url}&response_type=code&scope=public"
redis_host = os.environ.get("F42_REDIS_HOST")
redis_port = os.environ.get("F42_REDIS_PORT")
campuses_to_update = [1]
sentry_traces_sample_rate = 0.4
sentry_profiles_sample_rate = 0.4
