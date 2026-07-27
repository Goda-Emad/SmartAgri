# app/rag/reranker.py
"""
📊 إعادة ترتيب النتائج (Reranker)

يقوم بإعادة ترتيب المستندات المسترجعة حسب الأهمية باستخدام Cross-Encoder
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import hashlib
from dataclasses import dataclass, field
from datetime import datetime

# محاولة استيراد المكتبات المطلوبة
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    print("⚠️ CrossEncoder not available. Using simple reranking.")

from utils.logger import logger
from core.config import settings


@dataclass
class RerankedDocument:
    """
    مستند مع درجاته بعد إعادة الترتيب
    """
    id: str
    text: str
    metadata: Dict[str, Any]
    original_score: float
    rerank_score: float
    combined_score: float
    rank: int
    relevance_label: str  # high, medium, low


class Reranker:
    """
    إعادة ترتيب نتائج البحث
    
    يدعم:
    - Cross-Encoder لإعادة الترتيب
    - إعادة ترتيب بسيط بدون نموذج
    - دمج درجات متعددة
    - تصنيف النتائج حسب الأهمية
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        use_cross_encoder: bool = True,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        تهيئة أداة إعادة الترتيب
        
        Args:
            model_name: اسم نموذج Cross-Encoder
            use_cross_encoder: استخدام Cross-Encoder
            weights: أوزان الدمج المختلفة
        """
        self.model_name = model_name
        self.use_cross_encoder = use_cross_encoder and CROSS_ENCODER_AVAILABLE
        self.model = None
        
        # الأوزان الافتراضية للدمج
        self.weights = weights or {
            "relevance": 0.6,      # درجة المطابقة
            "recency": 0.15,       # الحداثة
            "popularity": 0.15,    # الشعبية
            "quality": 0.1         # الجودة
        }
        
        # تحميل النموذج إذا كان متاحاً
        if self.use_cross_encoder:
            try:
                self.model = CrossEncoder(model_name)
                logger.info(f"✅ Cross-Encoder loaded: {model_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load Cross-Encoder: {e}")
                self.use_cross_encoder = False
        
        self.stats = {
            "total_reranked": 0,
            "avg_rerank_time": 0,
            "last_rerank_time": 0
        }
        
        logger.info("📊 Reranker initialized")
    
    # ============================================================
    # الطريقة الرئيسية
    # ============================================================
    
    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        return_all: bool = False
    ) -> List[Dict[str, Any]]:
        """
        إعادة ترتيب المستندات حسب أهميتها للسؤال
        
        Args:
            query: سؤال المستخدم
            documents: قائمة المستندات المسترجعة
            top_k: عدد النتائج المطلوبة
            return_all: إرجاع جميع النتائج
            
        Returns:
            قائمة المستندات المرتبة
        """
        import time
        start_time = time.time()
        
        if not documents:
            return []
        
        logger.info(f"📊 Reranking {len(documents)} documents")
        
        # 1. حساب درجات إعادة الترتيب
        reranked_docs = await self._compute_rerank_scores(query, documents)
        
        # 2. ترتيب حسب الدرجة
        reranked_docs.sort(key=lambda x: x.combined_score, reverse=True)
        
        # 3. إضافة الترتيب والتسمية
        for i, doc in enumerate(reranked_docs):
            doc.rank = i + 1
            doc.relevance_label = self._get_relevance_label(doc.combined_score)
        
        # 4. تحويل إلى صيغة الإخراج
        result = []
        for doc in reranked_docs:
            result.append({
                "id": doc.id,
                "text": doc.text,
                "metadata": doc.metadata,
                "original_score": doc.original_score,
                "rerank_score": doc.rerank_score,
                "combined_score": doc.combined_score,
                "rank": doc.rank,
                "relevance_label": doc.relevance_label
            })
        
        # 5. تحديد عدد النتائج
        if not return_all and top_k:
            result = result[:top_k]
        
        # 6. تحديث الإحصائيات
        elapsed = time.time() - start_time
        self._update_stats(len(documents), elapsed)
        
        logger.info(f"✅ Reranked {len(result)} documents in {elapsed:.3f}s")
        
        return result
    
    # ============================================================
    # طرق حساب الدرجات
    # ============================================================
    
    async def _compute_rerank_scores(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[RerankedDocument]:
        """
        حساب درجات إعادة الترتيب لكل مستند
        
        Args:
            query: سؤال المستخدم
            documents: قائمة المستندات
            
        Returns:
            قائمة المستندات مع درجاتها
        """
        reranked = []
        
        # 1. حساب درجات Cross-Encoder
        cross_scores = []
        if self.use_cross_encoder and self.model:
            try:
                # تجهيز الأزواج (السؤال، النص)
                pairs = [[query, doc.get("text", "")] for doc in documents]
                cross_scores = self.model.predict(pairs)
                
                # تطبيع الدرجات
                if len(cross_scores) > 0:
                    max_score = max(cross_scores)
                    min_score = min(cross_scores)
                    if max_score > min_score:
                        cross_scores = [
                            (s - min_score) / (max_score - min_score)
                            for s in cross_scores
                        ]
                    else:
                        cross_scores = [0.5] * len(cross_scores)
            except Exception as e:
                logger.error(f"❌ Cross-Encoder error: {e}")
                cross_scores = [0.5] * len(documents)
        else:
            # استخدام الدرجات الأصلية إذا لم يتوفر Cross-Encoder
            cross_scores = [
                doc.get("relevance_score", 0.5)
                for doc in documents
            ]
        
        # 2. حساب الدرجات لكل مستند
        for i, doc in enumerate(documents):
            # الدرجة الأصلية
            original_score = doc.get("relevance_score", 0.5)
            
            # درجة Cross-Encoder (إعادة الترتيب)
            rerank_score = cross_scores[i] if i < len(cross_scores) else original_score
            
            # درجات إضافية
            recency_score = self._calculate_recency_score(doc)
            popularity_score = self._calculate_popularity_score(doc)
            quality_score = self._calculate_quality_score(doc)
            
            # دمج الدرجات
            combined_score = (
                self.weights["relevance"] * rerank_score +
                self.weights["recency"] * recency_score +
                self.weights["popularity"] * popularity_score +
                self.weights["quality"] * quality_score
            )
            
            # إنشاء الكائن
            reranked_doc = RerankedDocument(
                id=doc.get("id", f"doc_{i}"),
                text=doc.get("text", ""),
                metadata=doc.get("metadata", {}),
                original_score=original_score,
                rerank_score=rerank_score,
                combined_score=combined_score,
                rank=0,  # سيتم تحديثه لاحقاً
                relevance_label="medium"  # سيتم تحديثه لاحقاً
            )
            
            reranked.append(reranked_doc)
        
        return reranked
    
    # ============================================================
    # طرق حساب الدرجات الإضافية
    # ============================================================
    
    def _calculate_recency_score(self, doc: Dict[str, Any]) -> float:
        """
        حساب درجة الحداثة
        
        Args:
            doc: المستند
            
        Returns:
            درجة الحداثة (0-1)
        """
        metadata = doc.get("metadata", {})
        
        # محاولة استخراج التاريخ
        date_str = metadata.get("date_added") or metadata.get("modified_at")
        
        if not date_str:
            return 0.5  # قيمة افتراضية
        
        try:
            # محاولة تحويل التاريخ
            from datetime import datetime
            if isinstance(date_str, str):
                # محاولة تنسيقات مختلفة
                formats = [
                    "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%d/%m/%Y"
                ]
                
                for fmt in formats:
                    try:
                        doc_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return 0.5
                
                # حساب الفرق بالأيام
                now = datetime.now()
                days_diff = (now - doc_date).days
                
                # تحويل إلى درجة (كلما كان أحدث، كلما كانت الدرجة أعلى)
                if days_diff <= 30:
                    return 1.0
                elif days_diff <= 90:
                    return 0.8
                elif days_diff <= 180:
                    return 0.6
                elif days_diff <= 365:
                    return 0.4
                else:
                    return 0.2
                    
        except Exception:
            return 0.5
        
        return 0.5
    
    def _calculate_popularity_score(self, doc: Dict[str, Any]) -> float:
        """
        حساب درجة الشعبية (عدد الاستعلامات السابقة)
        
        Args:
            doc: المستند
            
        Returns:
            درجة الشعبية (0-1)
        """
        metadata = doc.get("metadata", {})
        
        # عدد مرات الاستعلام
        query_count = metadata.get("query_count", 0)
        
        if query_count <= 0:
            return 0.3
        
        # تحويل إلى درجة (كلما زادت الاستعلامات، زادت الدرجة)
        if query_count >= 100:
            return 1.0
        elif query_count >= 50:
            return 0.8
        elif query_count >= 20:
            return 0.6
        elif query_count >= 5:
            return 0.4
        else:
            return 0.3
    
    def _calculate_quality_score(self, doc: Dict[str, Any]) -> float:
        """
        حساب درجة الجودة
        
        Args:
            doc: المستند
            
        Returns:
            درجة الجودة (0-1)
        """
        metadata = doc.get("metadata", {})
        
        # 1. جودة النص (طول النص)
        text = doc.get("text", "")
        text_length = len(text)
        
        if text_length >= 1000:
            length_score = 1.0
        elif text_length >= 500:
            length_score = 0.8
        elif text_length >= 200:
            length_score = 0.5
        else:
            length_score = 0.3
        
        # 2. وجود بيانات وصفية كاملة
        metadata_score = 0.0
        required_fields = ["filename", "category"]
        for field in required_fields:
            if field in metadata and metadata[field]:
                metadata_score += 0.5
        
        # 3. درجة الجودة من التقرير (إذا كانت موجودة)
        quality_score = metadata.get("quality_score", 0)
        if isinstance(quality_score, (int, float)):
            quality_score = quality_score / 100  # تطبيع
        else:
            quality_score = 0.5
        
        # 4. دمج الدرجات
        combined = (
            length_score * 0.4 +
            metadata_score * 0.3 +
            quality_score * 0.3
        )
        
        return min(max(combined, 0.0), 1.0)
    
    # ============================================================
    # طرق مساعدة
    # ============================================================
    
    def _get_relevance_label(self, score: float) -> str:
        """
        الحصول على تسمية الأهمية بناءً على الدرجة
        
        Args:
            score: درجة الأهمية
            
        Returns:
            تسمية الأهمية (high, medium, low)
        """
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _update_stats(self, count: int, elapsed: float) -> None:
        """
        تحديث الإحصائيات
        
        Args:
            count: عدد المستندات
            elapsed: زمن المعالجة
        """
        self.stats["total_reranked"] += count
        self.stats["last_rerank_time"] = elapsed
        
        # تحديث المتوسط
        total = self.stats["total_reranked"]
        if total > 0:
            self.stats["avg_rerank_time"] = (
                (self.stats["avg_rerank_time"] * (total - count) +
                 elapsed * count) / total
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات إعادة الترتيب
        
        Returns:
            إحصائيات إعادة الترتيب
        """
        return {
            **self.stats,
            "model_name": self.model_name,
            "use_cross_encoder": self.use_cross_encoder,
            "weights": self.weights
        }
    
    def reset(self) -> None:
        """
        إعادة تعيين الإحصائيات
        """
        self.stats = {
            "total_reranked": 0,
            "avg_rerank_time": 0,
            "last_rerank_time": 0
        }
        logger.info("🔄 Reranker stats reset")
    
    # ============================================================
    # طرق إضافية
    # ============================================================
    
    async def rerank_by_metadata(
        self,
        documents: List[Dict[str, Any]],
        sort_by: str = "relevance",
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        إعادة ترتيب المستندات حسب البيانات الوصفية
        
        Args:
            documents: قائمة المستندات
            sort_by: حقل الترتيب
            ascending: ترتيب تصاعدي
            
        Returns:
            قائمة المستندات المرتبة
        """
        if not documents:
            return []
        
        # استخراج القيم
        def get_value(doc):
            if sort_by in doc:
                return doc[sort_by]
            elif sort_by in doc.get("metadata", {}):
                return doc["metadata"][sort_by]
            else:
                return 0
        
        # ترتيب
        result = sorted(documents, key=get_value, reverse=not ascending)
        
        # إضافة الترتيب
        for i, doc in enumerate(result, 1):
            doc["rank"] = i
        
        return result
    
    async def filter_by_threshold(
        self,
        documents: List[Dict[str, Any]],
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        تصفية المستندات حسب درجة الأهمية
        
        Args:
            documents: قائمة المستندات
            threshold: الحد الأدنى للقبول
            
        Returns:
            قائمة المستندات المقبولة
        """
        if not documents:
            return []
        
        return [
            doc for doc in documents
            if doc.get("combined_score", doc.get("relevance_score", 0)) >= threshold
        ]
    
    def get_top_k_by_category(
        self,
        documents: List[Dict[str, Any]],
        category: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        الحصول على أفضل النتائج من تصنيف معين
        
        Args:
            documents: قائمة المستندات
            category: التصنيف المطلوب
            top_k: عدد النتائج
            
        Returns:
            قائمة المستندات من التصنيف المطلوب
        """
        # تصفية حسب التصنيف
        filtered = []
        for doc in documents:
            doc_category = doc.get("metadata", {}).get("category", "")
            if doc_category == category:
                filtered.append(doc)
        
        # ترتيب حسب الدرجة
        filtered.sort(key=lambda x: x.get("combined_score", x.get("relevance_score", 0)), reverse=True)
        
        return filtered[:top_k]

