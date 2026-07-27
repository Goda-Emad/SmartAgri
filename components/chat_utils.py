# database/__init__.py
"""
🗄️ وحدة قاعدة البيانات - Database Module - SmartAgri
تحتوي على جميع مكونات التعامل مع قواعد البيانات والفهارس
"""
from .faiss_loader import FAISSLoader
from .embeddings import Embeddings
from .text_loader import TextLoader
from .docx_loader import DocxLoader
from .chroma_loader import ChromaLoader  # ✅ إضافة ChromaLoader

__all__ = [
    'FAISSLoader',
    'Embeddings',
    'TextLoader',
    'DocxLoader',
    'ChromaLoader',  # ✅ إضافة ChromaLoader
]

__version__ = "1.0.0"
__description__ = "SmartAgri Database Module - إدارة قواعد البيانات والفهارس"

COMPONENTS = {
    "faiss_loader": "تحميل وإدارة فهرس FAISS",
    "chroma_loader": "تحميل وإدارة قاعدة بيانات Chroma",  # ✅ إضافة Chroma
    "embeddings": "توليد المتجهات (Embeddings) للنصوص",
    "text_loader": "تحميل النصوص من ملفات .txt",
    "docx_loader": "تحميل النصوص من ملفات .docx"
}

SUPPORTED_FILE_TYPES = {
    "txt": {
        "description": "ملفات نصية عادية",
        "loader": "TextLoader",
        "icon": "📄"
    },
    "docx": {
        "description": "مستندات Word",
        "loader": "DocxLoader",
        "icon": "📝"
    },
    "pdf": {  # ✅ إضافة PDF
        "description": "ملفات PDF",
        "loader": "PDFLoader",
        "icon": "📕"
    }
}

DATABASE_SETTINGS = {
    "faiss": {
        "index_path": "./faiss_index/index.faiss",
        "metadata_path": "./faiss_index/metadata.pkl",
        "dimension": 384,
        "metric": "L2"
    },
    "chroma": {  # ✅ إضافة إعدادات Chroma
        "path": "./chroma_db",
        "collection_name": "documents"
    },
    "embeddings": {
        "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
        "device": "cpu",
        "batch_size": 32
    }
}
