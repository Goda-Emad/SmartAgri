# pages/3_Analytics.py
"""
🌾 صفحة التحليلات والإحصائيات - SmartAgri Analytics

تعرض إحصائيات وتحليلات النظام والمستندات والمزارع مع دعم الثيمين الفاتح والداكن
🌾 SmartAgri - Barbie Color Palette
"""

import streamlit as st
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import re

sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from database.faiss_loader import FAISSLoader
from utils.logger import logger
from components.sidebar import render_sidebar


# ============================================================
# 🌐 قاموس اللغات لصفحة التحليلات
# ============================================================
TRANSLATIONS = {
    "ar": {
        "title": "🌾 التحليلات والإحصائيات الزراعية",
        "subtitle": "نظرة عامة شاملة على المستندات، المزارع، المحاصيل، وإنتاجية البيانات",
        "docs_total": "📄 إجمالي المستندات",
        "categories_cnt": "📁 التصنيفات",
        "total_size": "💾 الحجم الإجمالي",
        "suppliers_cnt": "🌱 المزارع",
        "cat_dist": "📊 توزيع المستندات حسب التصنيف",
        "file_types": "📂 أنواع الملفات",
        "size_dist": "📊 توزيع أحجام الملفات (KB)",
        "supplier_analysis": "🌱 تحليل المزارع",
        "docs_per_supplier": "📊 عدد المستندات لكل مزرعة",
        "quality_analysis": "⭐ تحليل الإنتاجية",
        "avg_quality": "📊 متوسط درجة الإنتاجية",
        "best_supplier": "🏆 أفضل مزرعة",
        "quality_scores_title": "⭐ درجات الإنتاجية لكل مزرعة",
        "contract_analysis": "🌾 تحليل المحاصيل",
        "contract_values_title": "🌾 قيم المحاصيل لكل مزرعة",
        "system_info": "⚙️ معلومات النظام",
        "paths": "📁 المسارات",
        "settings": "🔧 الإعدادات",
        "index_status": "📊 حالة الفهرس",
        "no_docs": "📭 لا توجد مستندات متاحة للتحليل حالياً"
    },
    "en": {
        "title": "🌾 Agricultural Analytics & Statistics",
        "subtitle": "Comprehensive overview of documents, farms, crops, and productivity data",
        "docs_total": "📄 Total Documents",
        "categories_cnt": "📁 Categories",
        "total_size": "💾 Total Size",
        "suppliers_cnt": "🌱 Farms",
        "cat_dist": "📊 Document Distribution by Category",
        "file_types": "📂 File Types",
        "size_dist": "📊 File Size Distribution (KB)",
        "supplier_analysis": "🌱 Farm Analysis",
        "docs_per_supplier": "📊 Documents Count per Farm",
        "quality_analysis": "⭐ Productivity Analysis",
        "avg_quality": "📊 Average Productivity Score",
        "best_supplier": "🏆 Top Farm",
        "quality_scores_title": "⭐ Productivity Scores by Farm",
        "contract_analysis": "🌾 Crop Analysis",
        "contract_values_title": "🌾 Crop Values by Farm",
        "system_info": "⚙️ System Information",
        "paths": "📁 Paths",
        "settings": "🔧 Settings",
        "index_status": "📊 Index Status",
        "no_docs": "📭 No documents available for analysis"
    }
}


# ============================================================
# 🎨 دالة ضبط ثيم الرسوم البيانية (Plotly Theme Adaptability) - Barbie
# ============================================================
def update_chart_theme(fig, is_dark: bool):
    """تعديل ألوان الرسم البياني من Plotly ليتناسب تلقائياً مع الثيم الحالي"""
    font_color = "#FCE4EC" if is_dark else "#4A0E2E"
    grid_color = "rgba(224, 33, 138, 0.15)" if is_dark else "#F8BBD0"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color, family="Inter, system-ui, sans-serif"),
        xaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color, title_font=dict(color=font_color)),
        yaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color, title_font=dict(color=font_color)),
        legend=dict(font=dict(color=font_color)),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


# ============================================================
# 1. دوال استخراج واستعلام البيانات
# ============================================================

def get_documents_stats():
    """الحصول على إحصائيات المستندات والمجلدات"""
    kb_path = settings.KNOWLEDGE_BASE_PATH
    stats = {
        "total": 0,
        "by_category": {},
        "file_types": {},
        "total_size": 0,
        "documents": []
    }

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
                    stats["total_size"] += file_path.stat().st_size
                    stats["documents"].append({
                        "filename": file_path.name,
                        "category": category_dir.name,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime)
                    })
            stats["by_category"][category_dir.name] = count
            stats["total"] += count

    return stats


def get_suppliers_from_filenames(documents):
    """استخراج أسماء المحاصيل/المزارع والإحصائيات المرتبطة بها"""
    suppliers = {}
    patterns = [
        r'([A-Za-z]+)_Crop',
        r'([A-Za-z]+)_Farm',
        r'([A-Za-z]+)_Soil',
        r'([A-Za-z]+)_Irrigation',
        r'([A-Za-z]+)_Fertilizer',
        r'([A-Za-z]+)_Pest',
        r'([A-Za-z]+)_Wheat',
        r'([A-Za-z]+)_Corn',
        r'([A-Za-z]+)_Rice',
        r'([A-Za-z]+)_Barley',
        r'([A-Za-z]+)_Tomato',
        r'([A-Za-z]+)_Potato',
    ]

    for doc in documents:
        filename = doc["filename"]
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                supplier = match.group(1).replace('_', ' ')
                if supplier not in suppliers:
                    suppliers[supplier] = {
                        "name": supplier,
                        "documents": 0,
                        "categories": set(),
                        "total_size": 0
                    }
                suppliers[supplier]["documents"] += 1
                suppliers[supplier]["categories"].add(doc["category"])
                suppliers[supplier]["total_size"] += doc["size"]
                break

    return [{"name": k, **v} for k, v in suppliers.items()]


def get_quality_scores(documents):
    """استخراج درجات الإنتاجية المتاحة من أسماء الملفات"""
    scores = []
    for doc in documents:
        if "yield" in doc["category"].lower() or "productivity" in doc["filename"].lower() or "quality" in doc["filename"].lower():
            match = re.search(r'(\d+)', doc["filename"])
            if match:
                score = int(match.group(1))
                if score <= 100:
                    supplier_name = doc["filename"].replace('_Yield_', '').replace('_Productivity_', '').replace('.pdf', '').replace('.docx', '')
                    supplier_name = re.sub(r'^\d+_', '', supplier_name)
                    scores.append({
                        "supplier": supplier_name,
                        "score": score,
                        "category": doc["category"]
                    })
    return scores


def get_contract_values(documents):
    """استخراج قيم المحاصيل المتاحة"""
    contracts = []
    for doc in documents:
        if "crop" in doc["category"].lower() or "value" in doc["filename"].lower() or "price" in doc["filename"].lower():
            match = re.search(r'(\d+[,\d]*\.?\d*)', doc["filename"])
            if match:
                try:
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    if value > 100:
                        supplier_name = doc["filename"].replace('_Crop_', '').replace('_Value_', '').replace('.pdf', '').replace('.docx', '')
                        supplier_name = re.sub(r'^\d+_', '', supplier_name)
                        contracts.append({
                            "supplier": supplier_name,
                            "value": value,
                            "category": doc["category"]
                        })
                except Exception:
                    pass
    return contracts


# ============================================================
# 2. عرض واجهة الصفحة (Show Page)
# ============================================================

def show():
    """عرض صفحة التحليلات مع التوافق التام مع الثيم الفاتح والداكن"""

    stats = get_documents_stats()
    documents = stats["documents"]
    suppliers = get_suppliers_from_filenames(documents)
    quality_scores = get_quality_scores(documents)

    avg_quality_val = round(sum(s["score"] for s in quality_scores) / len(quality_scores), 1) if quality_scores else 0

    sidebar_stats = {
        "documents": stats["total"],
        "suppliers": len(suppliers),
        "contracts": len(get_contract_values(documents)),
        "quality": avg_quality_val
    }
    lang_code = render_sidebar(stats=sidebar_stats)
    T = TRANSLATIONS.get(lang_code, TRANSLATIONS["ar"])

    is_dark = st.session_state.get("dark_mode", True)

    # الترويسة الرئيسية - بتاخد لونها من .doc-header المشتركة في sidebar.py
    st.markdown(f"""
    <div class="doc-header" style="padding: 18px 24px; border-radius: 12px; margin-bottom: 20px;">
        <h2 style="margin: 0 0 6px 0; font-weight: 800; font-size: 1.6rem;">{T['title']}</h2>
        <p style="margin: 0; font-size: 0.9rem; opacity: 0.85;">{T['subtitle']}</p>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # 5. كروت الإحصائيات الرئيسية (Metrics Cards)
    # ============================================================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(T["docs_total"], stats["total"], delta="+2" if stats["total"] > 0 else "0")
    with col2:
        st.metric(T["categories_cnt"], len(stats["by_category"]))
    with col3:
        total_size_mb = stats["total_size"] / (1024 * 1024)
        st.metric(T["total_size"], f"{total_size_mb:.1f} MB")
    with col4:
        st.metric(T["suppliers_cnt"], len(suppliers))

    st.markdown("---")

    # ============================================================
    # 6. الرسوم البيانية المتوافقة مع الثيم - Barbie Palette
    # ============================================================

    # 6.1 توزيع المستندات حسب التصنيف
    if stats["by_category"]:
        df_categories = pd.DataFrame({
            "التصنيف": list(stats["by_category"].keys()),
            "العدد": list(stats["by_category"].values())
        })

        # باليت Barbie لدائرة التوزيع (تدرجات وردي/ماجنتا/بورجندي)
        barbie_pie_colors = ["#E0218A", "#C2185B", "#F48FB1", "#AD1457", "#F8BBD0", "#880E4F"]

        fig1 = px.pie(
            df_categories,
            names="التصنيف",
            values="العدد",
            title=f"<b>{T['cat_dist']}</b>",
            color_discrete_sequence=barbie_pie_colors,
            hole=0.4
        )
        fig1 = update_chart_theme(fig1, is_dark)
        fig1.update_layout(height=380, showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info(T["no_docs"])

    # 6.2 أنواع الملفات وتوزيع الأحجام
    if stats["file_types"]:
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            df_filetypes = pd.DataFrame({
                "نوع الملف": list(stats["file_types"].keys()),
                "العدد": list(stats["file_types"].values())
            })
            fig2 = px.bar(
                df_filetypes,
                x="نوع الملف",
                y="العدد",
                title=f"<b>{T['file_types']}</b>",
                color_discrete_sequence=["#E0218A" if is_dark else "#C2185B"]
            )
            fig2 = update_chart_theme(fig2, is_dark)
            fig2.update_layout(height=320)
            st.plotly_chart(fig2, use_container_width=True)

        with col_chart2:
            if documents:
                sizes = [doc["size"] / 1024 for doc in documents]
                df_sizes = pd.DataFrame({"الحجم (KB)": sizes})
                fig3 = px.histogram(
                    df_sizes,
                    x="الحجم (KB)",
                    title=f"<b>{T['size_dist']}</b>",
                    nbins=10,
                    color_discrete_sequence=["#F48FB1" if is_dark else "#AD1457"]
                )
                fig3 = update_chart_theme(fig3, is_dark)
                fig3.update_layout(height=320)
                st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 7. قسم المزارع (Farms Section)
    # ============================================================
    if suppliers:
        st.subheader(T["supplier_analysis"])

        suppliers_df = pd.DataFrame([
            {
                "المزرعة": s["name"],
                "المستندات": s["documents"],
                "التصنيفات": ", ".join(s["categories"]),
                "الحجم (KB)": f"{s['total_size'] / 1024:.1f}"
            }
            for s in suppliers
        ])

        st.dataframe(
            suppliers_df,
            use_container_width=True,
            hide_index=True
        )

        fig4 = px.bar(
            suppliers_df,
            x="المزرعة",
            y="المستندات",
            title=f"<b>{T['docs_per_supplier']}</b>",
            color_discrete_sequence=["#C2185B" if is_dark else "#880E4F"]
        )
        fig4 = update_chart_theme(fig4, is_dark)
        fig4.update_layout(height=340)
        st.plotly_chart(fig4, use_container_width=True)

    # ============================================================
    # 8. قسم الإنتاجية (Productivity Metrics)
    # ============================================================
    if quality_scores:
        st.markdown("---")
        st.subheader(T["quality_analysis"])

        scores_df = pd.DataFrame(quality_scores)
        col_q1, col_q2 = st.columns(2)

        with col_q1:
            st.metric(
                T["avg_quality"],
                f"{avg_quality_val}%",
                delta="+5%" if avg_quality_val > 80 else "0%"
            )

        with col_q2:
            best = max(quality_scores, key=lambda x: x["score"])
            st.metric(
                T["best_supplier"],
                best["supplier"],
                delta=f"{best['score']}%"
            )

        fig5 = px.bar(
            scores_df,
            x="supplier",
            y="score",
            title=f"<b>{T['quality_scores_title']}</b>",
            labels={"supplier": "المزرعة", "score": "درجة الإنتاجية (%)"},
            color="score",
            color_continuous_scale="RdYlGn",
            range_color=[0, 100]
        )
        fig5 = update_chart_theme(fig5, is_dark)
        fig5.update_layout(height=340)
        st.plotly_chart(fig5, use_container_width=True)

    # ============================================================
    # 9. قسم المحاصيل (Crops Section)
    # ============================================================
    contracts = get_contract_values(documents)
    if contracts:
        st.markdown("---")
        st.subheader(T["contract_analysis"])

        contracts_df = pd.DataFrame([
            {
                "المزرعة": c["supplier"],
                "القيمة (SAR)": c["value"],
                "التصنيف": c["category"]
            }
            for c in contracts
        ]).sort_values("القيمة (SAR)", ascending=False)

        st.dataframe(contracts_df, use_container_width=True, hide_index=True)

        fig6 = px.bar(
            contracts_df,
            x="المزرعة",
            y="القيمة (SAR)",
            title=f"<b>{T['contract_values_title']}</b>",
            color_discrete_sequence=["#AD1457" if is_dark else "#880E4F"]
        )
        fig6 = update_chart_theme(fig6, is_dark)
        fig6.update_layout(height=340)
        st.plotly_chart(fig6, use_container_width=True)

    # ============================================================
    # 10. معلومات وإعدادات النظام
    # ============================================================
    st.markdown("---")
    with st.expander(T["system_info"], expanded=False):
        col_sys1, col_sys2 = st.columns(2)

        with col_sys1:
            st.markdown(f"**{T['paths']}:**")
            st.code(f"KNOWLEDGE_BASE: {settings.KNOWLEDGE_BASE_PATH}")
            st.code(f"FAISS_INDEX: {settings.FAISS_INDEX_PATH}")
            st.code(f"DATA_PATH: {settings.DATA_PATH}")

        with col_sys2:
            st.markdown(f"**{T['settings']}:**")
            st.code(f"MODEL: {settings.EMBEDDING_MODEL}")
            st.code(f"DEVICE: {settings.EMBEDDING_DEVICE}")
            st.code(f"DIMENSION: {settings.EMBEDDING_DIMENSION}")

        st.markdown(f"**{T['index_status']}:**")
        try:
            loader = FAISSLoader()
            index_info = loader.get_index_info()
            st.code(f"Status: {index_info.get('status', 'Unknown')} | Total Vectors: {index_info.get('total_vectors', 0)}")
        except Exception as e:
            st.warning(f"⚠️ Index Loader Warning: {str(e)}")


# ============================================================
# 3. تشغيل الصفحة عند الاستدعاء المباشر
# ============================================================
if __name__ == "__main__":
    show()
