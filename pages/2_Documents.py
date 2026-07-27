"""
🌾 صفحة إدارة المعرفة الزراعية - SmartAgri Documents Page
تتيح للمستخدم استعراض، البحث، معاينة، رفع، وحذف المستندات في قاعدة المعرفة الزراعية.
"""

import streamlit as st
import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from core.config import settings
from utils.logger import logger

# ============================================================
# ⚙️ إعدادات الصفحة
# ============================================================
st.set_page_config(
    page_title="إدارة المعرفة الزراعية | SmartAgri",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 🌐 قاموس اللغات والتراجم الخاصة بالصفحة
# ============================================================
DOCS_TRANSLATIONS = {
    "ar": {
        "title": "🌾 إدارة المعرفة الزراعية",
        "subtitle": "🌱 استعراض، معاينة، تنزيل، ورفع المستندات الزراعية في قاعدة المعرفة الذكية.",
        "stat_total": "📄 إجمالي المستندات",
        "stat_cats": "📁 عدد التصنيفات",
        "stat_largest_cat": "📊 التصنيف الأكبر",
        "stat_top_type": "📂 النوع الأكثر شيوعاً",
        "upload_title": "📤 رفع مستند زراعي جديد",
        "upload_file": "اختر ملفاً",
        "upload_cat": "التصنيف الزراعي",
        "upload_btn": "🚀 رفع الملف وإعادة الفهرسة",
        "upload_success": "✅ تم رفع الملف بنجاح:",
        "search_placeholder": "🔍 ابحث باسم المستند...",
        "filter_cat": "التصنيف:",
        "all_cats": "الكل",
        "doc_list_title": "📋 قائمة المستندات الزراعية المخزنة",
        "no_docs": "📭 لا توجد مستندات تطابق خيارات البحث",
        "btn_preview": "👁️ معاينة",
        "btn_delete": "🗑️ حذف",
        "btn_download": "📥 تنزيل",
        "rebuild_btn": "🔄 إعادة بناء الفهرس الذكي",
        "rebuilding": "🔄 جاري تحديث الفهرس...",
        "kb_path_lbl": "📁 مسار قاعدة المعرفة المحلي:"
    },
    "en": {
        "title": "🌾 Agricultural Knowledge Management",
        "subtitle": "🌱 Browse, preview, download, and upload agricultural documents to your AI Knowledge Base.",
        "stat_total": "📄 Total Documents",
        "stat_cats": "📁 Categories",
        "stat_largest_cat": "📊 Top Category",
        "stat_top_type": "📂 Common File Type",
        "upload_title": "📤 Upload New Agricultural Document",
        "upload_file": "Select File",
        "upload_cat": "Agricultural Category",
        "upload_btn": "🚀 Upload File & Reindex",
        "upload_success": "✅ File uploaded successfully:",
        "search_placeholder": "🔍 Search document by filename...",
        "filter_cat": "Category:",
        "all_cats": "All",
        "doc_list_title": "📋 Stored Agricultural Documents Archive",
        "no_docs": "📭 No documents match your search criteria",
        "btn_preview": "👁️ Preview",
        "btn_delete": "🗑️ Delete",
        "btn_download": "📥 Download",
        "rebuild_btn": "🔄 Rebuild Vector Index",
        "rebuilding": "🔄 Updating index...",
        "kb_path_lbl": "📁 Local Knowledge Base Path:"
    }
}


# ============================================================
# 🎨 تحميل التنسيقات المخصصة (CSS) - Barbie Palette 💖
# ============================================================
def load_css():
    """تنسيق البطاقات والجداول الخاصة بصفحة المستندات"""
    st.markdown("""
        <style>
        /* هيدر الصفحة - نفس كلاس .doc-header اللي بيتلون من apply_dynamic_theme
           في sidebar.py، فبيستجيب تلقائي لتبديل الثيم */
        .doc-header {
            border-radius: 14px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 1.5rem;
        }
        .doc-header h2 {
            font-weight: 800;
            margin: 0 0 6px 0;
        }
        .doc-header p {
            font-size: 0.88rem;
            margin: 0;
        }

        .doc-card {
            background-color: rgba(224, 33, 138, 0.06);
            border: 1px solid rgba(224, 33, 138, 0.15);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.6rem;
            transition: all 0.2s ease;
        }
        .doc-card:hover {
            border-color: #E0218A;
        }
        </style>
    """, unsafe_allow_html=True)

    css_file = Path(__file__).parent.parent / "styles" / "custom.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ============================================================
# 🛠️ الدوال المساعدة لقاعدة المعرفة
# ============================================================

def get_documents_stats():
    """إحصائيات إجمالية للمستندات والتصنيفات"""
    kb_path = settings.KNOWLEDGE_BASE_PATH
    stats = {"total": 0, "by_category": {}, "file_types": {}}

    if not kb_path.exists():
        return stats

    for category_dir in kb_path.iterdir():
        if category_dir.is_dir():
            count = 0
            for file_path in category_dir.glob("*"):
                if file_path.is_file():
                    count += 1
                    ext = file_path.suffix.lower()
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
            stats["by_category"][category_dir.name] = count
            stats["total"] += count

    return stats


def get_documents(category: str = None, search_term: str = ""):
    """جلب قائمة المستندات مع التصفية والبحث"""
    kb_path = settings.KNOWLEDGE_BASE_PATH
    documents = []

    if not kb_path.exists():
        return documents

    for category_dir in kb_path.iterdir():
        if category_dir.is_dir():
            if category and category != "الكل" and category != "All" and category_dir.name != category:
                continue

            for file_path in category_dir.glob("*"):
                if file_path.is_file():
                    filename = file_path.name
                    if search_term and search_term.lower() not in filename.lower():
                        continue

                    documents.append({
                        "filename": filename,
                        "category": category_dir.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime)
                    })

    documents.sort(key=lambda x: x["modified"], reverse=True)
    return documents


def delete_document(file_path: str) -> bool:
    """حذف مستند من القرص"""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.info(f"🗑️ Deleted document: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Error deleting document: {str(e)}")
        return False


def preview_document_content(file_path: str) -> str:
    """معاينة جزء من نص المستند"""
    try:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext == ".txt":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(1500)
        elif ext == ".docx":
            import docx
            doc = docx.Document(path)
            full_text = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(full_text[:15])
        elif ext == ".pdf":
            # معاينة PDF (نص فقط)
            try:
                import PyPDF2
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for i, page in enumerate(reader.pages[:5]):
                        text += page.extract_text() or ""
                    return text[:1500] if text else "⚠️ لا يمكن استخراج نص من ملف PDF هذا."
            except ImportError:
                return "⚠️ مكتبة PyPDF2 غير مثبتة لمعاينة ملفات PDF."
            except Exception as e:
                return f"⚠️ تعذر قراءة PDF: {str(e)}"
        else:
            return "⚠️ معاينة النص المباشرة متاحة حالياً لملفات .txt و .docx و .pdf فقط."
    except Exception as e:
        return f"❌ تعذر فتح الملف للمعاينة: {str(e)}"


def rebuild_index():
    """إعادة بناء فهرس FAISS تلقائياً"""
    try:
        script_path = Path(__file__).parent.parent / "scripts" / "build_index.py"
        if script_path.exists():
            result = subprocess.run(
                ["python", str(script_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                st.success("✅ تم تحديث الفهرس الذكي بنجاح!")
                logger.info("Index rebuilt successfully.")
            else:
                st.error(f"❌ فشل تحديث الفهرس: {result.stderr}")
        else:
            st.warning("⚠️ لم يتم العثور على سكريبت بناء الفهرس build_index.py")
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء إعادة الفهرسة: {str(e)}")


# ============================================================
# 🖥️ واجهة الصفحة الرئيسية
# ============================================================

def show():
    load_css()

    # ✅ 1. تشغيل السايدبار الموحد
    current_lang = render_sidebar(
        show_theme_toggle=True,
        show_stats=False,
        show_navigation=True
    )
    T = DOCS_TRANSLATIONS.get(current_lang, DOCS_TRANSLATIONS["ar"])

    # ✅ 2. الترويسة الرئيسية
    st.markdown(f"""
    <div class="doc-header">
        <h2>{T['title']}</h2>
        <p>{T['subtitle']}</p>
    </div>
    """, unsafe_allow_html=True)

    # ✅ 3. الإحصائيات السريعة
    stats = get_documents_stats()
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(T["stat_total"], stats["total"])
    with c2:
        st.metric(T["stat_cats"], len(stats["by_category"]))
    with c3:
        max_cat = max(stats["by_category"], key=stats["by_category"].get) if stats["by_category"] else "—"
        st.metric(T["stat_largest_cat"], max_cat)
    with c4:
        max_ext = max(stats["file_types"], key=stats["file_types"].get) if stats["file_types"] else "—"
        st.metric(T["stat_top_type"], max_ext.upper())

    st.markdown("---")

    # ✅ 4. نموذج رفع المستندات
    with st.expander(T["upload_title"], expanded=False):
        col_f, col_c = st.columns(2)

        with col_f:
            uploaded_file = st.file_uploader(
                T["upload_file"],
                type=['txt', 'docx', 'pdf'],
                help="Supported formats: .txt, .docx, .pdf"
            )

        with col_c:
            category = st.selectbox(
                T["upload_cat"],
                ["crops", "soil", "irrigation", "fertilizers", "pests", "other"],
                index=0
            )

        if uploaded_file and st.button(T["upload_btn"], use_container_width=True, type="primary"):
            save_path = settings.KNOWLEDGE_BASE_PATH / category / uploaded_file.name
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"{T['upload_success']} {uploaded_file.name}")

            with st.spinner(T["rebuilding"]):
                rebuild_index()

            st.rerun()

    # ✅ 5. البحث والفلترة وقائمة المستندات
    st.subheader(T["doc_list_title"])

    col_search, col_filter = st.columns([2.5, 1.5])

    with col_search:
        search_query = st.text_input("", placeholder=T["search_placeholder"], label_visibility="collapsed")

    with col_filter:
        categories_list = [T["all_cats"]] + list(stats["by_category"].keys())
        selected_cat = st.selectbox(T["filter_cat"], categories_list, index=0)

    documents = get_documents(category=selected_cat, search_term=search_query)

    st.markdown("<br>", unsafe_allow_html=True)

    if documents:
        st.caption(f"عدد النتائج: {len(documents)}")
        for doc in documents:
            ext = Path(doc["filename"]).suffix.lower()
            icon = "📄" if ext == ".txt" else "📝" if ext == ".docx" else "📕" if ext == ".pdf" else "📎"

            with st.container():
                col_info, col_actions = st.columns([3, 2])

                with col_info:
                    st.markdown(f"**{icon} {doc['filename']}**")
                    st.caption(f"📂 {doc['category']} | 📦 {doc['size'] / 1024:.1f} KB | 📅 {doc['modified'].strftime('%Y-%m-%d %H:%M')}")

                with col_actions:
                    b1, b2, b3 = st.columns(3)

                    with b1:
                        if st.button(T["btn_preview"], key=f"prev_{doc['filename']}", use_container_width=True):
                            st.session_state[f"show_preview_{doc['filename']}"] = not st.session_state.get(f"show_preview_{doc['filename']}", False)

                    with b2:
                        try:
                            with open(doc["path"], "rb") as f:
                                st.download_button(
                                    label=T["btn_download"],
                                    data=f.read(),
                                    file_name=doc["filename"],
                                    key=f"dl_{doc['filename']}",
                                    use_container_width=True
                                )
                        except Exception:
                            pass

                    with b3:
                        if st.button(T["btn_delete"], key=f"del_{doc['filename']}", use_container_width=True):
                            if delete_document(doc["path"]):
                                st.success("تم الحذف!")
                                rebuild_index()
                                st.rerun()

                if st.session_state.get(f"show_preview_{doc['filename']}", False):
                    with st.expander(f"📖 معاينة: {doc['filename']}", expanded=True):
                        content = preview_document_content(doc["path"])
                        st.text_area("", content, height=180, disabled=True)

                st.divider()
    else:
        st.info(T["no_docs"])

    # ✅ 6. زر تحديث الفهرس السفلي
    st.markdown("<br>", unsafe_allow_html=True)
    c_reb, c_path = st.columns([1.5, 2])
    with c_reb:
        if st.button(T["rebuild_btn"], use_container_width=True):
            with st.spinner(T["rebuilding"]):
                rebuild_index()
    with c_path:
        st.caption(f"{T['kb_path_lbl']} `{settings.KNOWLEDGE_BASE_PATH}`")


# ============================================================
# 🚀 تشغيل الصفحة
# ============================================================
if __name__ == "__main__":
    show()
