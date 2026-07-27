"""
🌾 وحدة LLM (Large Language Models) - SmartAgri

تحتوي على جميع مكونات التواصل مع النماذج اللغوية الكبيرة للمجال الزراعي
"""

from .groq_client import GroqClient

# تعريف ما يتم تصديره عند استيراد الوحدة
__all__ = [
    'GroqClient'
]

# معلومات الوحدة
__version__ = "1.0.0"
__description__ = "SmartAgri LLM Module - التواصل مع النماذج اللغوية للزراعة"

# قائمة النماذج المدعومة
SUPPORTED_MODELS = {
    "groq": {
        "name": "Groq",
        "provider": "Groq",
        "default_model": "llama-3.3-70b-versatile",
        "description": "نموذج Llama عبر منصة Groq - للمجال الزراعي"
    }
}

# وصف المكونات
COMPONENTS = {
    "groq_client": "عميل Groq API للتوليد الزراعي"
}
