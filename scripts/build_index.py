"""
🌾 بناء فهرس Chroma من knowledge_base - SmartAgri
يشتغل تلقائياً عند بدء التطبيق لو الفهرس مش موجود
"""

import sys
import asyncio
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from database.embeddings import Embeddings
from database.chroma_loader import ChromaLoader
from utils.logger import logger


# ============================================================
# ✅ دالة تنظيف البيانات الوصفية لتكون متوافقة مع Chroma
# ============================================================

def clean_metadata(metadata: dict) -> dict:
    cleaned = {}
    for key, value in metadata.items():
        if not key:
            continue
        if value is None:
            cleaned[key] = "unknown"
        elif isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        elif isinstance(value, (list, tuple, set)):
            try:
                str_values = [str(v) for v in value if v is not None]
                cleaned[key] = ", ".join(str_values) if str_values else "empty_list"
            except:
                cleaned[key] = str(value)
        elif isinstance(value, dict):
            try:
                items = [f"{k}={v}" for k, v in value.items() if v is not None]
                cleaned[key] = "; ".join(items) if items else "empty_dict"
            except:
                cleaned[key] = str(value)
        else:
            try:
                cleaned[key] = str(value)
            except:
                cleaned[key] = "unknown_type"
    return cleaned


# ============================================================
# 📄 PDF Loader مدمج (بدون dependency خارجية غير pypdf)
# ============================================================

def load_pdf(file_path: Path) -> list[dict]:
    """
    تحميل PDF وتقسيمه لـ chunks
    بيرجع list من dicts كل واحد فيه text + metadata
    """
    chunks = []

    try:
        import pypdf
    except ImportError:
        try:
            import PyPDF2 as pypdf
        except ImportError:
            logger.error("❌ pypdf not installed. Run: pip install pypdf")
            return []

    try:
        reader = pypdf.PdfReader(str(file_path))
        full_text = ""

        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                full_text += text + "\n"
            except Exception as e:
                logger.warning(f"⚠️ Error reading page {page_num} of {file_path.name}: {e}")

        if not full_text.strip():
            logger.warning(f"⚠️ No text extracted from: {file_path.name}")
            return []

        # ✅ تقسيم النص لـ chunks بحجم 1000 حرف مع overlap 200
        chunk_size = 1000
        overlap = 200
        text = full_text.strip()

        if len(text) <= chunk_size:
            chunks.append({
                "text": text,
                "metadata": {
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            })
        else:
            start = 0
            chunk_index = 0
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "filename": file_path.name,
                            "file_path": str(file_path),
                            "chunk_index": chunk_index,
                        }
                    })
                    chunk_index += 1
                start += chunk_size - overlap

            # تحديث total_chunks
            for chunk in chunks:
                chunk["metadata"]["total_chunks"] = chunk_index

        logger.info(f"✅ Loaded PDF: {file_path.name} → {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"❌ Error loading PDF {file_path.name}: {e}")

    return chunks


# ============================================================
# 🔨 بناء الفهرس
# ============================================================

async def build_index():
    """بناء فهرس Chroma من مستندات knowledge_base"""
    logger.info("🌾 Starting index build with Chroma for SmartAgri...")

    kb_path = settings.KNOWLEDGE_BASE_PATH
    if not kb_path.exists():
        logger.error(f"❌ knowledge_base not found: {kb_path}")
        return False

    agricultural_categories = ['crops', 'soil', 'irrigation', 'fertilizers', 'pests', 'productivity']

    all_chunks = []

    for category_dir in sorted(kb_path.iterdir()):
        if not category_dir.is_dir():
            continue

        category_name = category_dir.name.lower()
        if category_name not in agricultural_categories:
            logger.info(f"📁 Skipping non-agricultural folder: {category_name}")
            continue

        # ✅ يدعم PDF و DOCX
        files = list(category_dir.glob("*.pdf")) + list(category_dir.glob("*.docx")) + list(category_dir.glob("*.txt"))

        if not files:
            logger.warning(f"⚠️ No supported files in: {category_name}")
            continue

        logger.info(f"📂 Processing category: {category_name} ({len(files)} files)")

        for file_path in files:
            ext = file_path.suffix.lower()

            if ext == ".pdf":
                file_chunks = load_pdf(file_path)

            elif ext == ".docx":
                try:
                    from database.docx_loader import DocxLoader
                    loader = DocxLoader()
                    result = loader.load_file(str(file_path))
                    if result:
                        file_chunks = [{
                            "text": result.get("text", ""),
                            "metadata": result.get("metadata", {})
                        }]
                    else:
                        file_chunks = []
                except Exception as e:
                    logger.error(f"❌ Error loading DOCX {file_path.name}: {e}")
                    file_chunks = []

            elif ext == ".txt":
                try:
                    from database.text_loader import TextLoader
                    loader = TextLoader()
                    result = loader.load_file(str(file_path))
                    if result:
                        file_chunks = [{
                            "text": result.get("text", ""),
                            "metadata": result.get("metadata", {})
                        }]
                    else:
                        file_chunks = []
                except Exception as e:
                    logger.error(f"❌ Error loading TXT {file_path.name}: {e}")
                    file_chunks = []

            else:
                continue

            # ✅ إضافة الـ category لكل chunk
            for chunk in file_chunks:
                chunk["metadata"]["category"] = category_dir.name
                chunk["metadata"] = clean_metadata(chunk["metadata"])

            all_chunks.extend(file_chunks)

    if not all_chunks:
        logger.error("❌ No chunks loaded! Check that knowledge_base has supported files (PDF/DOCX/TXT)")
        return False

    logger.info(f"📄 Total chunks to index: {len(all_chunks)}")

    # ✅ توليد المتجهات
    embeddings_model = Embeddings(
        model_name=settings.EMBEDDING_MODEL,
        device=settings.EMBEDDING_DEVICE
    )

    texts = [c.get("text", "") for c in all_chunks]

    logger.info("🧬 Generating embeddings...")
    vectors = await embeddings_model.encode(texts, show_progress=True)
    logger.info(f"🧬 Generated {len(vectors)} embeddings")

    # ✅ بناء فهرس Chroma
    chroma_loader = ChromaLoader()
    chroma_loader.clear()

    documents_to_add = []
    for i, (chunk, vector) in enumerate(zip(all_chunks, vectors)):
        doc_id = f"agri_{i}_{chunk['metadata'].get('filename', 'unknown').replace('.', '_')}"

        if hasattr(vector, 'tolist'):
            vector = vector.tolist()
        elif isinstance(vector, np.ndarray):
            vector = vector.tolist()
        elif not isinstance(vector, list):
            vector = list(vector)

        documents_to_add.append({
            "id": doc_id,
            "text": chunk.get("text", ""),
            "embedding": vector,
            "metadata": clean_metadata(chunk.get("metadata", {}))
        })

    if documents_to_add:
        added_count = chroma_loader.add_documents(documents_to_add)
        if added_count > 0:
            logger.info(f"✅ Index built successfully! ({added_count} chunks indexed in Chroma)")
            return True
        else:
            logger.error("❌ Failed to add documents to Chroma!")
            return False
    else:
        logger.error("❌ No documents to add!")
        return False


if __name__ == "__main__":
    asyncio.run(build_index())
