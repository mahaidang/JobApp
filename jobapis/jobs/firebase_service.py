import firebase_admin
from firebase_admin import credentials, auth, credentials
from django.conf import settings

# Initialize Firebase (chỉ chạy 1 lần)
if not firebase_admin._apps:
    cred = credentials.Certificate("jobs/firebase/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

def generate_firebase_custom_token(uid):
    return auth.create_custom_token(uid)
def generate_chat_id(user_id1, user_id2):
    # Luôn sắp xếp id tăng dần để không bị trùng
    ids = sorted([user_id1, user_id2])
    return f"chat_{ids[0]}_{ids[1]}"




