import os, time, uuid, json, base64, smtplib, imaplib, email, datetime
from pathlib import Path
from email.message import EmailMessage

import requests
from flask import Flask, send_from_directory, render_template_string
from dotenv import load_dotenv
from PIL import Image, ImageDraw
import threading
import base64
import requests
from pathlib import Path
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import html


load_dotenv()

# === Paths ===
BASE_DIR = Path(__file__).parent
ARCHIVE_DIR = BASE_DIR / "archive"
ARCHIVE_DIR.mkdir(exist_ok=True)

# === LinkedIn config ===
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")

# === Email config ===
EMAIL_SMTP = os.getenv("EMAIL_SMTP", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_IMAP = os.getenv("EMAIL_IMAP", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# === Time config ===
POST_HOUR = int(os.getenv("POST_HOUR", "9"))
POST_GRACE_MINUTES = int(os.getenv("POST_GRACE_MINUTES", "15"))

# ---------- Gemini helpers ----------

def pick_gemini_key() -> str:
    """Rotate keys by day-of-year."""
    raw = os.getenv("GEMINI_KEYS", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise RuntimeError("No GEMINI_KEYS set in .env")
    day_index = datetime.datetime.now().timetuple().tm_yday
    return keys[day_index % len(keys)]

def generate_text_with_gemini(topic_title: str, mode: str) -> str:
    """
    Use Gemini to generate LinkedIn-ready text:
    - Greeting line
    - 3–5 bullet points with emojis
    - Optional 'Caption:' line
    - Hashtags at the end
    """
    api_keys = [k.strip() for k in os.getenv("GEMINI_KEYS", "").split(",") if k.strip()]
    if not api_keys:
        raise RuntimeError("No GEMINI_KEYS set in .env")

    if mode == "article":
        post_type_desc = "a short LinkedIn explainer post"
    elif mode == "meme":
        post_type_desc = (
            "a LinkedIn post that explains the topic briefly, then gives a fun meme-style caption "
            "on a separate line starting with 'Caption:'"
        )
    elif mode == "short":
        post_type_desc = "a concise LinkedIn update"
    else:  # freestyle
        post_type_desc = "a LinkedIn post mixing information and a light Gen Z tone"

    prompt = (
        "You are a professional but Gen Z-friendly tech writer creating a LinkedIn post.\n\n"
        f"Topic: {topic_title}\n\n"
        f"Write {post_type_desc} with this structure:\n"
        "1) First line: a friendly greeting, e.g. 'Hey tech fam 👋' or similar.\n"
        "2) Then 3–5 bullet points. Each bullet:\n"
        "   - Starts with an emoji (like 🔹, 🚀, 🤖, ⚙️, 💡 etc.)\n"
        "   - Has 1–3 short lines, not a huge paragraph.\n"
        "   - Is factual, neutral and easy to skim.\n"
        "3) If the mode is meme, include a separate line starting with 'Caption:' "
        "that is a fun but respectful meme-style caption.\n"
        "4) End with 3–6 relevant hashtags on one line. Example: #Tech #AI #Cloud\n\n"
        "Rules:\n"
        "- Do NOT directly attack or insult any person or company.\n"
        "- No slang that feels offensive or cringe.\n"
        "- Keep it understandable for a broad audience.\n"
    )

    body = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
    }

    model = "gemini-2.5-flash"
    last_error = None

    for key in api_keys:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            r = requests.post(url, json=body, timeout=60)
            if r.status_code == 429:
                print("Text: key rate-limited, trying next Gemini key...")
                last_error = "rate-limited"
                continue
            r.raise_for_status()
            data = r.json()
            chunks = []
            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if "text" in part:
                        chunks.append(part["text"])
            text = "\n".join(chunks).strip()
            if text:
                return text
        except Exception as e:
            print("Gemini text error with one key:", e)
            last_error = str(e)
            continue

    print("All Gemini keys failed for text, using fallback. Last error:", last_error)
    return (
        f"Hey tech fam 👋\n\n"
        f"🔹 Quick update on: {topic_title}\n\n"
        "Caption: Quick tech update.\n\n"
        "#Tech #News"
    )


# def generate_image_with_gemini(topic_title: str, mode: str, out_path: Path) -> bool:
#     """
#     Use gemini-2.5-flash-image for image generation.
#     If a key gets 429 (Too Many Requests), try the next key.
#     Only fall back to placeholder if all keys fail or are rate-limited.
#     """
#     api_keys = [k.strip() for k in os.getenv("GEMINI_KEYS", "").split(",") if k.strip()]
#     if not api_keys:
#         print("No GEMINI_KEYS set, skipping Gemini image.")
#         return False

#     model = "gemini-2.5-flash-image"

#     if mode == "meme":
#         style = (
#             "An eye-catching, meme-style tech illustration in a 1:1 square format. "
#             "Clean, bold composition, no text in the image, no logos, no real faces. "
#             "Should clearly relate to the topic so that someone seeing the image "
#             "can guess it is about streaming platforms and tech."
#         )
#     else:
#         style = (
#             "A clean, modern tech-themed illustration suitable for a LinkedIn post. "
#             "1:1 square format, minimalistic, no logos, no real faces. "
#             "Should visually relate to the topic."
#         )

#     prompt = f"{style} Topic: {topic_title}"

#     body = {
#         "contents": [
#             {"parts": [{"text": prompt}]}
#         ],
#         "generationConfig": {
#             "imageConfig": {"aspectRatio": "1:1"}
#         }
#     }

#     last_error = None

#     for key in api_keys:
#         url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
#         try:
#             r = requests.post(url, json=body, timeout=120)
#             if r.status_code == 429:
#                 print("Image: key rate-limited, trying next Gemini key...")
#                 last_error = "rate-limited"
#                 continue
#             r.raise_for_status()
#             data = r.json()
#             parts = data["candidates"][0]["content"]["parts"]
#             img_part = next(p for p in parts if "inlineData" in p)
#             b64 = img_part["inlineData"]["data"]
#             img_bytes = base64.b64decode(b64)
#             out_path.write_bytes(img_bytes)
#             print("Gemini image saved.")
#             return True
#         except Exception as e:
#             print("Gemini image error with one key:", e)
#             last_error = str(e)
#             continue

#     print("All Gemini keys failed for image, last error:", last_error)
#     return False
def generate_image_with_nvidia(prompt: str, out_path: Path):
    """
    Generate an image using NVIDIA NIM (Stable Diffusion 3 Medium).

    Requires:
      - NVIDIA_API_KEY in your environment
    """
    if not NVIDIA_API_KEY:
        raise RuntimeError("NVIDIA_API_KEY not set in environment")

    url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
    }

    payload = {
        "prompt": prompt,
        "cfg_scale": 5,
        "aspect_ratio": "1:1",
        "seed": 0,
        "steps": 30,
        "negative_prompt": ""
    }

    print("Calling NVIDIA NIM image API...")
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    # NIM returns base64-encoded PNG under "image" for SD3 Medium :contentReference[oaicite:2]{index=2}
    image_b64 = data.get("image")
    if not image_b64:
        raise RuntimeError("NIM: no 'image' field in response")

    img_bytes = base64.b64decode(image_b64)
    with open(out_path, "wb") as f:
        f.write(img_bytes)

    print("NVIDIA NIM image saved:", out_path)

from PIL import Image, ImageDraw, ImageFont
import textwrap, random
from pathlib import Path

def fallback_image(topic_title: str, out_path: Path):
    """
    Fully compatible fallback — never fails on old Pillow.
    Draws centered-ish wrapped text without measuring size.
    """

    # Pleasant background colors
    colors = [
        (25, 118, 210),   # blue
        (56, 142, 60),    # green
        (123, 31, 162),   # purple
        (245, 124, 0),    # orange
        (2, 136, 209),    # light blue
    ]
    bg = random.choice(colors)

    width, height = 1024, 1024
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Try nicer font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 48)
        small_font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()
        small_font = font

    # Split title into wrapped lines
    title = topic_title[:120]
    lines = textwrap.wrap(title, width=22)

    # Vertical center: approximate baseline
    total_lines = len(lines)
    line_height = 60  # fixed height value to avoid measuring
    start_y = (height - total_lines * line_height) // 2

    # Draw white box background behind title block
    box_x0, box_x1 = 80, width - 80
    box_y0 = start_y - 60
    box_y1 = start_y + total_lines * line_height + 20
    draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill=(255, 255, 255))

    # Draw wrapped lines (centered by fixed offset)
    for i, line in enumerate(lines):
        y = start_y + i * line_height
        draw.text((100, y), line, fill=(20, 20, 20), font=font)

    # Footer subtitle
    footer = "Daily Tech Snapshot"
    draw.text((width//2 - 150, box_y1 + 25), footer, fill=(230, 230, 230), font=small_font)

    img.save(out_path)
    print("Saved ultra-compatible fallback banner image.")

# ---------- Trending topic (Hacker News) ----------

import random
import requests

def fetch_hackernews_top(limit: int = 10):
    """
    Try to fetch a top story from Hacker News.
    If there is any SSL/network error, fall back to a static topic list.
    This way the script never crashes just because HN is down or TLS is weird.
    """
    fallback_topics = [
        {
            "title": "Latest AI breakthroughs shaping 2025",
            "url": "https://ai.google",
            "score": 0,
        },
        {
            "title": "How GPUs are powering the next wave of AI startups",
            "url": "https://nvidia.com",
            "score": 0,
        },
        {
            "title": "Serverless vs containers: what modern teams actually use",
            "url": "https://aws.amazon.com",
            "score": 0,
        },
        {
            "title": "Top 5 trends in full-stack development for 2025",
            "url": "https://developer.mozilla.org",
            "score": 0,
        },
    ]

    try:
        ids_resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=20
        )
        ids_resp.raise_for_status()
        ids = ids_resp.json()
        topics = []
        for id_ in ids[:limit]:
            try:
                item_resp = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{id_}.json",
                    timeout=20
                )
                item_resp.raise_for_status()
                item = item_resp.json()
                topics.append({
                    "title": item.get("title", "No title"),
                    "url": item.get("url", "https://news.ycombinator.com/"),
                    "score": item.get("score", 0)
                })
            except Exception as inner_e:
                print("Error fetching an HN item, skipping:", inner_e)
                continue

        if topics:
            topics.sort(key=lambda t: t["score"], reverse=True)
            return topics[0]
        else:
            print("No topics from HN, using fallback.")
            return random.choice(fallback_topics)

    except Exception as e:
        print("Hacker News fetch failed, using fallback topic. Error:", e)
        return random.choice(fallback_topics)

# ---------- Day-of-week mode rotation ----------

def get_mode_for_today() -> str:
    # Monday=0, Sunday=6
    weekday = datetime.datetime.now().weekday()
    if weekday == 0:   # Mon
        return "article"
    if weekday == 1:   # Tue
        return "meme"
    if weekday == 2:   # Wed
        return "short"
    if weekday == 3:   # Thu
        return "article"
    if weekday == 4:   # Fri
        return "meme"
    if weekday == 5:   # Sat
        return "freestyle"
    # Sunday: no post
    return "none"

# ---------- Email helpers ----------

def send_email(to_address: str, subject: str, body_text: str, body_html: str | None = None):
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_USER
    msg["To"] = to_address
    msg["Subject"] = subject

    # Plain text part (always)
    part1 = MIMEText(body_text, "plain")
    msg.attach(part1)

    # Optional HTML part
    if body_html:
        part2 = MIMEText(body_html, "html")
        msg.attach(part2)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(EMAIL_USER, EMAIL_PASS)
        s.sendmail(EMAIL_USER, [to_address], msg.as_string())

def send_preview_email(preview_id: str, title: str):
    preview_url = f"http://127.0.0.1:5000/preview/{preview_id}"

    # Plain text fallback (for clients that ignore HTML)
    body_text = f"""Preview for: {title}

Preview URL:
{preview_url}

After reviewing, reply to this email with:

APPROVE {preview_id}

to post to LinkedIn at the scheduled time.
"""

    safe_title = html.escape(title)

    # HTML body with a button
    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 16px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 24px; border-radius: 8px;">
          <h2 style="color:#0a66c2; margin-top:0;">📌 Preview your LinkedIn post</h2>
          <p style="font-size: 16px; color:#333;">
            <strong>{safe_title}</strong>
          </p>
          <p style="font-size: 14px; color:#555;">
            Click the button below to open the post preview in your browser:
          </p>
          <p style="text-align:center; margin: 24px 0;">
            <a href="{preview_url}"
               style="display:inline-block; padding:12px 24px;
                      background:#0a66c2; color:#ffffff; text-decoration:none;
                      border-radius:6px; font-weight:bold;">
              View Preview
            </a>
          </p>
          <hr style="border:none; border-top:1px solid #eee; margin:24px 0;" />
          <p style="font-size: 13px; color:#777; line-height:1.5;">
            After reviewing, reply to this email with:<br/>
            <code style="background:#f0f0f0; padding:4px 6px; border-radius:4px;">
              APPROVE {preview_id}
            </code><br/>
            Your bot will then post it automatically to your LinkedIn profile.
          </p>
        </div>
      </body>
    </html>
    """

    send_email(
        EMAIL_USER,
        f"[Preview] LinkedIn {preview_id}",
        body_text,
        body_html
    )


def poll_for_approval(preview_id: str, deadline_dt: datetime.datetime) -> bool:
    M = imaplib.IMAP4_SSL(EMAIL_IMAP)
    M.login(EMAIL_USER, EMAIL_PASS)
    try:
        while datetime.datetime.now() < deadline_dt:
            M.select("INBOX")
            typ, data = M.search(None, "UNSEEN")
            if typ == "OK":
                for num in data[0].split():
                    typ2, msg_data = M.fetch(num, "(RFC822)")
                    raw = msg_data[0][1]
                    mail = email.message_from_bytes(raw)
                    subj = (mail.get("Subject") or "").upper()
                    if f"APPROVE {preview_id}".upper() in subj:
                        print("Approval email detected.")
                        return True
            time.sleep(30)
        return False
    finally:
        M.logout()

def send_summary_email(success: bool, title: str, topic_url: str):
    status = "SUCCESS" if success else "NOT POSTED"
    body = (
        f"LinkedIn auto-post summary for {datetime.date.today()}:\n\n"
        f"Status: {status}\n"
        f"Topic: {title}\n"
        f"Source: {topic_url}\n"
    )
    send_email(EMAIL_USER, f"[Summary] LinkedIn auto-post {status}", body)

# ---------- Flask preview ----------

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<title>Preview {{post_id}}</title>
<h2>LinkedIn Auto-Post Preview ({{post_id}})</h2>
<p><b>Topic:</b> {{title}}</p>
<p><b>Source:</b> <a href="{{src_url}}">{{src_url}}</a></p>
<img src="/archive/{{post_id}}/image.png" style="max-width:600px;display:block;margin-bottom:20px;">
<pre style="white-space:pre-wrap;">{{text}}</pre>
"""


@app.route("/preview/<id_>")
def preview(id_):
    folder = ARCHIVE_DIR / id_
    if not folder.exists():
        return "Not found", 404
    meta = json.loads((folder / "meta.json").read_text())
    text = (folder / "text.txt").read_text(encoding="utf-8")
    return render_template_string(
        TEMPLATE,
        post_id=id_,
        title=meta["title"],
        src_url=meta["url"],
        text=text,
    )


@app.route("/archive/<id_>/<filename>")
def serve_file(id_, filename):
    folder = ARCHIVE_DIR / id_
    return send_from_directory(folder, filename)

def start_preview_server():
    threading.Thread(
        target=lambda: app.run(port=5000, debug=False, use_reloader=False),
        daemon=True
    ).start()

# ---------- LinkedIn image upload + post ----------

def upload_image_to_linkedin(image_path: Path) -> str:
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    register_body = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": LINKEDIN_PERSON_URN,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    r = requests.post(register_url, headers=headers, json=register_body)
    r.raise_for_status()
    data = r.json()
    upload_mech = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]
    upload_url = upload_mech["uploadUrl"]
    asset_urn = data["value"]["asset"]

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    upload_headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "image/png"
    }
    r2 = requests.put(upload_url, headers=upload_headers, data=img_bytes)
    r2.raise_for_status()
    return asset_urn

def post_to_linkedin(title: str, full_text: str, image_path: Path) -> bool:
    asset_urn = upload_image_to_linkedin(image_path)

    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    body = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": full_text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "description": {"text": title},
                    "media": asset_urn,
                    "title": {"text": title}
                }]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    url = "https://api.linkedin.com/v2/ugcPosts"
    r = requests.post(url, headers=headers, json=body)
    print("LinkedIn post status:", r.status_code, r.text)
    return r.ok

# ---------- Main ----------

def main():
    now = datetime.datetime.now()
    if now.hour < 6:
        print("Too early (<06:00), exiting.")
        return

    mode = get_mode_for_today()
    if mode == "none":
        print("Sunday: skipping auto-post.")
        return

    start_preview_server()

    topic = fetch_hackernews_top()
    title = topic["title"]
    url = topic["url"]
    print("Chosen topic:", title, url, "mode:", mode)

    text = generate_text_with_gemini(title, mode)

    folder_id = now.strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6]
    folder = ARCHIVE_DIR / folder_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "meta.json").write_text(json.dumps({"title": title, "url": url}, indent=2))
    (folder / "text.txt").write_text(text, encoding="utf-8")

    # ---------- IMAGE GENERATION (NVIDIA NIM) ----------
    img_path = folder / "image.png"
    try:
        image_prompt = f"""
Professional, minimal, high-contrast tech artwork about:
"{title}"

Requirements:
- 1:1 square aspect ratio
- Clean, modern illustration
- No logos of real companies
- No real faces
- Should look good as a LinkedIn post visual
"""
        generate_image_with_nvidia(image_prompt, img_path)
    except Exception as e:
        print("NVIDIA NIM image error:", e)
        fallback_image(title, img_path)
    # ---------------------------------------------------

    send_preview_email(folder_id, title)

    # Wait until POST_HOUR, then poll until grace end
    target = now.replace(hour=POST_HOUR, minute=0, second=0, microsecond=0)
    if datetime.datetime.now() < target:
        sleep_secs = (target - datetime.datetime.now()).total_seconds()
        print(f"Sleeping until {POST_HOUR}:00 (~{int(sleep_secs)}s)")
        time.sleep(max(0, sleep_secs))

    deadline = target + datetime.timedelta(minutes=POST_GRACE_MINUTES)
    approved = poll_for_approval(folder_id, deadline)
    if not approved:
        print("No approval received by deadline, not posting.")
        send_summary_email(False, title, url)
        return

    success = post_to_linkedin(title, text, img_path)
    send_summary_email(success, title, url)

if __name__ == "__main__":
    main()
