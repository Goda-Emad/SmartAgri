# utils/__init__.py
"""
🌿🛠️ وحدة الأدوات المساعدة - Utils Module - SmartAgri
تحتوي على أدوات ووظائف مساعدة تستخدم في جميع أنحاء التطبيق الزراعي
"""
from .logger import logger, setup_logging
from .file_utils import (
    FileUtils,
    get_file_extension,
    get_file_name,
    get_file_size,
    format_file_size,
    is_file_allowed,
    read_text_file,
    write_text_file,
    create_directory,
    delete_file,
    get_file_hash,
    get_file_info,
    list_files,
    get_available_space,
    safe_filename,
    get_unique_filename
)

__all__ = [
    'logger',
    'setup_logging',
    'FileUtils',
    'get_file_extension',
    'get_file_name',
    'get_file_size',
    'format_file_size',
    'is_file_allowed',
    'read_text_file',
    'write_text_file',
    'create_directory',
    'delete_file',
    'get_file_hash',
    'get_file_info',
    'list_files',
    'get_available_space',
    'safe_filename',
    'get_unique_filename'
]

__version__ = "1.0.0"
__description__ = "SmartAgri Utils Module - أدوات ووظائف مساعدة للزراعة"

UTILS_LIST = {
    "logger": "نظام التسجيل وإدارة السجلات الزراعية",
    "file_utils": "أدوات التعامل مع الملفات الزراعية"
}
