# components/sidebar.py
"""
🎨 المكون الموحد للقائمة الجانبية - Sidebar Component
يدير الثيمات (Dark/Light)، اللغات (Ar/En)، وتنسيقات الهيكل العام
🌾 SmartAgri - Barbie Color Palette
"""

import streamlit as st

TRANSLATIONS = {
    "ar": {
        "home": "الصفحة الرئيسية",
        "chat": "المساعد الذكي",
        "docs": "المستندات",
        "analytics": "التحليلات",
        "theme_light": "☀️ وضع فاتح",
        "theme_dark": "🌙 وضع داكن",
        "lang_btn": "🌐 English",
        "brand_subtitle": "🌾 منصة المعرفة الزراعية والذكاء الاصطناعي",
        "stats_title": "📊 الإحصائيات",
        "docs_count": "المستندات",
        "suppliers_count": "🌱 المزارع",
        "contracts_count": "🌾 المحاصيل",
        "quality_rate": "⭐ الإنتاجية"
    },
    "en": {
        "home": "Home",
        "chat": "AI Assistant",
        "docs": "Documents",
        "analytics": "Analytics",
        "theme_light": "☀️ Light Mode",
        "theme_dark": "🌙 Dark Mode",
        "lang_btn": "🌐 العربية",
        "brand_subtitle": "🌾 AI Agricultural Knowledge Platform",
        "stats_title": "📊 Statistics",
        "docs_count": "Documents",
        "suppliers_count": "🌱 Farms",
        "contracts_count": "🌾 Crops",
        "quality_rate": "⭐ Productivity"
    }
}

def apply_dynamic_theme():
    """تطبيق الثيم وإصلاح مشاكل الـ Expander، اتجاه النصوص، والألوان"""
    is_dark = st.session_state.get("dark_mode", True)
    lang = st.session_state.get("lang", "ar")
    is_rtl = (lang == "ar")

    # 🌐 ضبط اتجاه المحاذاة حسب اللغة
    direction_css = f"""
        .stApp, [data-testid="stSidebar"], .stMarkdown, p, h1, h2, h3, h4, h5, h6 {{
            direction: {'rtl' if is_rtl else 'ltr'} !important;
            text-align: {'right' if is_rtl else 'left'} !important;
        }}
    """

    if is_dark:
        # 🌙 Dark Mode - Barbie (Deep Burgundy/Magenta base + Hot Pink accents)
        theme_css = """
            /* 1. خلفيات التطبيق والسايدبار */
            .stApp { background-color: #2B0715 !important; color: #FCE4EC !important; }
            [data-testid="stSidebar"] { background-color: #3D0F24 !important; border-right: 1px solid rgba(224, 33, 138, 0.25) !important; }
            [data-testid="stSidebar"] * { color: #F3C6DC !important; }

            /* 1.b تأكيد إضافي على نصوص الـ Caption في السايدبار
               (لبعض عناصر Streamlit الداخلية قد يكون لها specificity أعلى
               من القاعدة العامة [data-testid="stSidebar"] * أعلاه) */
            [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
            [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
                color: #F3C6DC !important;
            }

            /* 2. الهيدر والبانر الرئيسي (hero-banner + chat-header + doc-header) */
            .hero-banner, .chat-header, .doc-header {
                background: linear-gradient(135deg, #4A0E2E 0%, #2B0715 100%) !important;
                border: 1px solid rgba(224, 33, 138, 0.35) !important;
                border-radius: 16px !important;
                padding: 1.8rem !important;
                margin-bottom: 1.5rem !important;
            }
            .hero-banner h1, .hero-banner p,
            .chat-header h2, .chat-header p,
            .doc-header h2, .doc-header p { color: #FFFFFF !important; }

            /* 3. بطاقات الإحصائيات المخصصة (HTML - metric-card) */
            .metric-card {
                background: #3D0F24 !important;
                border: 1px solid rgba(224, 33, 138, 0.2) !important;
                border-radius: 12px !important;
                padding: 1rem !important;
                text-align: center !important;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25) !important;
            }
            .metric-value { color: #E0218A !important; font-size: 1.8rem !important; font-weight: 800 !important; }
            .metric-label { color: #F3C6DC !important; font-size: 0.85rem !important; font-weight: 600 !important; }

            /* 3.b مقاييس Streamlit الأصلية (st.metric) في محتوى الصفحة
               ملحوظة: النسخ الحديثة من Streamlit بتستخدم data-testid بدل
               الكلاسات القديمة (.stMetric)، فبنستهدفها هنا مباشرة عشان
               تاخد ألوان واضحة في الـ Dark Mode بدل اللون الافتراضي الغامق */
            [data-testid="stMetric"] {
                background: #3D0F24 !important;
                border: 1px solid rgba(224, 33, 138, 0.2) !important;
                border-radius: 12px !important;
                padding: 1rem !important;
            }
            [data-testid="stMetricLabel"],
            [data-testid="stMetricLabel"] p {
                color: #F3C6DC !important;
            }
            [data-testid="stMetricValue"],
            [data-testid="stMetricValue"] div {
                color: #FFFFFF !important;
            }

            /* 4. إصلاح مشكلة الـ Expander الأبيض في الأسفل */
            div[data-testid="stExpander"] {
                background-color: #3D0F24 !important;
                border: 1px solid rgba(224, 33, 138, 0.25) !important;
                border-radius: 12px !important;
            }
            div[data-testid="stExpander"] details {
                background-color: #3D0F24 !important;
                color: #FCE4EC !important;
                border-radius: 12px !important;
            }
            div[data-testid="stExpander"] summary {
                background-color: #4A0E2E !important;
                color: #FCE4EC !important;
                border-radius: 12px !important;
            }
            div[data-testid="stExpander"] summary:hover {
                color: #E0218A !important;
            }

            /* 5. الأزرار الموحدة (Barbie Pink بدل الأزرق) */
            .stButton > button[kind="primary"] {
                background: linear-gradient(90deg, #C2185B 0%, #E0218A 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
                font-weight: 700 !important;
                border-radius: 10px !important;
            }
            .stButton > button {
                background-color: #4A0E2E !important;
                color: #FCE4EC !important;
                border: 1px solid rgba(224, 33, 138, 0.3) !important;
                border-radius: 10px !important;
            }
            .stButton > button:hover {
                border-color: #E0218A !important;
                color: #E0218A !important;
            }
        """
    else:
        # ☀️ Light Mode - Barbie الأصلي
        theme_css = """
            .stApp { background-color: #FCE4EC !important; color: #4A0E2E !important; }
            [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #F8BBD0 !important; }
            [data-testid="stSidebar"] * { color: #4A0E2E !important; }

            [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
            [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
                color: #4A0E2E !important;
            }

            .hero-banner, .chat-header, .doc-header {
                background: linear-gradient(135deg, #FCE4EC 0%, #F8BBD0 100%) !important;
                border: 1px solid #E0218A !important;
                border-radius: 16px !important;
                padding: 1.8rem !important;
            }
            .hero-banner h1, .hero-banner p,
            .chat-header h2, .chat-header p,
            .doc-header h2, .doc-header p { color: #4A0E2E !important; }

            .metric-card {
                background-color: #FFFFFF !important;
                border: 1px solid #F8BBD0 !important;
                border-radius: 12px !important;
                padding: 1rem !important;
                text-align: center !important;
                box-shadow: 0 2px 8px rgba(194, 24, 91, 0.08) !important;
            }
            .metric-value { color: #E0218A !important; font-size: 1.8rem !important; font-weight: 800 !important; }
            .metric-label { color: #C2185B !important; font-size: 0.85rem !important; }

            [data-testid="stMetric"] {
                background-color: #FFFFFF !important;
                border: 1px solid #F8BBD0 !important;
                border-radius: 12px !important;
                padding: 1rem !important;
            }
            [data-testid="stMetricLabel"],
            [data-testid="stMetricLabel"] p {
                color: #C2185B !important;
            }
            [data-testid="stMetricValue"],
            [data-testid="stMetricValue"] div {
                color: #4A0E2E !important;
            }

            div[data-testid="stExpander"] {
                background-color: #FFFFFF !important;
                border: 1px solid #F8BBD0 !important;
                border-radius: 12px !important;
            }
            div[data-testid="stExpander"] summary {
                background-color: #FCE4EC !important;
                color: #4A0E2E !important;
            }
            div[data-testid="stExpander"] summary:hover {
                color: #E0218A !important;
            }

            .stButton > button[kind="primary"] {
                background: linear-gradient(90deg, #C2185B 0%, #E0218A 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
                font-weight: 700 !important;
                border-radius: 10px !important;
            }
            .stButton > button {
                background-color: #FFFFFF !important;
                color: #4A0E2E !important;
                border: 1px solid #F8BBD0 !important;
                border-radius: 10px !important;
            }
            .stButton > button:hover {
                border-color: #E0218A !important;
                color: #E0218A !important;
            }
        """

    # 🛠️ إصلاح نصوص الأيقونات التي تسربت أعلى وأسفل الصفحة
    icon_fix_css = """
        /* إخفاء نصوص الأيقونات التالفة */
        header [data-testid="stHeader"] { background: transparent !important; }
    """

    st.markdown(f"<style>{direction_css}\n{theme_css}\n{icon_fix_css}</style>", unsafe_allow_html=True)

def render_sidebar(stats=None, show_theme_toggle=True, show_stats=True, show_navigation=True):
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"

    apply_dynamic_theme()
    
    lang_code = st.session_state.lang
    T = TRANSLATIONS.get(lang_code, TRANSLATIONS["ar"])

    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <h2 style="margin: 0; font-weight: 800; font-size: 1.4rem; color: #E0218A;">🌾 SmartAgri</h2>
            <span style="font-size: 0.75rem; opacity: 0.75;">{T['brand_subtitle']}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        if show_navigation:
            st.page_link("app.py", label=T["home"], icon="🏠")
            st.page_link("pages/1_Chat.py", label=T["chat"], icon="💬")
            st.page_link("pages/2_Documents.py", label=T["docs"], icon="📁")
            st.page_link("pages/3_Analytics.py", label=T["analytics"], icon="📊")
            st.markdown("---")

        if show_stats and stats:
            st.markdown(f"##### {T['stats_title']}")
            st.caption(f"📄 {T['docs_count']}: {stats.get('documents', 0)}")
            st.caption(f"🌱 {T['suppliers_count']}: {stats.get('suppliers', 0)}")
            st.caption(f"🌾 {T['contracts_count']}: {stats.get('contracts', 0)}")
            st.caption(f"⭐ {T['quality_rate']}: {stats.get('quality', 0)}%")
            st.markdown("---")

        col_theme, col_lang = st.columns(2)

        with col_theme:
            if show_theme_toggle:
                theme_btn_label = T["theme_light"] if st.session_state.dark_mode else T["theme_dark"]
                if st.button(theme_btn_label, key="toggle_theme_btn", use_container_width=True):
                    st.session_state.dark_mode = not st.session_state.dark_mode
                    st.rerun()

        with col_lang:
            if st.button(T["lang_btn"], key="toggle_lang_btn", use_container_width=True):
                st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
                st.rerun()

    return st.session_state.lang
