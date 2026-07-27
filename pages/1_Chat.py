"""
🌾 صفحة المحادثة الزراعية - SmartAgri Chat
تتيح للمستخدم التفاعل المباشر مع الذكاء الاصطناعي واسترجاع المعرفة الزراعية.
"""

import streamlit as st
import sys
import uuid
from pathlib import Path

# إضافة المجلد الرئيسي للتطبيق إلى المسار
sys.path.append(str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.chat_utils import render_sources, render_error
from core.config import settings
from utils.logger import logger

# ============================================================
# ⚙️ إعدادات الصفحة
# ============================================================
st.set_page_config(
    page_title="المساعد الزراعي | SmartAgri",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 🎨 تحميل التنسيقات المخصصة (CSS) - Green Theme 🌿
# ============================================================
def load_css():
    st.markdown("""
        <style>
        .stChatMessage {
            border-radius: 12px !important;
            padding: 1rem !important;
            margin-bottom: 0.8rem !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        .chat-header {
            border-radius: 14px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 1.5rem;
        }
        .chat-header h2 { font-weight: 800; margin: 0 0 6px 0; }
        .chat-header p  { font-size: 0.88rem; margin: 0; }

        /* ✅ Green Theme - أزرار الأسئلة المقترحة */
        div[data-testid="stColumn"] div.stButton > button {
            background: #2E4A2E !important;
            border: 1px solid rgba(46, 125, 50, 0.2) !important;
            color: #C8E6C9 !important;
            border-radius: 10px !important;
            padding: 0.6rem 0.8rem !important;
            font-size: 0.88rem !important;
            text-align: right !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stColumn"] div.stButton > button:hover {
            border-color: #4CAF50 !important;
            color: #4CAF50 !important;
            background: #1B3A1B !important;
            transform: translateY(-2px) !important;
        }

        /* ✅ Green Theme - أزرار التحكم (مسح، تحديث) */
        .stButton > button {
            background: linear-gradient(135deg, #1B5E20, #2E7D32) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 15px rgba(46, 125, 50, 0.3);
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(46, 125, 50, 0.4);
        }

        /* ✅ Green Theme - مدخل النص */
        .stChatInput textarea {
            border: 2px solid #2E7D32 !important;
            border-radius: 12px !important;
            background-color: #FFFFFF !important;
            color: #1B3A1B !important;
            box-shadow: 0 2px 10px rgba(46, 125, 50, 0.1) !important;
        }
        .stChatInput textarea:focus {
            border-color: #1B5E20 !important;
            box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.2) !important;
        }

        /* ✅ Green Theme - نصوص المحادثة */
        .stChatMessage p, .stChatMessage div, .stChatMessage span {
            color: #1B3A1B !important;
        }

        /* ✅ Green Theme - سبينر */
        .stSpinner > div {
            border-color: #2E7D32 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    css_file = Path(__file__).parent.parent / "styles" / "custom.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ============================================================
# ✅ Singleton للـ ChromaLoader — نفس الـ instance في كل الـ app
# ============================================================
@st.cache_resource
def get_chroma_loader():
    from database.chroma_loader import ChromaLoader
    return ChromaLoader()


# ============================================================
# 1. تهيئة خدمة المحادثة — تستخدم نفس الـ ChromaLoader
# ============================================================
@st.cache_resource
def get_chat_service():
    from database.embeddings import Embeddings
    from rag.retriever import Retriever
    from rag.reranker import Reranker
    from llm.groq_client import GroqClient
    from rag.qa_engine import QAEngine
    from services.chat_service import ChatService

    # ✅ نفس الـ singleton — مش instance جديدة
    chroma_loader = get_chroma_loader()

    embeddings = Embeddings(
        model_name=settings.EMBEDDING_MODEL,
        device=settings.EMBEDDING_DEVICE
    )
    retriever = Retriever(chroma_loader=chroma_loader, embeddings=embeddings)
    reranker = Reranker()
    llm = GroqClient()
    qa_engine = QAEngine(retriever=retriever, reranker=reranker, llm=llm)

    return ChatService(qa_engine=qa_engine)


chat_service = get_chat_service()


# ============================================================
# 2. تهيئة حالة الجلسة (Session State)
# ============================================================
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


# ============================================================
# 3. عرض سوابق المحادثة
# ============================================================
def display_messages():
    for message in st.session_state.messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        sources = message.get("sources", [])

        with st.chat_message(role):
            st.markdown(content)
            if sources and role == "assistant":
                render_sources(sources)


# ============================================================
# 4. معالجة سؤال المستخدم
# ============================================================
def process_question(question: str):
    if not question.strip():
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("🤔 جاري البحث في المعرفة الزراعية واستخلاص الإجابة..."):
            try:
                response = chat_service.process_question_sync(
                    question=question,
                    session_id=st.session_state.session_id
                )

                if response.get("session_id"):
                    st.session_state.session_id = response["session_id"]

                answer = response.get("answer", "لم أتمكن من الحصول على إجابة.")
                sources = response.get("sources", [])

                st.markdown(answer)
                if sources:
                    render_sources(sources)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except Exception as e:
                error_msg = f"❌ حدث خطأ أثناء معالجة الطلب: {str(e)}"
                st.error(error_msg)
                logger.error(f"Chat error: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sources": []
                })


# ============================================================
# 5. عرض الأسئلة المقترحة (باللغتين)
# ============================================================
def display_suggested_questions():
    if len(st.session_state.messages) > 0:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🌱 أسئلة زراعية مقترحة للبدء / Suggested Questions:")

    suggestions = [
        "What are the best crop management practices?",
        "What is crop marketing?",
        "What is plant breeding?",
        "How to manage soil?",
        "What are the main crop nutrients?",
        "What is irrigation management?"
    ]

    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"📌 {suggestion}", use_container_width=True, key=f"suggest_{i}"):
                st.session_state.pending_question = suggestion
                st.rerun()


# ============================================================
# 6. الصفحة الرئيسية للمحادثة
# ============================================================
def show():
    load_css()
    init_session_state()

    render_sidebar(
        show_theme_toggle=True,
        show_stats=False,
        show_navigation=True
    )

    col_title, col_actions = st.columns([3, 1.5])

    with col_title:
        st.markdown("""
        <div class="chat-header">
            <h2>🌾 المساعد الزراعي (SmartAgri)</h2>
            <p>طرح الأسئلة والبحث التفاعلي في المحاصيل، التربة، الري، والأسمدة.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_actions:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("🗑️ مسح", use_container_width=True, help="مسح سجل المحادثة الحالي"):
                st.session_state.messages = []
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()
        with ac2:
            if st.button("🔄 تحديث", use_container_width=True, help="تحديث الصفحة"):
                st.rerun()

    st.markdown("---")

    display_messages()

    query_to_process = None

    if st.session_state.pending_question:
        query_to_process = st.session_state.pending_question
        st.session_state.pending_question = None
    elif prompt := st.chat_input("اكتب سؤالك هنا / Ask your question here (English or Arabic)..."):
        query_to_process = prompt

    if query_to_process:
        process_question(query_to_process)
        st.rerun()

    display_suggested_questions()


# ============================================================
# 🚀 تشغيل الصفحة
# ============================================================
if __name__ == "__main__":
    show()
