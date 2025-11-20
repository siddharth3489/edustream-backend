# ----------------------------------------------------
# EduStream Backend - FINAL & FULLY FIXED
# For project: edustream-2ab24
# ----------------------------------------------------

import os
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests

# ----------------------------------------------------
# Firebase Admin Initialization
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(BASE_DIR, "serviceAccountKey_cloud.json")

cred = credentials.Certificate(KEY_PATH)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Your Web API Key
FIREBASE_API_KEY = "AIzaSyBQEd3pUensBqgTIIZ2sUQHQHBRDFbLnac"

# ----------------------------------------------------
# Flask + CORS
# ----------------------------------------------------
app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response, 200

# ----------------------------------------------------
# Helpers
# ----------------------------------------------------
def error(msg, code=400):
    return jsonify({"success": False, "error": msg}), code

def log(context, e):
    print(f"\n🔥 ERROR in {context}")
    print(e)
    traceback.print_exc()
    print("\n")

# ----------------------------------------------------
# ROUTES
# ----------------------------------------------------

@app.route("/")
def home():
    return {"message": "EduStream API Running 🚀"}

# ----------------------- REGISTER -----------------------
@app.route("/register", methods=["POST"])
def register():
    try:
        d = request.json
        name = d.get("name", "")
        email = d["email"]
        password = d["password"]

        user = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )

        db.collection("users").document(user.uid).set({
            "uid": user.uid,
            "email": email,
            "name": name,
            "createdAt": datetime.utcnow().isoformat()
        })

        return {"success": True, "uid": user.uid}

    except Exception as e:
        log("REGISTER", e)
        return error(str(e), 500)

# ----------------------- LOGIN ---------------------------
@app.route("/login", methods=["POST"])
def login():
    try:
        d = request.json
        email = d["email"]
        password = d["password"]

        url = (
            "https://identitytoolkit.googleapis.com/v1/accounts:"
            f"signInWithPassword?key={FIREBASE_API_KEY}"
        )

        res = requests.post(url, json={
            "email": email,
            "password": password,
            "returnSecureToken": True
        })

        if res.status_code != 200:
            return error("Invalid login", 401)

        data = res.json()

        return {"success": True, "uid": data["localId"], "idToken": data["idToken"]}

    except Exception as e:
        log("LOGIN", e)
        return error("Login failed", 500)

# ----------------------- VIDEOS --------------------------
@app.route("/videos", methods=["GET"])
def videos():
    try:
        docs = db.collection("videos").stream()
        arr = []
        for doc in docs:
            v = doc.to_dict()
            v["id"] = doc.id
            arr.append(v)

        return {"success": True, "videos": arr}

    except Exception as e:
        log("VIDEOS", e)
        return error("Failed to load videos", 500)

# ----------------------- DOWNLOAD LOG ----------------------
@app.route("/download", methods=["POST"])
def download():
    try:
        d = request.json

        db.collection("downloads").add({
            "uid": d["uid"],
            "lectureId": d["lectureId"],
            "title": d.get("title", ""),
            "src": d.get("src", ""),
            "createdAt": datetime.utcnow().isoformat(),
        })

        return {"success": True}

    except Exception as e:
        log("DOWNLOAD", e)
        return error("Failed to record download", 500)

# ----------------------- DOWNLOAD HISTORY -----------------
@app.route("/downloads", methods=["GET"])
def downloads():
    try:
        uid = request.args.get("uid")
        docs = db.collection("downloads").where("uid", "==", uid).stream()

        arr = []
        for doc in docs:
            x = doc.to_dict()
            x["id"] = doc.id
            arr.append(x)

        return {"success": True, "downloads": arr}

    except Exception as e:
        log("GET DOWNLOADS", e)
        return error("Failed to fetch downloads", 500)

# ----------------------------------------------------
# Run
# ----------------------------------------------------
if __name__ == "__main__":
    print("🔥 EduStream Backend Running on http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=True)