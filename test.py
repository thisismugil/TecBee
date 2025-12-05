# test_linkedin_post.py
import os, requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")

assert ACCESS_TOKEN, "Missing LINKEDIN_ACCESS_TOKEN"
assert PERSON_URN, "Missing LINKEDIN_PERSON_URN"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type": "application/json"
}

body = {
    "author": PERSON_URN,
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": "Test post ✅ from my Python script (safe test)."
            },
            "shareMediaCategory": "NONE"
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
}

resp = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=body)
print("Status:", resp.status_code)
print("Response:", resp.text)
