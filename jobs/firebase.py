# jobs/firebase.py
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os


# Singleton pattern để đảm bảo khởi tạo Firebase chỉ một lần
class FirebaseManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not FirebaseManager._initialized:
            try:
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                firebase_admin.initialize_app(cred)
                FirebaseManager._initialized = True
            except (ValueError, firebase_admin.exceptions.FirebaseError) as e:
                # Xử lý trường hợp đã khởi tạo hoặc lỗi
                if "already exists" not in str(e):
                    print(f"Firebase initialization error: {e}")


firebase_manager = FirebaseManager()


def send_push_notification(token, title, body, data=None):
    """
    Gửi push notification đến một thiết bị cụ thể

    Args:
        token (str): FCM registration token
        title (str): Tiêu đề thông báo
        body (str): Nội dung thông báo
        data (dict, optional): Dữ liệu bổ sung

    Returns:
        dict: Kết quả gửi thông báo
    """
    try:
        # Ensure data is a dictionary
        if data is None:
            data = {}

        # Ensure all values in data are strings
        for key, value in data.items():
            data[key] = str(value)

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data,
            token=token,
        )

        response = messaging.send(message)
        return {
            'success': True,
            'message_id': response
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def send_multicast_notification(tokens, title, body, data=None):
    """
    Gửi push notification đến nhiều thiết bị

    Args:
        tokens (list): Danh sách FCM registration tokens
        title (str): Tiêu đề thông báo
        body (str): Nội dung thông báo
        data (dict, optional): Dữ liệu bổ sung

    Returns:
        dict: Kết quả gửi thông báo
    """
    try:
        if not tokens:
            return {'success': False, 'error': 'No tokens provided'}

        # Ensure data is a dictionary
        if data is None:
            data = {}

        # Ensure all values in data are strings
        for key, value in data.items():
            data[key] = str(value)

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data,
            tokens=tokens,
        )

        response = messaging.send_multicast(message)
        return {
            'success': True,
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }