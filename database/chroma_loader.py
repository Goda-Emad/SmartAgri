"""
🗄️ تحميل وإدارة قاعدة بيانات Chroma - SmartAgri

يقوم بإدارة الاتصال بقاعدة بيانات Chroma والبحث فيها للمجال الزراعي
✅ يستخدم EphemeralClient (في الذاكرة) لأن Streamlit Cloud لا يحتفظ بالملفات بين الـ deployments
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
import numpy as np

from core.config import settings
from utils.logger import logger


# ============================================================
# ✅ دالة تنظيف البيانات الوصفية
# ============================================================

def clean_metadata_for_chroma(metadata: Dict[str, Any]) -> Dict[str, Any]:
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
        elif isinstance(value, np.ndarray):
            try:
                arr_list = value.tolist()
                str_values = [str(v) for v in arr_list if v is not None]
                cleaned[key] = ", ".join(str_values) if str_values else "empty_array"
            except:
                cleaned[key] = str(value)
        else:
            try:
                cleaned[key] = str(value)
            except:
                cleaned[key] = "unknown_type"
    return cleaned


class ChromaLoader:
    """
    إدارة قاعدة بيانات Chroma في الذاكرة (EphemeralClient)
    مناسب لـ Streamlit Cloud حيث لا يتم الاحتفاظ بالملفات بين الـ deployments
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_model: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL

        # ✅ EphemeralClient — في الذاكرة بدلاً من الـ disk
        # Streamlit Cloud يمسح الـ filesystem عند كل deploy/restart
        self.client = chromadb.EphemeralClient()

        # تهيئة دالة التضمين
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )

        # الحصول على المجموعة أو إنشاؤها
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        self.is_loaded = True
        self.stats = {
            "total_documents": 0,
            "total_searches": 0,
            "avg_search_time": 0,
            "last_search_time": 0
        }

        logger.info(f"🗄️ ChromaLoader initialized with collection: {collection_name}")
        logger.info(f"📊 Documents in collection: {self.get_index_size()}")

    # ============================================================
    # طرق البحث
    # ============================================================

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        include_metadata: bool = True,
        filter_category: Optional[str] = None,
        filter_farm: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        import time
        start_time = time.time()

        # ✅ التأكد من صيغة المتجه
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()
        elif not isinstance(query_vector, list):
            query_vector = list(query_vector)

        if query_vector and isinstance(query_vector[0], (list, np.ndarray)):
            query_vector = query_vector[0]

        where_filter = {}
        if filter_category:
            where_filter["category"] = filter_category
        if filter_farm:
            where_filter["farm"] = filter_farm

        try:
            count = self.get_index_size()
            if count == 0:
                logger.warning("⚠️ Collection is empty")
                return []

            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=min(top_k, count),
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )

            formatted_results = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0]
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]

                for i, doc_id in enumerate(ids):
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity = 1 / (1 + distance)

                    if similarity < min_score:
                        continue

                    formatted_results.append({
                        "id": doc_id,
                        "text": documents[i] if i < len(documents) else "",
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "relevance_score": similarity,
                        "distance": distance
                    })

            elapsed = time.time() - start_time
            self._update_stats(len(formatted_results), elapsed)
            logger.info(f"🔍 Found {len(formatted_results)} results in {elapsed:.3f}s")

            return formatted_results

        except Exception as e:
            logger.error(f"❌ Error searching Chroma: {str(e)}")
            return []

    # ============================================================
    # طرق إدارة المستندات
    # ============================================================

    def add_document(self, doc_id: str, text: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        try:
            clean_meta = clean_metadata_for_chroma(metadata)
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            elif not isinstance(embedding, list):
                embedding = list(embedding)

            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[clean_meta]
            )
            self.stats["total_documents"] = self.get_index_size()
            return True

        except Exception as e:
            logger.error(f"❌ Error adding document: {str(e)}")
            return False

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        if not documents:
            return 0

        try:
            ids, texts, embeddings, metadatas = [], [], [], []

            for doc in documents:
                clean_meta = clean_metadata_for_chroma(doc.get("metadata", {}))
                embedding = doc.get("embedding", [])
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()
                elif not isinstance(embedding, list):
                    embedding = list(embedding)

                ids.append(doc.get("id", str(uuid.uuid4())))
                texts.append(doc.get("text", ""))
                embeddings.append(embedding)
                metadatas.append(clean_meta)

            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )

            self.stats["total_documents"] = self.get_index_size()
            logger.info(f"✅ {len(documents)} documents added")
            return len(documents)

        except Exception as e:
            logger.error(f"❌ Error adding documents: {str(e)}")
            return 0

    def delete_document(self, doc_id: str) -> bool:
        try:
            self.collection.delete(ids=[doc_id])
            self.stats["total_documents"] = self.get_index_size()
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting document: {str(e)}")
            return False

    def update_document(self, doc_id: str, text: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        try:
            self.collection.delete(ids=[doc_id])
            return self.add_document(doc_id, text, embedding, metadata)
        except Exception as e:
            logger.error(f"❌ Error updating document: {str(e)}")
            return False

    def clear(self) -> bool:
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
            self.stats["total_documents"] = 0
            logger.info("🗑️ Collection cleared")
            return True
        except Exception as e:
            logger.error(f"❌ Error clearing collection: {str(e)}")
            return False

    # ============================================================
    # طرق الاستعلام
    # ============================================================

    def get_all_documents(self) -> List[Dict[str, Any]]:
        try:
            results = self.collection.get(include=["documents", "metadatas"])
            documents = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"]):
                    documents.append({
                        "id": doc_id,
                        "text": results["documents"][i] if i < len(results["documents"]) else "",
                        "metadata": results["metadatas"][i] if i < len(results["metadatas"]) else {}
                    })
            return documents
        except Exception as e:
            logger.error(f"❌ Error getting all documents: {str(e)}")
            return []

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        try:
            results = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
            if results and results.get("ids") and len(results["ids"]) > 0:
                return {
                    "id": results["ids"][0],
                    "text": results["documents"][0] if results.get("documents") else "",
                    "metadata": results["metadatas"][0] if results.get("metadatas") else {}
                }
            return None
        except Exception as e:
            logger.error(f"❌ Error getting document: {str(e)}")
            return None

    def get_index_size(self) -> int:
        """✅ ترجع 0 بدون error لو المجموعة مش موجودة"""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def get_index_info(self) -> Dict[str, Any]:
        return {
            "status": "loaded" if self.is_loaded else "not_loaded",
            "collection_name": self.collection_name,
            "total_vectors": self.get_index_size(),
            "storage": "in-memory (EphemeralClient)"
        }

    def save(self) -> bool:
        logger.info("✅ EphemeralClient: no disk save needed")
        return True

    def _update_stats(self, count: int, elapsed: float) -> None:
        self.stats["total_searches"] += 1
        self.stats["last_search_time"] = elapsed
        total = self.stats["total_searches"]
        if total > 0:
            self.stats["avg_search_time"] = (
                (self.stats["avg_search_time"] * (total - 1) + elapsed) / total
            )

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "collection_name": self.collection_name,
            "storage": "in-memory",
            "is_loaded": self.is_loaded
        }

    def reset_stats(self) -> None:
        self.stats = {
            "total_documents": self.get_index_size(),
            "total_searches": 0,
            "avg_search_time": 0,
            "last_search_time": 0
        }
        logger.info("🔄 ChromaLoader stats reset")
