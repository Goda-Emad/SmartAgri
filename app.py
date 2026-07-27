import streamlit as st
import sys
import os
import uuid
import asyncio
from pathlib import Path

# إدراج المسار الرئيسي للتطبيق
sys.path.append(str(Path(__file__).parent))

from components.sidebar import render_sidebar
from core.config import settings
from utils.logger import logger

# ============================================================
# ⚙️ إعدادات الصفحة الرئيسية
# ============================================================
st.set_page_config(
    page_title="SmartAgri | المنصة الزراعية الذكية",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 🌐 قاموس النصوص المترجمة للواجهة الرئيسية
# ============================================================
HOME_TRANSLATIONS = {
    "ar": {
        "badge": "🌿 نظام استرجاع المعرفة الزراعية V2.5",
        "hero_title": "مرحباً بك في منصة SmartAgri 🌾",
        "hero_desc": "مساعدك الذكي لاسترجاع المعرفة الزراعية، تحليل المحاصيل والتربة والري، والإجابة الدقيقة بناءً على قاعدة معرفتك الزراعية.",
        "stat_docs": "📄 إجمالي المستندات",
        "stat_suppliers": "🌱 المزارع",
        "stat_contracts": "🌾 المحاصيل",
        "stat_quality": "⭐ دقة التوصيات",
        "guide_title": "🚀 الدليل السريع للبدء",
        "guide_chat": "**💬 المساعد الذكي:** اطرح الأسئلة حول المحاصيل، التربة، الري، والأسمدة للحصول على إجابات معززة بالمصادر.",
        "guide_docs": "**📁 أرشيف المعرفة الزراعية:** استعراض ومعاينة كافة الملفات والمستندات الموجودة بالفهرس.",
        "guide_analytics": "**📊 لوحة التحليلات:** الاطلاع على تحليلات دقيقة وإحصائيات المزارع والمحاصيل بشكل بياني.",
        "btn_start_chat": "💬 ابدأ المحادثة الآن",
        "features_title": "✨ ميزات المنصة",
        "feat_1": "🔍 بحث دلالي (Semantic Search)",
        "feat_2": "⚡ معالجة فائقة السرعة مع Groq API",
        "feat_3": "🔒 حماية وأمان كامل للبيانات",
        "feat_4": "🌙 دعم كلي للوضع الليلي والنهار",
        "sys_info_title": "⚙️ معلومات وبيئة التشغيل"
    },
    "en": {
        "badge": "🌿 AI AGRICULTURAL KNOWLEDGE SYSTEM V2.5",
        "hero_title": "Welcome to SmartAgri Platform 🌾",
        "hero_desc": "Your AI assistant for agricultural knowledge retrieval, crop, soil, and irrigation analysis, and accurate Q&A based on your agricultural knowledge base.",
        "stat_docs": "📄 Total Documents",
        "stat_suppliers": "🌱 Farms",
        "stat_contracts": "🌾 Crops",
        "stat_quality": "⭐ Recommendation Accuracy",
        "guide_title": "🚀 Quick Start Guide",
        "guide_chat": "**💬 AI Assistant:** Ask questions about crops, soil, irrigation, and fertilizers to get source-backed answers.",
        "guide_docs": "**📁 Agricultural Knowledge Archive:** Browse and preview all indexed files and documents.",
        "guide_analytics": "**📊 Analytics Dashboard:** View detailed analytics and visual farm and crop statistics.",
        "btn_start_chat": "💬 Start Chatting Now",
        "features_title": "✨ Platform Features",
        "feat_1": "🔍 Semantic Search Integration",
        "feat_2": "⚡ Ultra-fast processing via Groq API",
        "feat_3": "🔒 End-to-end Data Privacy & Security",
        "feat_4": "🌙 Full Light & Dark Theme Support",
        "sys_info_title": "⚙️ System & Environment Info"
    }
}

# ============================================================
# 🎨 تحسين التنسيقات وإخفاء قائمة Streamlit الافتراضية - Green Theme
# ============================================================
def load_css():
    """تحميل التنسيقات مع إخفاء قائمة التنقل الافتراضية لـ Streamlit وتحسين كروت الإحصائيات"""
    st.markdown("""
        <style>
        /* 🚫 إخفاء قائمة التنقل الافتراضية التي يولدها Streamlit */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        
        /* 🌿 Green Theme - Hero Section */
        .hero-banner {
            background: rgba(46, 125, 50, 0.05);
            border: 1px solid rgba(46, 125, 50, 0.2);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
        }
        
        /* 🌿 Green Theme - بطاقات الإحصائيات */
        .metric-card {
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 14px;
            padding: 1.2rem;
            text-align: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            border-color: #2E7D32;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #2E7D32;
            margin-top: 0.2rem;
        }
        .metric-label {
            font-size: 0.85rem;
            font-weight: 600;
            opacity: 0.85;
        }
        </style>
    """, unsafe_allow_html=True)

    css_file = Path(__file__).parent / "styles" / "custom.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================================
# 🔄 تهيئة حالة الجلسة (Session State)
# ============================================================
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"
    if "stats" not in st.session_state:
        st.session_state.stats = {
            "documents": 13,
            "suppliers": 5,
            "contracts": 5,
            "quality": 85.0
        }

init_session_state()

# ============================================================
# ⚡ بناء الفهرس الذكي تلقائياً (باستخدام Chroma)
# ============================================================
@st.cache_resource(show_spinner="⏳ Checking & Building Chroma Index...")
def build_index_if_needed():
    from database.chroma_loader import ChromaLoader
    
    chroma_loader = ChromaLoader()
    
    if chroma_loader.get_index_size() > 0:
        logger.info(f"✅ Chroma index already exists with {chroma_loader.get_index_size()} documents")
        return True
    
    logger.info("🌿 Building Chroma index for SmartAgri...")
    try:
        from scripts.build_index import build_index
        
        # معالجة حلقة الأحداث آمنة لمواضيع Streamlit
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(build_index())
        return result
    except Exception as e:
        logger.error(f"❌ Index build failed: {e}")
        return False

build_index_if_needed()

# ============================================================
# 🏠 الصفحة الرئيسية - Modern Dashboard UI
# ============================================================
def show_home():
    """عرض الواجهة الرئيسية العصرية للتطبيق"""
    
    # ✅ عرض السايدبار الموحد
    current_lang = render_sidebar(
        stats=st.session_state.stats,
        show_theme_toggle=True,
        show_stats=False,
        show_navigation=True
    )
    
    # جلب ترجمة الواجهة بناءً على اللغة المحددة
    T = HOME_TRANSLATIONS.get(current_lang, HOME_TRANSLATIONS["ar"])

    # 🌐 تطبيق الاتجاه RTL تلقائياً عند استخدام اللغة العربية
    if current_lang == "ar":
        st.markdown("""
            <style>
                .stApp { direction: rtl; text-align: right; }
            </style>
        """, unsafe_allow_html=True)

    # 1. Hero Banner ترحيبي
    st.markdown(f"""
    <div class="hero-banner">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="background: rgba(46, 125, 50, 0.15); color: #2E7D32; font-size: 0.75rem; font-weight: 800; padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(46, 125, 50, 0.3);">
                {T['badge']}
            </span>
        </div>
        <h1 style="font-weight: 800; font-size: 2.1rem; margin: 0 0 10px 0;">
            {T['hero_title']}
        </h1>
        <p style="font-size: 0.98rem; line-height: 1.6; margin: 0;">
            {T['hero_desc']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. بطاقات الإحصائيات (Metrics Bar)
    stats = st.session_state.stats
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{T['stat_docs']}</div>
            <div class="metric-value">{stats.get('documents', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{T['stat_suppliers']}</div>
            <div class="metric-value">{stats.get('suppliers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{T['stat_contracts']}</div>
            <div class="metric-value">{stats.get('contracts', 0)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{T['stat_quality']}</div>
            <div class="metric-value">{stats.get('quality', 0):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. قسم خيارات الوصول السريع والتوجيه
    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown(f"### {T['guide_title']}")
        st.markdown(f"- {T['guide_chat']}")
        st.markdown(f"- {T['guide_docs']}")
        st.markdown(f"- {T['guide_analytics']}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(T['btn_start_chat'], use_container_width=True, type="primary"):
            st.switch_page("pages/1_Chat.py")

    with col_side:
        st.markdown(f"### {T['features_title']}")
        st.markdown(f"- {T['feat_1']}")
        st.markdown(f"- {T['feat_2']}")
        st.markdown(f"- {T['feat_3']}")
        st.markdown(f"- {T['feat_4']}")

    st.markdown("---")

    # 4. تفاصيل ومعلومات النظام (System Status)
    with st.expander(T['sys_info_title'], expanded=False):
        ec1, ec2 = st.columns(2)
        with ec1:
            st.code(f"Chroma Path: {settings.CHROMA_PATH}", language="text")
            st.code(f"Docs Path: {settings.KNOWLEDGE_BASE_PATH}", language="text")
        with ec2:
            st.code(f"LLM Model: {settings.GROQ_MODEL}", language="text")
            st.code(f"Embeddings: {settings.EMBEDDING_MODEL}", language="text")

# ============================================================
# 🚀 تشغيل التطبيق
# ============================================================
if __name__ == "__main__":
    show_home()
