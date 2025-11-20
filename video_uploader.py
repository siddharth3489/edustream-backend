import streamlit as st
from google.cloud import storage
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin
import uuid
import os

# ----------------------------------------------------
# FIREBASE SETUP
# ----------------------------------------------------

KEY_PATH = "serviceAccountKey_cloud.json"   # must be in same folder

BUCKET_NAME = "edustream-2ab24.firebasestorage.app"   # YOUR correct bucket

# 1) Initialize Firebase Admin for Firestore
if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred, {
        "storageBucket": BUCKET_NAME
    })

db = firestore.client()

# 2) Initialize Storage Client
storage_client = storage.Client.from_service_account_json(KEY_PATH)
bucket = storage_client.bucket(BUCKET_NAME)

# ----------------------------------------------------
# STREAMLIT UI
# ----------------------------------------------------

st.title("🎬 EduStream — Video Creator & Editor")
st.markdown("Upload videos + metadata to Firebase Storage and Firestore.")

# ----------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------

def upload_video_to_storage(file):
    """Upload file to Firebase Storage and return public URL."""
    file_id = str(uuid.uuid4())
    blob = bucket.blob(f"videos/{file_id}.mp4")

    # Upload
    blob.upload_from_file(file, content_type="video/mp4")

    # Make public
    blob.make_public()

    return blob.public_url, file_id


def save_video_metadata(doc_id, subject, topic, subtopic, title, url):
    """Save metadata to Firestore."""
    db.collection("videos").document(doc_id).set({
        "subject": subject,
        "topic": topic,
        "subtopic": subtopic,
        "title": title,
        "url": url
    })


def get_all_videos():
    docs = db.collection("videos").stream()
    arr = []
    for d in docs:
        x = d.to_dict()
        x["id"] = d.id
        arr.append(x)
    return arr


def delete_video(doc_id):
    """Delete Firestore metadata only."""
    db.collection("videos").document(doc_id).delete()


# ----------------------------------------------------
# UPLOAD SECTION
# ----------------------------------------------------

st.header("📤 Upload New Video")

with st.form("upload_form"):
    subject = st.text_input("Subject")
    topic = st.text_input("Topic")
    subtopic = st.text_input("Subtopic")
    title = st.text_input("Lecture Title")
    file = st.file_uploader("Select video file (.mp4)", type=["mp4"])

    uploaded = st.form_submit_button("Upload Video")

if uploaded:
    if not (subject and topic and subtopic and title and file):
        st.error("Please fill all fields and select a video.")
    else:
        with st.spinner("Uploading to Firebase…"):
            video_url, video_id = upload_video_to_storage(file)

            save_video_metadata(
                doc_id=video_id,
                subject=subject,
                topic=topic,
                subtopic=subtopic,
                title=title,
                url=video_url
            )

        st.success("Video uploaded successfully!")
        st.video(video_url)
        st.json({
            "subject": subject,
            "topic": topic,
            "subtopic": subtopic,
            "title": title,
            "url": video_url
        })

st.divider()

# ----------------------------------------------------
# EDIT SECTION
# ----------------------------------------------------

st.header("📝 Edit Existing Videos")

videos = get_all_videos()

if not videos:
    st.info("No videos uploaded yet.")
else:
    selected_title = st.selectbox(
        "Select a video",
        options=[v["title"] for v in videos]
    )

    selected_video = next(v for v in videos if v["title"] == selected_title)

    st.video(selected_video["url"])

    st.write("### Current Metadata")
    st.json(selected_video)

    # Editing input fields
    with st.form("edit_form"):
        new_subject = st.text_input("Subject", selected_video["subject"])
        new_topic = st.text_input("Topic", selected_video["topic"])
        new_subtopic = st.text_input("Subtopic", selected_video["subtopic"])
        new_title = st.text_input("Lecture Title", selected_video["title"])

        save_btn = st.form_submit_button("Save Changes")
        delete_btn = st.form_submit_button("❌ Delete Video")

    if save_btn:
        save_video_metadata(
            doc_id=selected_video["id"],
            subject=new_subject,
            topic=new_topic,
            subtopic=new_subtopic,
            title=new_title,
            url=selected_video["url"]
        )
        st.success("Changes saved!")
        st.rerun()

    if delete_btn:
        delete_video(selected_video["id"])
        st.warning("Video deleted!")
        st.rerun()