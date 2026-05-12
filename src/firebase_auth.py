import requests
import json
from datetime import datetime

# Firebase Config - ضع بيانات مشروعك هنا
FIREBASE_CONFIG = {
    "apiKey": "YOUR_API_KEY",
    "projectId": "YOUR_PROJECT_ID",
    "databaseURL": "YOUR_DATABASE_URL"
}

def verify_license(email, license_key):
    """التحقق من صلاحية الترخيص"""
    try:
        # محاكاة Firebase للتطوير
        # في الإنتاج استبدل هذا بـ Firebase Real Database
        test_licenses = {
            "admin@trading.com": {
                "license": "SMC-PRO-2024",
                "status": "Active",
                "plan": "Pro",
                "expiry": "2025-12-31"
            },
            "trader@trading.com": {
                "license": "SMC-BASIC-2024",
                "status": "Active",
                "plan": "Basic",
                "expiry": "2025-06-30"
            }
        }

        if email in test_licenses:
            user = test_licenses[email]
            if user["license"] == license_key:
                return {
                    "success": True,
                    "status": user["status"],
                    "plan": user["plan"],
                    "expiry": user["expiry"],
                    "message": "License verified successfully"
                }
        return {
            "success": False,
            "status": "Inactive",
            "message": "Invalid email or license key"
        }
    except Exception as e:
        return {
            "success": False,
            "status": "Error",
            "message": str(e)
        }

def get_user_plan(email):
    """جلب خطة المستخدم"""
    try:
        plans = {
            "admin@trading.com": "Pro",
            "trader@trading.com": "Basic"
        }
        return plans.get(email, "Free")
    except:
        return "Free"