"""
🧠 محرك الأسئلة والأجوبة (QA Engine) - SmartAgri

يدير تدفق RAG بالكامل للمجال الزراعي:
1. استرجاع المستندات الزراعية
2. إعادة ترتيب النتائج
3. بناء السياق
4. توليد الإجابة
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import time
import hashlib
from datetime import datetime

from rag.retriever import Retriever
from rag.reranker import Reranker
from rag.chunking import Chunking, Chunk
from llm.groq_client import GroqClient
from core.config import settings
from core.prompts import get_rag_prompt, get_system_prompt
from utils.logger import logger


@dataclass
class QAResult:
    """
    نتيجة محرك الأسئلة والأجوبة
    """
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float
    retrieved_count: int
    reranked_count: int
    chunks_used: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class QAEngine:
    """
    محرك الأسئلة والأجوبة (RAG Pipeline) - للمجال الزراعي
    
    يقوم بتنفيذ تدفق RAG بالكامل:
    1. استرجاع المستندات من ChromaDB
    2. إعادة ترتيب النتائج
    3. بناء السياق
    4. توليد الإجابة باستخدام LLM
    """
    
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        reranker: Optional[Reranker] = None,
        chunking: Optional[Chunking] = None,
        llm: Optional[GroqClient] = None
    ):
        """
        تهيئة محرك الأسئلة والأجوبة
        
        Args:
            retriever: أداة الاسترجاع
            reranker: أداة إعادة الترتيب
            chunking: أداة التقسيم
            llm: عميل النموذج اللغوي
        """
        self.retriever = retriever or Retriever()
        self.reranker = reranker or Reranker()
        self.chunking = chunking or Chunking()
        self.llm = llm or GroqClient()
        
        self.default_top_k = settings.DEFAULT_TOP_K
        self.default_max_sources = settings.DEFAULT_MAX_SOURCES
        self.min_confidence = settings.MIN_CONFIDENCE_SCORE
        
        logger.info("🌾 QA Engine initialized successfully for SmartAgri")
    
    # ============================================================
    # الطريقة الرئيسية
    # ============================================================
    
    async def answer(
        self,
        question: str,
        top_k: int = None,
        max_sources: int = None,
        temperature: float = None,
        include_sources: bool = True,
        filter_category: Optional[str] = None,
        filter_farm: Optional[str] = None,
        context: str = "",
        **kwargs
    ) -> QAResult:
        """
        الإجابة على سؤال زراعي باستخدام RAG
        
        Args:
            question: سؤال المستخدم عن الزراعة
            top_k: عدد المستندات المسترجعة
            max_sources: الحد الأقصى للمصادر
            temperature: درجة الإبداع
            include_sources: عرض المصادر
            filter_category: تصفية حسب التصنيف (crops, soil, irrigation, fertilizers, pests)
            filter_farm: تصفية حسب المزرعة/المحصول
            context: سياق إضافي (من المحادثة السابقة)
            
        Returns:
            QAResult: نتيجة السؤال
        """
        import time
        start_time = time.time()
        
        logger.info(f"🌾 Processing agricultural question: {question[:50]}...")
        
        # 1. إعداد المعلمات
        top_k = top_k or self.default_top_k
        max_sources = max_sources or self.default_max_sources
        temperature = temperature or settings.DEFAULT_TEMPERATURE
        
        # ✅ التحقق مما إذا كان السؤال عاماً (لا يحتاج إلى استرجاع مستندات)
        is_general_question = self._is_general_question(question)
        
        if is_general_question:
            logger.info(f"💬 سؤال عام تم اكتشافه: {question[:50]}... - سيتم الرد بدون استرجاع مستندات")
            # الإجابة على السؤال العام بدون سياق
            full_context = ""
            retrieved_docs = []
            reranked_docs = []
            retrieved_count = 0
            reranked_count = 0
            chunks_used = 0
            
            # توليد الإجابة بدون سياق
            answer = await self.llm.generate(
                question=question,
                context="",
                temperature=temperature,
                system_prompt=kwargs.get("system_prompt") or self._get_general_system_prompt()
            )
            
            confidence_score = 0.8  # ثقة عالية في الأسئلة العامة
            sources = []
            
        else:
            # 2. تحسين السؤال (للأسئلة الزراعية)
            enhanced_question = self._enhance_question(question)
            
            # 3. استرجاع المستندات
            retrieved_docs = await self.retriever.retrieve(
                query=enhanced_question,
                top_k=top_k,
                filter_category=filter_category,
                filter_farm=filter_farm
            )
            
            retrieved_count = len(retrieved_docs)
            logger.info(f"📚 Retrieved {retrieved_count} agricultural documents")
            
            # 4. إعادة ترتيب النتائج
            reranked_docs = await self.reranker.rerank(
                query=question,
                documents=retrieved_docs,
                top_k=max_sources
            )
            
            reranked_count = len(reranked_docs)
            logger.info(f"📊 Reranked to {reranked_count} documents")
            
            # 5. بناء السياق
            built_context = self._build_context(reranked_docs)
            
            # دمج السياق الإضافي (من المحادثة السابقة)
            if context and context.strip():
                full_context = f"سياق المحادثة السابقة:\n{context}\n\nمعلومات من المستندات الزراعية:\n{built_context}"
            else:
                full_context = built_context
            
            # ✅ اقتصاص السياق الكامل إذا كان كبيراً جداً (حماية إضافية)
            if len(full_context) > 3000:
                full_context = full_context[:3000] + "\n...(تم اختصار السياق لتقليل حجم الطلب)"
            
            chunks_used = len(reranked_docs)
            
            # 6. توليد الإجابة
            answer = await self.llm.generate(
                question=question,
                context=full_context,
                temperature=temperature,
                system_prompt=kwargs.get("system_prompt")
            )
            
            # 7. حساب درجة الثقة
            confidence_score = self._calculate_confidence(
                reranked_docs,
                len(answer),
                chunks_used
            )
            
            # 8. تجهيز المصادر
            sources = []
            if include_sources:
                sources = self._format_sources(reranked_docs)
        
        # 9. حساب زمن المعالجة
        processing_time = time.time() - start_time
        
        # 10. بناء النتيجة
        result = QAResult(
            question=question,
            answer=answer,
            sources=sources,
            confidence_score=confidence_score,
            processing_time=processing_time,
            retrieved_count=retrieved_count,
            reranked_count=reranked_count,
            chunks_used=chunks_used,
            metadata={
                "temperature": temperature,
                "top_k": top_k,
                "max_sources": max_sources,
                "filter_category": filter_category,
                "filter_farm": filter_farm,
                "is_general_question": is_general_question
            }
        )
        
        logger.info(f"✅ Agricultural answer generated in {processing_time:.2f}s")
        
        return result
    
    # ============================================================
    # طرق بناء السياق
    # ============================================================
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        بناء السياق من المستندات الزراعية المسترجعة
        
        Args:
            documents: قائمة المستندات
            
        Returns:
            النص السياقي
        """
        if not documents:
            return "لا توجد معلومات كافية للإجابة على هذا السؤال الزراعي."
        
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            # إضافة رقم المستند ومصدره
            source = doc.get("metadata", {}).get("filename", f"مصدر {i}")
            category = doc.get("metadata", {}).get("category", "غير مصنف")
            relevance = doc.get("relevance_score", 0.0)
            
            # ✅ اقتصاص النص إلى 500 حرف كحد أقصى لكل مستند
            text_content = doc.get('text', '')
            if len(text_content) > 500:
                text_content = text_content[:500] + "..."
            
            context_parts.append(f"[{i}] المصدر: {source}")
            context_parts.append(f"    التصنيف الزراعي: {category}")
            context_parts.append(f"    درجة المطابقة: {relevance:.2%}")
            context_parts.append(f"    المحتوى:\n    {text_content}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _build_context_chunks(self, chunks: List[Chunk]) -> str:
        """
        بناء السياق من قطع النصوص الزراعية
        
        Args:
            chunks: قائمة القطع النصية
            
        Returns:
            النص السياقي
        """
        if not chunks:
            return "لا توجد معلومات كافية."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get("metadata", {}).get("filename", f"مصدر {i}")
            # ✅ اقتصاص النص إلى 500 حرف كحد أقصى لكل قطعة
            text_content = chunk.text
            if len(text_content) > 500:
                text_content = text_content[:500] + "..."
            context_parts.append(f"[{i}] {source}:")
            context_parts.append(text_content)
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    # ============================================================
    # طرق حساب الثقة
    # ============================================================
    
    def _calculate_confidence(
        self,
        documents: List[Dict[str, Any]],
        answer_length: int,
        chunks_used: int
    ) -> float:
        """
        حساب درجة الثقة في الإجابة الزراعية
        
        Args:
            documents: المستندات المستخدمة
            answer_length: طول الإجابة
            chunks_used: عدد القطع المستخدمة
            
        Returns:
            درجة الثقة (0-1)
        """
        if not documents:
            return 0.0
        
        # 1. متوسط درجة المطابقة
        avg_relevance = sum(
            doc.get("relevance_score", 0.0) for doc in documents
        ) / len(documents)
        
        # 2. عدد المستندات المستخدمة
        doc_score = min(chunks_used / 5, 1.0)  # 5 مستندات كحد أقصى للثقة
        
        # 3. طول الإجابة
        length_score = min(answer_length / 200, 1.0)  # 200 حرف كحد أقصى
        
        # 4. وجود مستندات
        has_docs_score = 1.0 if chunks_used > 0 else 0.0
        
        # الوزن النهائي
        confidence = (
            avg_relevance * 0.5 +      # 50% من درجة المطابقة
            doc_score * 0.2 +          # 20% من عدد المستندات
            length_score * 0.2 +       # 20% من طول الإجابة
            has_docs_score * 0.1       # 10% من وجود مستندات
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    # ============================================================
    # طرق تحسين الأسئلة
    # ============================================================
    
    def _enhance_question(self, question: str) -> str:
        """
        تحسين السؤال الزراعي لتحسين جودة الاسترجاع
        
        Args:
            question: السؤال الأصلي
            
        Returns:
            السؤال المحسن
        """
        # إزالة علامات الترقيم الزائدة
        question = question.strip()
        
        # إذا كان السؤال قصيراً، حاول توسيعه
        if len(question.split()) < 3:
            # إضافة كلمات مفتاحية عامة
            question = f"{question} معلومات تفاصيل زراعية"
        
        return question
    
    def _extract_keywords(self, question: str) -> List[str]:
        """
        استخراج الكلمات المفتاحية الزراعية من السؤال
        
        Args:
            question: السؤال
            
        Returns:
            قائمة الكلمات المفتاحية الزراعية
        """
        # كلمات شائعة في الزراعة
        agricultural_keywords = [
            "محصول", "تربة", "ري", "سماد", "آفة", "حشائش",
            "قمح", "أرز", "ذرة", "شعير", "طماطم", "بطاطس",
            "مياه", "نبات", "بذور", "تقاوي", "موسم", "حصاد",
            "إنتاجية", "جودة", "تغذية", "عناصر", "مكافحة",
            "زراعة", "أرض", "مناخ", "درجة", "رطوبة",
            "مزرعة", "حقل", "خضروات", "فواكه", "زيتون",
            "تمر", "عنب", "موز", "برتقال", "ليمون"
        ]
        
        words = question.split()
        keywords = []
        
        for word in words:
            # إزالة علامات الترقيم
            clean_word = word.strip("،؛؟!.،")
            if clean_word in agricultural_keywords:
                keywords.append(clean_word)
        
        return keywords
    
    # ============================================================
    # طرق تنسيق النتائج
    # ============================================================
    
    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        تنسيق المصادر الزراعية للعرض
        
        Args:
            documents: قائمة المستندات
            
        Returns:
            قائمة المصادر المنسقة
        """
        sources = []
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            
            # ✅ اقتصاص المحتوى للمصادر أيضاً
            content = doc.get("text", "")
            if len(content) > 300:
                content = content[:300] + "..."
            
            source = {
                "id": doc.get("id", ""),
                "filename": metadata.get("filename", "مصدر غير معروف"),
                "category": metadata.get("category", "غير مصنف"),
                "content": content,
                "relevance_score": doc.get("relevance_score", 0.0),
                "preview": self._get_preview(doc.get("text", ""))
            }
            
            sources.append(source)
        
        return sources
    
    def _get_preview(self, text: str, max_length: int = 200) -> str:
        """
        الحصول على معاينة للنص
        
        Args:
            text: النص الكامل
            max_length: الحد الأقصى لطول المعاينة
            
        Returns:
            معاينة النص
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # قطع عند أقرب مسافة
        preview = text[:max_length]
        last_space = preview.rfind(' ')
        
        if last_space > 0:
            preview = preview[:last_space]
        
        return preview + "..."
    
    # ============================================================
    # ✅ طرق جديدة للكشف عن الأسئلة العامة
    # ============================================================
    
    def _is_general_question(self, question: str) -> bool:
        """
        التحقق مما إذا كان السؤال عاماً (لا يحتاج إلى استرجاع مستندات)
        
        Args:
            question: السؤال
            
        Returns:
            True إذا كان السؤال عاماً، False إذا كان يحتاج إلى مستندات
        """
        question_lower = question.lower().strip()
        
        # قائمة الكلمات والعبارات التي تشير إلى أسئلة عامة
        general_patterns = [
            "السلام عليكم",
            "وعليكم السلام",
            "صباح الخير",
            "مساء الخير",
            "مرحبا",
            "اهلا",
            "كيف حالك",
            "شكرا",
            "thank you",
            "hello",
            "hi",
            "good morning",
            "good evening",
            "how are you",
            "مع السلامة",
            "باي",
            "bye"
        ]
        
        # التحقق من تطابق السؤال مع أي من الأنماط العامة
        for pattern in general_patterns:
            if pattern in question_lower:
                return True
        
        # إذا كان السؤال قصيراً جداً (أقل من 3 كلمات) ولا يحتوي على كلمات مفتاحية زراعية
        if len(question.split()) <= 2:
            # التحقق مما إذا كانت الكلمات مفتاحية زراعية
            keywords = self._extract_keywords(question)
            if len(keywords) == 0:
                return True
        
        return False
    
    def _get_general_system_prompt(self) -> str:
        """
        الحصول على توجيه النظام للأسئلة العامة - SmartAgri
        
        Returns:
            توجيه النظام للأسئلة العامة للمجال الزراعي (بالإنجليزية)
        """
        return """You are a helpful and polite AI assistant - SmartAgri.
The user is greeting you or asking a general question.
Instructions:
1. Respond with an appropriate and polite greeting
2. Use clear English language
3. Be friendly and respectful
4. Remind the user that you are here to help with agricultural questions about crops, soil, irrigation, and fertilizers
5. Suggest asking specific questions about the available agricultural documents
"""
    
    # ============================================================
    # طرق مساعدة
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات المحرك
        
        Returns:
            إحصائيات المحرك
        """
        return {
            "retriever_stats": self.retriever.get_stats(),
            "reranker_stats": self.reranker.get_stats(),
            "default_top_k": self.default_top_k,
            "default_max_sources": self.default_max_sources,
            "min_confidence": self.min_confidence
        }
    
    def reset(self) -> None:
        """
        إعادة تعيين المحرك
        """
        self.retriever.reset()
        self.reranker.reset()
        logger.info("🔄 QA Engine reset")
