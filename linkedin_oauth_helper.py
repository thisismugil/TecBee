# linkedin_oauth_helper.py
from flask import Flask, request
import requests, os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

app = Flask(__name__)

@app.route("/")
def index():
    # ✅ OIDC + posting scopes, no r_liteprofile
    # openid + profile + email -> for user info
    # w_member_social -> to post on member's behalf
    scopes = "openid profile email w_member_social"
    scope_param = scopes.replace(" ", "%20")

    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope_param}"
    )
    return f"<a href='{auth_url}'>Click here to authorize LinkedIn</a>"

@app.route("/callback")
def callback():
    err = request.args.get("error")
    if err:
        desc = request.args.get("error_description", "")
        return f"OAuth error: {err}<br>{desc}", 400

    code = request.args.get("code")
    if not code:
        return "No code in callback", 400

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r = requests.post(token_url, data=data)
    j = r.json()
    access_token = j.get("access_token")

    return (
        "Your access token (copy into .env as LINKEDIN_ACCESS_TOKEN):"
        f"<br><pre>{access_token}</pre><br>"
        f"Raw JSON:<br><pre>{j}</pre>"
    )

if __name__ == "__main__":
    app.run(port=8000, debug=True)
