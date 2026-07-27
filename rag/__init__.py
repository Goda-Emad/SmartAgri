# app/rag/__init__.py
"""
🌾 وحدة RAG (Retrieval-Augmented Generation) - SmartAgri

تحتوي على جميع مكونات نظام الاسترجاع والتوليد المدعوم بالاسترجاع للمجال الزراعي
"""

from .retriever import Retriever
from .qa_engine import QAEngine
from .reranker import Reranker
from .chunking import Chunking

# تعريف ما يتم تصديره عند استيراد الوحدة
__all__ = [
    'Retriever',
    'QAEngine',
    'Reranker',
    'Chunking'
]

# معلومات الوحدة
__version__ = "1.0.0"
__description__ = "SmartAgri RAG Module - محرك الاسترجاع والتوليد الزراعي"

# وصف المكونات
COMPONENTS = {
    "retriever": "استرجاع المستندات الزراعية من ChromaDB",
    "qa_engine": "محرك الأسئلة والأجوبة الزراعية (RAG Pipeline)",
    "reranker": "إعادة ترتيب النتائج (Cross-Encoder)",
    "chunking": "تقسيم النصوص الزراعية إلى أجزاء"
}
