# app/services/__init__.py
"""
🔧 وحدة الخدمات - Services Module - SmartAgri

تحتوي على جميع خدمات التطبيق (منطق الأعمال) للمجال الزراعي
"""

from .chat_service import ChatService

# تعريف ما يتم تصديره عند استيراد الوحدة
__all__ = [
    'ChatService'
]

# معلومات الوحدة
__version__ = "1.0.0"
__description__ = "SmartAgri Services Module - منطق الأعمال الزراعية"

# وصف الخدمات
SERVICES = {
    "chat_service": "خدمة المحادثة الزراعية - إدارة RAG والرد على الأسئلة الزراعية"
}

# إعدادات الخدمات
SERVICE_DEFAULTS = {
    "chat": {
        "max_history": 50,
        "default_temperature": 0.7,
        "default_top_k": 5
    }
}
