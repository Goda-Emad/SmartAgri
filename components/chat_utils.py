# components/chat_utils.py
"""
💬 أدوات المحادثة - Chat Utilities
دوال مساعدة لعرض مكونات المحادثة في Streamlit
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable
import time


# ============================================================
# 1. عرض رسالة في المحادثة
# ============================================================

def render_chat_message(
    message: Dict[str, Any],
    is_last: bool = False,
    show_sources: bool = True
) -> None:
    role = message.get("role", "user")
    content = message.get("content", "")
    sources = message.get("sources", [])

    with st.chat_message(role):
        st.markdown(content)
        if show_sources and sources and role == "assistant":
            render_sources(sources)


def render_messages(
    messages: List[Dict[str, Any]],
    show_sources: bool = True
) -> None:
    for i, message in enumerate(messages):
        is_last = (i == len(messages) - 1)
        render_chat_message(message, is_last, show_sources)


# ============================================================
# 2. عرض المصادر
# ============================================================

def render_sources(sources: List[Dict[str, Any]]) -> None:
    if not sources:
        return

    with st.expander(f"📎 المصادر ({len(sources)})"):
        for i, source in enumerate(sources, 1):
            filename = source.get("filename", "مصدر غير معروف")
            score = source.get("relevance_score", 0)
            content = source.get("content", "")
            category = source.get("category", "غير مصنف")

            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"**{i}. {filename}**")
                st.caption(f"📂 {category}")
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    st.text(preview)

            with col2:
                score_percent = int(score * 100)
                color = "🟢" if score_percent >= 80 else ("🟡" if score_percent >= 50 else "🔴")
                st.metric("المطابقة", f"{color} {score_percent}%")

            st.divider()


# ============================================================
# 3. عرض الأسئلة المقترحة
# ============================================================

def render_suggested_questions(
    questions: List[str],
    on_click: Optional[Callable[[str], None]] = None,
    cols: int = 2
) -> None:
    if not questions:
        return

    st.markdown("### 💡 أسئلة مقترحة")
    columns = st.columns(cols)

    for i, question in enumerate(questions):
        with columns[i % cols]:
            if st.button(question, use_container_width=True, key=f"suggested_{i}"):
                if on_click:
                    on_click(question)


# ============================================================
# 4. مدخل النص
# ============================================================

def render_chat_input(
    placeholder: str = "اكتب سؤالك هنا...",
    disabled: bool = False,
    key: str = "chat_input"
) -> Optional[str]:
    return st.chat_input(
        placeholder=placeholder,
        disabled=disabled,
        key=key
    )


# ============================================================
# 5-9. رسائل الحالة
# ============================================================

def render_loading_indicator(message: str = "🤔 جاري البحث والتفكير...") -> None:
    with st.spinner(message):
        time.sleep(0.5)


def render_error(message: str) -> None:
    st.error(f"❌ {message}")


def render_success(message: str) -> None:
    st.success(f"✅ {message}")


def render_warning(message: str) -> None:
    st.warning(f"⚠️ {message}")


def render_info(message: str) -> None:
    st.info(f"ℹ️ {message}")


# ============================================================
# 10. بطاقة مصدر مبسطة
# ============================================================

def render_source_card(source: Dict[str, Any]) -> None:
    filename = source.get("filename", "مصدر غير معروف")
    score = source.get("relevance_score", 0)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{filename}**")
    with col2:
        st.caption(f"{int(score * 100)}% مطابقة")


# ============================================================
# 11. شريط التقدم
# ============================================================

def render_progress(progress: float, text: str = "جاري المعالجة...") -> None:
    st.progress(min(max(progress / 100, 0.0), 1.0))
    st.caption(f"{text} ({int(progress)}%)")


# ============================================================
# 12. تنسيق النص - مُصلح (IndexError على السطر الفاضي)
# ============================================================

def format_message_content(content: str) -> str:
    if not content:
        return ""

    lines = content.split("\n")
    formatted = []

    for line in lines:
        if not line.strip():
            formatted.append(line)
        elif line.startswith("## "):
            formatted.append(f"### {line[3:]}")
        elif line.startswith("### "):
            formatted.append(f"#### {line[4:]}")
        elif line.startswith(("- ", "* ")):
            formatted.append(f"• {line[2:]}")
        elif len(line) >= 2 and line[0].isdigit() and "." in line[:3]:
            formatted.append(line)
        else:
            formatted.append(line)

    return "\n".join(formatted)


# ============================================================
# تصدير الدوال
# ============================================================

__all__ = [
    'render_chat_message',
    'render_messages',
    'render_sources',
    'render_suggested_questions',
    'render_chat_input',
    'render_loading_indicator',
    'render_error',
    'render_success',
    'render_warning',
    'render_info',
    'render_source_card',
    'render_progress',
    'format_message_content',
]

