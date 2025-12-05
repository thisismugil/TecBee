import os, requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("LINKEDIN_ACCESS_TOKEN")
if not token:
    raise RuntimeError("LINKEDIN_ACCESS_TOKEN not found in .env")

print("Token length:", len(token))

r = requests.get(
    "https://api.linkedin.com/v2/userinfo",
    headers={"Authorization": f"Bearer {token}"},
    timeout=15
)

print("HTTP status:", r.status_code)
print("Body:", r.json())
