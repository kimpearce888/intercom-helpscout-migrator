from flask import Flask, render_template, request, redirect, session, jsonify
import requests, os, re, time, base64

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecret")

INTERCOM_CLIENT_ID = os.getenv("a8a92a69-ed1a-4535-9242-4ab1a27adfe4")
INTERCOM_CLIENT_SECRET = os.getenv("39f8d42c-c7bc-4a9a-ad69-44a37c66ddb1")
INTERCOM_REDIRECT_URI = os.getenv("INTERCOM_REDIRECT_URI", "https://intercom-helpscout-migrator.onrender.com/oauth/callback")

# In-memory log store
progress_log = []

# -------------------------------
# Helpers
# -------------------------------
def log(msg):
    progress_log.append(msg)
    print(msg, flush=True)

def download_and_replace_images(html, intercom_token, helpscout_key):
    img_urls = re.findall(r'<img[^>]+src="([^"]+)"', html)
    headers = {"Authorization": f"Basic {base64.b64encode((helpscout_key + ':X').encode()).decode()}"}

    for url in img_urls:
        try:
            resp = requests.get(url, headers={"Authorization": f"Bearer {intercom_token}"})
            if resp.status_code != 200: continue

            files = {"file": ("asset.png", resp.content, "image/png")}
            upload = requests.post("https://docsapi.helpscout.net/v1/assets", headers=headers, files=files)
            if upload.status_code == 201:
                html = html.replace(url, upload.json()["asset"]["url"])
                log(f"🖼️ Migrated image {url}")
        except Exception as e:
            log(f"⚠️ Failed image {url}: {e}")
    return html

def migrate_articles(intercom_token, helpscout_key, collection_id):
    headers_intercom = {"Authorization": f"Bearer {intercom_token}", "Accept": "application/json"}
    headers_hs = {
        "Authorization": f"Basic {base64.b64encode((helpscout_key + ':X').encode()).decode()}",
        "Content-Type": "application/json"
    }

    url = "https://api.intercom.io/articles"
    while url:
        r = requests.get(url, headers=headers_intercom)
        data = r.json()

        for art in data.get("data", []):
            title = art.get("title", "Untitled")
            body = art.get("body", "")

            log(f"➡️ Migrating: {title}")
            body = download_and_replace_images(body, intercom_token, helpscout_key)

            payload = {"collectionId": collection_id, "status": "published", "name": title, "text": body}
            resp = requests.post("https://docsapi.helpscout.net/v1/articles", headers=headers_hs, json=payload)

            if resp.status_code not in (200, 201):
                log(f"❌ Failed {title}: {resp.text}")
            else:
                log(f"✅ Migrated: {title}")

            time.sleep(1)

        url = data.get("pages", {}).get("next")

# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/connect")
def connect():
    url = (
        f"https://app.intercom.com/a/oauth/connect?client_id={INTERCOM_CLIENT_ID}"
        f"&redirect_uri={INTERCOM_REDIRECT_URI}&state=xyz"
    )
    return redirect(url)

@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    resp = requests.post("https://api.intercom.io/auth/eagle/token", data={
        "client_id": INTERCOM_CLIENT_ID,
        "client_secret": INTERCOM_CLIENT_SECRET,
        "code": code
    })
    session["intercom_token"] = resp.json().get("access_token")
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/start", methods=["POST"])
def start():
    global progress_log
    progress_log = []

    helpscout_key = request.form["helpscout_key"]
    collection_id = request.form["collection_id"]
    intercom_token = session.get("intercom_token")
    if not intercom_token: return "❌ Not connected to Intercom"

    migrate_articles(intercom_token, helpscout_key, collection_id)
    return "Migration completed!"

@app.route("/progress")
def progress():
    return jsonify({"logs": progress_log})

if __name__ == "__main__":
    app.run(debug=True)
