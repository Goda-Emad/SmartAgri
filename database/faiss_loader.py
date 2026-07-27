# database/faiss_loader.py
"""
🗄️ تحميل وإدارة فهرس FAISS

يقوم بتحميل فهرس FAISS والبحث فيه واسترجاع المستندات
"""

import os
import pickle
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
from datetime import datetime

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS not available. Install with: pip install faiss-cpu")

from core.config import settings
from utils.logger import logger


class FAISSLoader:
    """
    تحميل وإدارة فهرس FAISS

    يدعم:
    - تحميل فهرس FAISS من القرص
    - البحث في الفهرس
    - إضافة مستندات جديدة
    - حذف مستندات
    - إعادة بناء الفهرس
    """

    def __init__(
        self,
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
        dimension: int = 384
    ):
        self.index_path = Path(index_path or settings.FAISS_INDEX_PATH / "index.faiss")
        self.metadata_path = Path(metadata_path or settings.FAISS_INDEX_PATH / "metadata.pkl")
        self.dimension = dimension

        self.index = None
        self.metadata = []
        self.is_loaded = False

        self.stats = {
            "total_documents": 0,
            "total_searches": 0,
            "avg_search_time": 0,
            "last_search_time": 0
        }

        self.load()

        logger.info("🗄️ FAISSLoader initialized")

    # ============================================================
    # طرق التحميل والحفظ
    # ============================================================

    def load(self) -> bool:
        try:
            if not FAISS_AVAILABLE:
                logger.error("❌ faiss library not installed - add 'faiss-cpu' to requirements.txt")
                self.is_loaded = False
                return False

            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"✅ FAISS index loaded: {self.index_path}")
            else:
                logger.warning(f"⚠️ FAISS index not found: {self.index_path}")
                self._create_empty_index()

            if self.metadata_path.exists():
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"✅ Metadata loaded: {len(self.metadata)} documents")
            else:
                logger.warning(f"⚠️ Metadata not found: {self.metadata_path}")
                self.metadata = []

            self.is_loaded = True
            self.stats["total_documents"] = len(self.metadata)

            return True

        except Exception as e:
            logger.error(f"❌ Error loading FAISS: {str(e)}")
            self.is_loaded = False
            return False

    def save(self) -> bool:
        try:
            if self.index is None:
                logger.warning("⚠️ No index to save")
                return False

            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            faiss.write_index(self.index, str(self.index_path))

            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)

            logger.info(f"✅ FAISS index saved: {self.index_path}")
            logger.info(f"✅ Metadata saved: {len(self.metadata)} documents")

            return True

        except Exception as e:
            logger.error(f"❌ Error saving FAISS: {str(e)}")
            return False

    def _create_empty_index(self) -> None:
        if not FAISS_AVAILABLE:
            return
        self.index = faiss.IndexFlatL2(self.dimension)
        logger.info("📁 Created empty FAISS index")

    # ============================================================
    # طرق البحث
    # ============================================================

    async def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        import time
        start_time = time.time()

        if not self.is_loaded or self.index is None:
            logger.error("❌ FAISS not loaded")
            return []

        if len(self.metadata) == 0:
            logger.warning("⚠️ No documents in index")
            return []

        try:
            if len(query_vector.shape) == 1:
                query_vector = query_vector.reshape(1, -1)

            distances, indices = self.index.search(query_vector.astype('float32'), top_k)

            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1 or idx >= len(self.metadata):
                    continue

                similarity = self._distance_to_similarity(dist)

                result = {
                    "id": self.metadata[idx].get("id", f"doc_{idx}"),
                    "text": self.metadata[idx].get("text", ""),
                    "metadata": self.metadata[idx].get("metadata", {}),
                    "relevance_score": similarity,
                    "distance": float(dist),
                    "index": int(idx)
                }

                results.append(result)

            elapsed = time.time() - start_time
            self._update_stats(len(results), elapsed)

            logger.debug(f"🔍 Found {len(results)} results in {elapsed:.3f}s")

            return results

        except Exception as e:
            logger.error(f"❌ Error searching FAISS: {str(e)}")
            return []

    def search_sync(
        self,
        query_vector: np.ndarray,
        top_k: int = 10
    ) -> Tuple[List[int], List[float]]:
        if not self.is_loaded or self.index is None:
            return [], []

        if len(self.metadata) == 0:
            return [], []

        try:
            if len(query_vector.shape) == 1:
                query_vector = query_vector.reshape(1, -1)

            distances, indices = self.index.search(
                query_vector.astype('float32'),
                min(top_k, len(self.metadata))
            )

            return indices[0].tolist(), distances[0].tolist()

        except Exception as e:
            logger.error(f"❌ Error in sync search: {str(e)}")
            return [], []

    # ============================================================
    # طرق إدارة المستندات
    # ============================================================

    def add_document(
        self,
        doc_id: str,
        text: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            if self.index is None:
                self._create_empty_index()

            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)

            self.index.add(embedding.astype('float32'))

            doc_data = {
                "id": doc_id,
                "text": text,
                "metadata": metadata,
                "added_at": datetime.now().isoformat()
            }
            self.metadata.append(doc_data)

            self.stats["total_documents"] = len(self.metadata)

            logger.info(f"✅ Document added: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error adding document: {str(e)}")
            return False

    def delete_document(self, doc_id: str) -> bool:
        try:
            idx = None
            for i, doc in enumerate(self.metadata):
                if doc.get("id") == doc_id:
                    idx = i
                    break

            if idx is None:
                logger.warning(f"⚠️ Document not found: {doc_id}")
                return False

            self.metadata.pop(idx)

            self._rebuild_index()

            self.stats["total_documents"] = len(self.metadata)

            logger.info(f"✅ Document deleted: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting document: {str(e)}")
            return False

    def update_document(
        self,
        doc_id: str,
        text: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            self.delete_document(doc_id)
            return self.add_document(doc_id, text, embedding, metadata)

        except Exception as e:
            logger.error(f"❌ Error updating document: {str(e)}")
            return False

    def _rebuild_index(self) -> None:
        self._create_empty_index()
        logger.warning("⚠️ Rebuilding index requires embeddings. Use rebuild_from_embeddings()")

    def rebuild_from_embeddings(self, embeddings: List[np.ndarray]) -> bool:
        try:
            if len(embeddings) != len(self.metadata):
                logger.error("❌ Embeddings count doesn't match metadata")
                return False

            self._create_empty_index()

            for embedding in embeddings:
                if len(embedding.shape) == 1:
                    embedding = embedding.reshape(1, -1)
                self.index.add(embedding.astype('float32'))

            self.stats["total_documents"] = len(self.metadata)

            logger.info(f"✅ Index rebuilt with {len(embeddings)} documents")
            return True

        except Exception as e:
            logger.error(f"❌ Error rebuilding index: {str(e)}")
            return False

    # ============================================================
    # طرق مساعدة
    # ============================================================

    def _distance_to_similarity(self, distance: float) -> float:
        similarity = 1 / (1 + distance)
        return min(max(similarity, 0.0), 1.0)

    def _update_stats(self, count: int, elapsed: float) -> None:
        self.stats["total_searches"] += 1
        self.stats["last_search_time"] = elapsed

        total = self.stats["total_searches"]
        if total > 0:
            self.stats["avg_search_time"] = (
                (self.stats["avg_search_time"] * (total - 1) + elapsed) / total
            )

    # ============================================================
    # طرق الإحصائيات والمعلومات
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "is_loaded": self.is_loaded,
            "dimension": self.dimension,
            "index_path": str(self.index_path),
            "metadata_path": str(self.metadata_path)
        }

    def get_index_info(self) -> Dict[str, Any]:
        if self.index is None:
            return {"status": "not_loaded"}

        return {
            "status": "loaded",
            "total_vectors": self.index.ntotal,
            "dimension": self.index.d,
            "index_type": type(self.index).__name__,
            "is_trained": self.index.is_trained,
            "metadata_count": len(self.metadata)
        }

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        for doc in self.metadata:
            if doc.get("id") == doc_id:
                return doc
        return None

    def get_all_documents(self) -> List[Dict[str, Any]]:
        return self.metadata.copy()

    def get_index_size(self) -> int:
        return len(self.metadata)

    def clear(self) -> None:
        self._create_empty_index()
        self.metadata = []
        self.stats["total_documents"] = 0
        self.is_loaded = True
        logger.info("🗑️ FAISS index cleared")

    # ============================================================
    # طرق التحقق من الصحة
    # ============================================================

    async def check_health(self) -> bool:
        try:
            if not self.is_loaded:
                return False

            if self.index is None:
                return False

            test_vector = np.random.randn(1, self.dimension).astype('float32')
            self.index.search(test_vector, 1)

            return True

        except Exception as e:
            logger.error(f"❌ FAISS health check failed: {str(e)}")
            return False

