"""
🌾 إعدادات تطبيق SmartAgri - Application Configuration

يقرأ الإعدادات من Streamlit Secrets (على الكلاود) أو من متغيرات البيئة (محليًا)
بدون أي اعتماد على مكتبة dotenv
"""

import os
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any


def get_secret(key: str, default: str = "") -> str:
    """
    يقرأ القيمة من st.secrets أولاً (شغال محلي وعلى Cloud لو فيه secrets.toml)
    ولو مش موجودة، يرجع لمتغيرات البيئة العادية (os.environ)
    وده بيلغي الحاجة لمكتبة dotenv خالص
    """
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


class Settings:
    """
    إعدادات التطبيق
    يتم قراءة جميع الإعدادات من Streamlit Secrets أو متغيرات البيئة
    """

    # ============================================================
    # 🔑 مفاتيح API
    # ============================================================

    # Groq API (وليس Grok/xAI - انتبه للاسم)
    GROQ_API_KEY: str = get_secret("GROQ_API_KEY", "")
    GROQ_MODEL: str = get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_API_URL: str = get_secret(
        "GROQ_API_URL",
        "https://api.groq.com/openai/v1/chat/completions"
    )

    # ============================================================
    # 📁 مسارات الملفات
    # ============================================================

    # ⚠️ ملحوظة: core/ دلوقتي في الروت مباشرة (مش جوه app/) لذلك parent.parent فقط
    BASE_DIR: Path = Path(__file__).parent.parent

    KNOWLEDGE_BASE_PATH: Path = Path(get_secret("KNOWLEDGE_BASE_PATH", "./knowledge_base"))
    FAISS_INDEX_PATH: Path = Path(get_secret("FAISS_INDEX_PATH", "./faiss_index"))  # ✅ سيتم إزالته لاحقاً
    DATA_PATH: Path = Path(get_secret("DATA_PATH", "./data"))
    LOGS_PATH: Path = Path(get_secret("LOGS_PATH", "./data/logs"))
    
    # ✅ مسار قاعدة بيانات Chroma (جديد)
    CHROMA_PATH: Path = Path(get_secret("CHROMA_PATH", "./chroma_db"))

    # ============================================================
    # 📊 إعدادات RAG
    # ============================================================

    DEFAULT_TOP_K: int = int(get_secret("DEFAULT_TOP_K", "10"))
    DEFAULT_MAX_SOURCES: int = int(get_secret("DEFAULT_MAX_SOURCES", "3"))
    DEFAULT_TEMPERATURE: float = float(get_secret("DEFAULT_TEMPERATURE", "0.7"))
    MIN_CONFIDENCE_SCORE: float = float(get_secret("MIN_CONFIDENCE_SCORE", "0.3"))

    CHUNK_SIZE: int = int(get_secret("CHUNK_SIZE", "300"))
    CHUNK_OVERLAP: int = int(get_secret("CHUNK_OVERLAP", "50"))
    MIN_CHUNK_SIZE: int = int(get_secret("MIN_CHUNK_SIZE", "50"))

    # ============================================================
    # 🧬 إعدادات المتجهات (Embeddings)
    # ============================================================

    EMBEDDING_MODEL: str = get_secret(
        "EMBEDDING_MODEL",
        "paraphrase-multilingual-MiniLM-L12-v2"
    )
    EMBEDDING_DEVICE: str = get_secret("EMBEDDING_DEVICE", "cpu")
    EMBEDDING_BATCH_SIZE: int = int(get_secret("EMBEDDING_BATCH_SIZE", "32"))
    EMBEDDING_DIMENSION: int = int(get_secret("EMBEDDING_DIMENSION", "384"))

    # ============================================================
    # 🖥️ إعدادات التطبيق
    # ============================================================

    APP_NAME: str = get_secret("APP_NAME", "SmartAgri")
    APP_VERSION: str = get_secret("APP_VERSION", "1.0.0")
    ENVIRONMENT: str = get_secret("ENVIRONMENT", "production")
    DEBUG: bool = get_secret("DEBUG", "False").lower() == "true"

    # ============================================================
    # 📝 إعدادات التسجيل (Logging)
    # ============================================================

    LOG_LEVEL: str = get_secret("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = get_secret(
        "LOG_FORMAT",
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    LOG_FILE: str = get_secret("LOG_FILE", "data/logs/app.log")
    LOG_MAX_SIZE: int = int(get_secret("LOG_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(get_secret("LOG_BACKUP_COUNT", "5"))

    # ============================================================
    # 📄 إعدادات المستندات
    # ============================================================

    MAX_FILE_SIZE: int = int(get_secret("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: List[str] = get_secret(
        "ALLOWED_EXTENSIONS",
        ".txt,.docx,.pdf"
    ).split(",")

    # ============================================================
    # 🔒 إعدادات الأمان (اختياري)
    # ============================================================

    SECRET_KEY: str = get_secret("SECRET_KEY", "your-secret-key-change-in-production")

    RATE_LIMIT_REQUESTS: int = int(get_secret("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(get_secret("RATE_LIMIT_PERIOD", "60"))

    # ============================================================
    # 🧪 إعدادات الاختبار (اختياري)
    # ============================================================

    TESTING: bool = get_secret("TESTING", "False").lower() == "true"

    # ============================================================
    # طرق مساعدة
    # ============================================================

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    def is_testing(self) -> bool:
        return self.TESTING or self.ENVIRONMENT.lower() == "testing"

    def get_allowed_extensions(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS if ext.strip()]

    def get_embedding_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.EMBEDDING_MODEL,
            "device": self.EMBEDDING_DEVICE,
            "batch_size": self.EMBEDDING_BATCH_SIZE,
            "dimension": self.EMBEDDING_DIMENSION
        }

    def get_rag_config(self) -> Dict[str, Any]:
        return {
            "top_k": self.DEFAULT_TOP_K,
            "max_sources": self.DEFAULT_MAX_SOURCES,
            "temperature": self.DEFAULT_TEMPERATURE,
            "min_confidence": self.MIN_CONFIDENCE_SCORE,
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP
        }

    def get_llm_config(self) -> Dict[str, Any]:
        return {
            "api_key": self.GROQ_API_KEY,
            "model": self.GROQ_MODEL,
            "api_url": self.GROQ_API_URL
        }

    def get_paths(self) -> Dict[str, Path]:
        return {
            "base": self.BASE_DIR,
            "knowledge_base": self.KNOWLEDGE_BASE_PATH,
            "faiss_index": self.FAISS_INDEX_PATH,
            "chroma_path": self.CHROMA_PATH,  # ✅ إضافة مسار Chroma
            "data": self.DATA_PATH,
            "logs": self.LOGS_PATH
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "GROQ_API_KEY": "***" if self.GROQ_API_KEY else "",
            "GROQ_MODEL": self.GROQ_MODEL,
            "GROQ_API_URL": self.GROQ_API_URL,
            "KNOWLEDGE_BASE_PATH": str(self.KNOWLEDGE_BASE_PATH),
            "FAISS_INDEX_PATH": str(self.FAISS_INDEX_PATH),
            "CHROMA_PATH": str(self.CHROMA_PATH),  # ✅ إضافة Chroma
            "DATA_PATH": str(self.DATA_PATH),
            "LOGS_PATH": str(self.LOGS_PATH),
            "DEFAULT_TOP_K": self.DEFAULT_TOP_K,
            "DEFAULT_MAX_SOURCES": self.DEFAULT_MAX_SOURCES,
            "DEFAULT_TEMPERATURE": self.DEFAULT_TEMPERATURE,
            "MIN_CONFIDENCE_SCORE": self.MIN_CONFIDENCE_SCORE,
            "CHUNK_SIZE": self.CHUNK_SIZE,
            "CHUNK_OVERLAP": self.CHUNK_OVERLAP,
            "EMBEDDING_MODEL": self.EMBEDDING_MODEL,
            "EMBEDDING_DEVICE": self.EMBEDDING_DEVICE,
            "EMBEDDING_BATCH_SIZE": self.EMBEDDING_BATCH_SIZE,
            "EMBEDDING_DIMENSION": self.EMBEDDING_DIMENSION,
            "APP_NAME": self.APP_NAME,
            "APP_VERSION": self.APP_VERSION,
            "ENVIRONMENT": self.ENVIRONMENT,
            "DEBUG": self.DEBUG,
            "MAX_FILE_SIZE": self.MAX_FILE_SIZE,
            "ALLOWED_EXTENSIONS": self.ALLOWED_EXTENSIONS,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_FILE": self.LOG_FILE,
        }


# ============================================================
# إنشاء كائن الإعدادات
# ============================================================

settings = Settings()


# ============================================================
# التحقق من الإعدادات عند بدء التشغيل
# ============================================================

def validate_settings():
    """
    التحقق من صحة الإعدادات عند بدء التشغيل
    """
    if not settings.GROQ_API_KEY:
        print("⚠️ تحذير: GROQ_API_KEY غير موجود")
        print("   محليًا: أضفه في .streamlit/secrets.toml")
        print("   على Streamlit Cloud: أضفه من Manage app → Settings → Secrets")

    directories = [
        settings.KNOWLEDGE_BASE_PATH,
        settings.FAISS_INDEX_PATH,
        settings.CHROMA_PATH,  # ✅ إضافة Chroma
        settings.DATA_PATH,
        settings.LOGS_PATH
    ]

    for dir_path in directories:
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ تعذر إنشاء المجلد {dir_path}: {e}")

    if settings.is_production():
        print("🚀 تشغيل في بيئة إنتاجية")
    elif settings.is_development():
        print("🛠️ تشغيل في بيئة تطويرية")
    elif settings.is_testing():
        print("🧪 تشغيل في بيئة اختبارية")

    print(f"🌾 {settings.APP_NAME} v{settings.APP_VERSION}")


validate_settings()
