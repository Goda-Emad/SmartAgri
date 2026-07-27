# utils/file_utils.py
"""
📁 أدوات التعامل مع الملفات - File Utilities

مجموعة دوال مساعدة للتعامل مع الملفات: القراءة، الكتابة، الفحص، والتسمية الآمنة
"""

import hashlib
import re
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

from core.config import settings


# ============================================================
# 1. دوال أساسية على المسار
# ============================================================

def get_file_extension(file_path: str) -> str:
    """يرجع امتداد الملف بحروف صغيرة (مع النقطة)، مثال: '.docx'"""
    return Path(file_path).suffix.lower()


def get_file_name(file_path: str, with_extension: bool = True) -> str:
    """يرجع اسم الملف، مع أو بدون الامتداد"""
    p = Path(file_path)
    return p.name if with_extension else p.stem


def get_file_size(file_path: str) -> int:
    """يرجع حجم الملف بالبايت. يرجع 0 لو الملف مش موجود"""
    p = Path(file_path)
    return p.stat().st_size if p.exists() else 0


def format_file_size(size_bytes: int) -> str:
    """يحول الحجم بالبايت لصيغة قابلة للقراءة (KB, MB, GB)"""
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


# ============================================================
# 2. التحقق من الملفات
# ============================================================

def is_file_allowed(file_path: str) -> bool:
    """يتحقق إن امتداد الملف ضمن الامتدادات المسموحة في الإعدادات"""
    ext = get_file_extension(file_path)
    allowed = [e.strip().lower() for e in settings.ALLOWED_EXTENSIONS]
    return ext in allowed


# ============================================================
# 3. القراءة والكتابة
# ============================================================

def read_text_file(file_path: str, encoding: str = "utf-8") -> str:
    """يقرأ محتوى ملف نصي"""
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def write_text_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
    """يكتب محتوى نصي لملف، وينشئ المجلدات الأب لو مش موجودة"""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding=encoding) as f:
        f.write(content)


# ============================================================
# 4. إدارة المجلدات والملفات
# ============================================================

def create_directory(dir_path: str) -> Path:
    """ينشئ مجلد (ومساراته الأب) لو مش موجود، ويرجع الـ Path"""
    p = Path(dir_path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def delete_file(file_path: str) -> bool:
    """يحذف ملف. يرجع True لو نجح، False لو الملف مش موجود أو حصل خطأ"""
    try:
        p = Path(file_path)
        if p.exists():
            p.unlink()
            return True
        return False
    except Exception:
        return False


# ============================================================
# 5. Hash ومعلومات الملف
# ============================================================

def get_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """يحسب الـ hash بتاع محتوى الملف (مفيد لمنع تكرار المستندات في الفهرسة)"""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def get_file_info(file_path: str) -> Dict[str, Any]:
    """يرجع معلومات شاملة عن الملف"""
    p = Path(file_path)
    if not p.exists():
        return {"exists": False, "path": str(p)}

    stat = p.stat()
    return {
        "exists": True,
        "path": str(p),
        "name": p.name,
        "stem": p.stem,
        "extension": p.suffix.lower(),
        "size_bytes": stat.st_size,
        "size_formatted": format_file_size(stat.st_size),
        "modified_time": stat.st_mtime,
        "is_allowed": is_file_allowed(file_path),
    }


def list_files(dir_path: str, extensions: Optional[List[str]] = None, recursive: bool = True) -> List[Path]:
    """يسرد كل الملفات في مجلد، مع إمكانية الفلترة بامتدادات معينة"""
    p = Path(dir_path)
    if not p.exists():
        return []

    pattern = "**/*" if recursive else "*"
    files = [f for f in p.glob(pattern) if f.is_file()]

    if extensions:
        exts = [e.lower() for e in extensions]
        files = [f for f in files if f.suffix.lower() in exts]

    return files


def get_available_space(dir_path: str = ".") -> int:
    """يرجع المساحة المتاحة بالبايت في المسار المحدد"""
    total, used, free = shutil.disk_usage(dir_path)
    return free


# ============================================================
# 6. تسمية آمنة للملفات
# ============================================================

def safe_filename(filename: str) -> str:
    """يحول اسم الملف لصيغة آمنة (بدون رموز ممنوعة في أنظمة الملفات)"""
    name = re.sub(r'[<>:"/\\|?*]', "_", filename)
    name = name.strip().strip(".")
    return name or "unnamed_file"


def get_unique_filename(dir_path: str, filename: str) -> str:
    """
    يرجع اسم ملف فريد جوه المجلد المحدد، بإضافة رقم لو الاسم متكرر
    مثال: report.docx -> report (1).docx لو report.docx موجود بالفعل
    """
    p = Path(dir_path)
    safe_name = safe_filename(filename)
    candidate = p / safe_name

    if not candidate.exists():
        return safe_name

    stem = Path(safe_name).stem
    ext = Path(safe_name).suffix
    counter = 1
    while True:
        new_name = f"{stem} ({counter}){ext}"
        if not (p / new_name).exists():
            return new_name
        counter += 1


# ============================================================
# 7. واجهة موحدة (Class wrapper)
# ============================================================

class FileUtils:
    """
    واجهة موحدة تجمع كل دوال التعامل مع الملفات في مكان واحد
    (بديل اختياري لاستيراد الدوال منفردة)
    """

    get_file_extension = staticmethod(get_file_extension)
    get_file_name = staticmethod(get_file_name)
    get_file_size = staticmethod(get_file_size)
    format_file_size = staticmethod(format_file_size)
    is_file_allowed = staticmethod(is_file_allowed)
    read_text_file = staticmethod(read_text_file)
    write_text_file = staticmethod(write_text_file)
    create_directory = staticmethod(create_directory)
    delete_file = staticmethod(delete_file)
    get_file_hash = staticmethod(get_file_hash)
    get_file_info = staticmethod(get_file_info)
    list_files = staticmethod(list_files)
    get_available_space = staticmethod(get_available_space)
    safe_filename = staticmethod(safe_filename)
    get_unique_filename = staticmethod(get_unique_filename)

