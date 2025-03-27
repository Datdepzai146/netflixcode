from flask import Flask, jsonify
import base64
import os
import pickle
import re
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = Flask(_name_)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

def get_latest_otp():
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", maxResults=10).execute()
    messages = results.get("messages", [])

    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])

        for header in headers:
            if header["name"] == "From" and "netflix.com" in header["value"]:
                parts = payload.get("parts", [])
                for part in parts:
                    if part.get("mimeType") == "text/plain":
                        data = part["body"]["data"]
                        text = base64.urlsafe_b64decode(data).decode("utf-8")
                        otp_match = re.search(r"\b\d{4,6}\b", text)
                        if otp_match:
                            return otp_match.group(0)
    return None

@app.route("/otp", methods=["GET"])
def otp():
    code = get_latest_otp()
    if code:
        return jsonify({"otp": code})
    return jsonify({"error": "Không tìm thấy mã OTP"}), 404

if _name_ == "_main_":
    app.run(host="0.0.0.0", port=5000, debug=True)
