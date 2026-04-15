"""
YouTube Uploader Agent
Handles OAuth 2.0 authentication and video uploading to YouTube via the Data API v3.
"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')


def get_authenticated_service():
    """Authenticates with YouTube and returns an API service object."""
    creds = None
    token_path = os.path.join(CONFIG_DIR, 'token.json')
    secrets_path = os.path.join(CONFIG_DIR, 'client_secrets.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(secrets_path):
                print(f"Error: client_secrets.json not found in {CONFIG_DIR}")
                exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('youtube', 'v3', credentials=creds)


def upload_video(youtube, file_path, title, description, tags, privacy_status="public"):
    """Uploads a video to YouTube and returns the video ID."""
    print(f"  [Upload] Preparing: {file_path}")

    if not os.path.exists(file_path):
        print(f"  [Upload] Error: '{file_path}' not found.")
        return None

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22'  # People & Blogs
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/*')
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  [Upload] {int(status.progress() * 100)}%")

    video_id = response['id']
    print(f"  [Upload] Success! https://youtu.be/{video_id}")
    return video_id
