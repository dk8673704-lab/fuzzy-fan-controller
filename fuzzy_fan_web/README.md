# Fuzzy Fan Controller - Web Version

This project converts the original Tkinter fuzzy fan controller into a browser-based Flask application.

## Run locally

1. Install Python 3.10+.
2. Open this folder in VS Code.
3. Open Terminal and run:

```bash
python -m venv venv
```

Windows:

```bash
venv\\Scripts\\activate
```

Then:

```bash
pip install -r requirements.txt
python app.py
```

4. Open the address shown by Flask, normally `http://127.0.0.1:5000`.

## Deploy for a shareable link

Recommended simple setup:

1. Create a GitHub repository.
2. Upload all project files to the repository.
3. Create a Render Web Service from the GitHub repository.
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. After deployment, Render gives you a public `https://...` URL.

For Render, add `gunicorn` to requirements.txt if using the start command above.
