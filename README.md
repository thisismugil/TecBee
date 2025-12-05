# TecBee — LinkedIn Auto Post Tools

A small Python utility collection for automating LinkedIn posts and extracting LinkedIn URNs. Includes helper scripts for OAuth, posting, and simple tests. The repository also stores posted content in an `archive/` folder.

**Overview**

- **Purpose**: Provide tools to post content to LinkedIn programmatically and manage published items.
- **Language**: Python (3.8+ recommended).

**Contents**

- **Scripts**: `auto_post_bot.py`, `get_linkedin_urn.py`, `linkedin_oauth_helper.py` — main utilities for posting and OAuth.
- **Tests**: `test.py`, `test_https.py` — quick, script-style tests.
- **Archive**: `archive/` — subfolders for each posted item containing `meta.json` and `text.txt`.

**Requirements**

- **Dependencies**: See `requirements.txt` for pinned packages.
- **Python**: 3.8 or newer recommended.

**Installation**

1. Create and activate a virtual environment.

```powershell
# create venv (if not already present)
python -m venv venv
; & .\venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

**Configuration**

- The scripts expect LinkedIn OAuth credentials and/or an access token. Provide these via environment variables or update the helper files as needed.
- Suggested environment variables:

  - `LINKEDIN_CLIENT_ID` : your LinkedIn app client id
  - `LINKEDIN_CLIENT_SECRET` : your LinkedIn app client secret
  - `LINKEDIN_REDIRECT_URI` : redirect URI configured in your LinkedIn app
  - `LINKEDIN_ACCESS_TOKEN` : (optional) a persistent access token if you have one

Set them in PowerShell like this:

```powershell
$env:LINKEDIN_CLIENT_ID = 'your-client-id'
$env:LINKEDIN_CLIENT_SECRET = 'your-client-secret'
$env:LINKEDIN_REDIRECT_URI = 'https://your.redirect/uri'
$env:LINKEDIN_ACCESS_TOKEN = 'your-access-token'
```

**Usage**

- Run the OAuth helper to obtain/refresh tokens (if implemented):

```powershell
python linkedin_oauth_helper.py
```

- Use the posting bot (example):

```powershell
python auto_post_bot.py
```

- Extract a LinkedIn URN (example):

```powershell
python get_linkedin_urn.py --profile-url "https://www.linkedin.com/in/username/"
```

Note: Each script may accept additional CLI args or require editing constants at the top of the file — check the file headers for quick usage notes.

**Archive Format**

- Each item stored under `archive/<timestamp-id>/` contains:
  - `meta.json`: JSON metadata about the post (time, id, recipients, etc.)
  - `text.txt`: the message/body that was posted

**Development & Testing**

- Quick test runs:

```powershell
python test.py
python test_https.py
```

- For more structured testing, consider adding `pytest` tests and a `tox`/`GitHub Actions` workflow.

**Files of Interest**

- `auto_post_bot.py`: Main automation script that posts content to LinkedIn.
- `get_linkedin_urn.py`: Helper to extract URNs from profile URLs.
- `linkedin_oauth_helper.py`: Helpers to perform OAuth flows and token management.
- `requirements.txt`: Python dependencies list.

**Contributing**

- Open an issue or submit a PR. Keep changes small and focused.

**License**

- No license included. Add a `LICENSE` file if you want to make reuse terms explicit.

**Contact / Notes**

- This README is intentionally concise. If you want, I can expand the usage examples, add exact CLI flags, or generate a `README` section documenting each script's arguments.
