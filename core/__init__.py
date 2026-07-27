# app/core/__init__.py
"""
🌾⚙️ النواة الأساسية - Core Module - SmartAgri

تحتوي على الإعدادات الأساسية والثوابت والنماذج التوجيهية للتطبيق الزراعي
"""

from .config import settings
from .prompts import (
    RAG_PROMPTS,
    SYSTEM_PROMPTS,
    get_prompt,
    get_rag_prompt,
    get_system_prompt,
    get_question_prompt,
    get_comparison_prompt,
    get_summary_prompt,
    get_analysis_prompt
)
from .constants import (
    APP_NAME,
    APP_VERSION,
    SUPPORTED_FILE_TYPES,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_TOP_K,
    DEFAULT_MAX_SOURCES,
    DEFAULT_TEMPERATURE,
    MIN_CONFIDENCE_SCORE,
    CATEGORIES,
    FILE_EXTENSIONS,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE
)

# تعريف ما يتم تصديره عند استيراد الوحدة
__all__ = [
    # الإعدادات
    'settings',
    
    # النماذج التوجيهية
    'RAG_PROMPTS',
    'SYSTEM_PROMPTS',
    'get_prompt',
    'get_rag_prompt',
    'get_system_prompt',
    'get_question_prompt',
    'get_comparison_prompt',
    'get_summary_prompt',
    'get_analysis_prompt',
    
    # الثوابت
    'APP_NAME',
    'APP_VERSION',
    'SUPPORTED_FILE_TYPES',
    'DEFAULT_CHUNK_SIZE',
    'DEFAULT_TOP_K',
    'DEFAULT_MAX_SOURCES',
    'DEFAULT_TEMPERATURE',
    'MIN_CONFIDENCE_SCORE',
    'CATEGORIES',
    'FILE_EXTENSIONS',
    'ALLOWED_EXTENSIONS',
    'MAX_FILE_SIZE'
]

# معلومات الوحدة
__version__ = "1.0.0"
__description__ = "SmartAgri Core Module - الإعدادات الأساسية والثوابت الزراعية"

# تعريف المكونات الأساسية
CORE_COMPONENTS = {
    "config": "إعدادات التطبيق من ملف .env - SmartAgri",
    "prompts": "النماذج التوجيهية للنماذج اللغوية الزراعية",
    "constants": "الثوابت والإعدادات الافتراضية الزراعية"
}
