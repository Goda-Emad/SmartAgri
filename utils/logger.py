# utils/logger.py
"""
🌾📝 نظام التسجيل - Logging System - SmartAgri

يوفر واجهة موحدة للتسجيل في جميع أنحاء التطبيق الزراعي
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from core.config import settings


# ============================================================
# 1. إعدادات التسجيل
# ============================================================

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

DEFAULT_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
DETAILED_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s'
JSON_FORMAT = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'

COLORS = {
    'DEBUG': '\033[94m',
    'INFO': '\033[92m',
    'WARNING': '\033[93m',
    'ERROR': '\033[91m',
    'CRITICAL': '\033[95m',
    'RESET': '\033[0m'
}


# ============================================================
# 2. تنسيقات مخصصة
# ============================================================

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


# ============================================================
# 3. إعدادات التسجيل الرئيسية
# ============================================================

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
    use_colors: bool = True,
    use_json: bool = False
) -> None:
    """
    إعداد نظام التسجيل لـ SmartAgri
    """
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    log_format = log_format or settings.LOG_FORMAT
    max_bytes = max_bytes or settings.LOG_MAX_SIZE
    backup_count = backup_count or settings.LOG_BACKUP_COUNT

    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)

    handlers = []

    # معالج الطرفية (دايمًا شغال)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if use_json:
        console_handler.setFormatter(JSONFormatter())
    elif use_colors:
        console_handler.setFormatter(ColoredFormatter(log_format))
    else:
        console_handler.setFormatter(logging.Formatter(log_format))

    handlers.append(console_handler)

    # معالج الملف - محمي بـ try/except لأن Streamlit Cloud
    # ممكن يكون فيه قيود على الكتابة، والـ logs مش هتتحفظ دائمًا هناك
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except Exception as e:
            print(f"⚠️ تعذر إعداد ملف السجل ({log_file}): {e} - هيتم التسجيل على الطرفية فقط")

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True
    )

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)

    logger = logging.getLogger("SmartAgri")
    logger.info("🌾 SmartAgri Logging system initialized")
    logger.info(f"📊 Log level: {log_level}")
    logger.info(f"📁 Log file: {log_file}")


# ============================================================
# 4. إنشاء كائن المسجل
# ============================================================

def get_logger(name: str = "SmartAgri") -> logging.Logger:
    return logging.getLogger(name)


# ============================================================
# 5. واجهة برمجة التطبيقات
# ============================================================

class Logger:
    """
    واجهة برمجة التطبيقات للتسجيل - SmartAgri
    """

    def __init__(self, name: str = "SmartAgri"):
        self.logger = get_logger(name)

    def debug(self, message: str, *args, **kwargs) -> None:
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        self.logger.exception(message, *args, **kwargs)

    def log(self, level: str, message: str, *args, **kwargs) -> None:
        level = level.upper()
        if level == 'DEBUG':
            self.debug(message, *args, **kwargs)
        elif level == 'INFO':
            self.info(message, *args, **kwargs)
        elif level == 'WARNING':
            self.warning(message, *args, **kwargs)
        elif level == 'ERROR':
            self.error(message, *args, **kwargs)
        elif level == 'CRITICAL':
            self.critical(message, *args, **kwargs)
        else:
            self.info(message, *args, **kwargs)


# ============================================================
# 6. دوال مساعدة إضافية
# ============================================================

def log_function_call(func):
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"🔹 Calling {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"✅ {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ {func.__name__} failed: {str(e)}")
            raise

    return wrapper


def log_async_function_call(func):
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"🔹 Calling async {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"✅ {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ {func.__name__} failed: {str(e)}")
            raise

    return wrapper


def log_exception(exc: Exception, context: Optional[str] = None) -> None:
    logger = get_logger()
    if context:
        logger.error(f"❌ Exception in {context}: {str(exc)}")
    else:
        logger.error(f"❌ Exception: {str(exc)}")
    logger.exception(exc)


# ============================================================
# 7. تهيئة التسجيل تلقائياً
# ============================================================

if not logging.getLogger().handlers:
    setup_logging()


# ============================================================
# 8. إنشاء كائن المسجل الرئيسي
# ============================================================

logger = Logger()

__all__ = [
    'logger',
    'Logger',
    'setup_logging',
    'get_logger',
    'log_function_call',
    'log_async_function_call',
    'log_exception',
    'LOG_LEVELS'
]
