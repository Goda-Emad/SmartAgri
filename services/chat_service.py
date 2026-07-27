import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from rag.qa_engine import QAEngine
from rag.retriever import Retriever
from rag.reranker import Reranker
from llm.groq_client import GroqClient
from core.config import settings
from core.prompts import get_system_prompt
from utils.logger import logger


class ChatService:
    """
    خدمة المحادثة الزراعية - SmartAgri
    إدارة RAG والرد على الأسئلة الزراعية
    """
    
    def __init__(
        self,
        qa_engine=None,
        retriever=None,
        reranker=None,
        llm_client=None,
        max_history: int = 50
    ):
        self.retriever = retriever or Retriever()
        self.reranker = reranker or Reranker()
        self.llm_client = llm_client or GroqClient()
        self.qa_engine = qa_engine or QAEngine(
            retriever=self.retriever,
            reranker=self.reranker,
            llm=self.llm_client
        )
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.stats = {
            "total_conversations": 0,
            "total_messages": 0,
            "total_questions": 0
        }
        logger.info("🌾 ChatService initialized")

    async def process_question(
        self,
        question: str,
        session_id: Optional[str] = None,
        max_sources: int = 3,
        temperature: float = 0.7,
        include_sources: bool = True,
        filter_category: Optional[str] = None,
        filter_farm: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        معالجة سؤال المستخدم في المجال الزراعي
        
        Args:
            question: سؤال المستخدم
            session_id: معرف الجلسة
            max_sources: الحد الأقصى للمصادر
            temperature: درجة الحرارة للنموذج
            include_sources: تضمين المصادر
            filter_category: تصفية حسب التصنيف (crops, soil, irrigation, fertilizers, pests)
            filter_farm: تصفية حسب المزرعة/المحصول
            
        Returns:
            النتيجة مع الإجابة والمصادر
        """
        logger.info(f"🌾 Processing question: {question[:50]}...")

        if not session_id:
            session_id = str(uuid.uuid4())

        user_message = {
            "role": "user",
            "content": question,
            "timestamp": datetime.now().isoformat()
        }
        self._add_message(session_id, user_message)

        try:
            context = self._get_conversation_context(session_id, max_messages=3)
            
            # ✅ اقتصاص السياق إذا كان كبيراً جداً
            if context and len(context) > 2000:
                context = context[:2000] + "\n...(تم اختصار سياق المحادثة السابقة)"
            
            result = await self.qa_engine.answer(
                question=question,
                max_sources=max_sources,
                temperature=temperature,
                include_sources=include_sources,
                filter_category=filter_category,
                filter_farm=filter_farm,
                context=context,
                **kwargs
            )

            assistant_message = {
                "role": "assistant",
                "content": result.answer,
                "sources": result.sources,
                "confidence_score": result.confidence_score,
                "timestamp": datetime.now().isoformat()
            }
            self._add_message(session_id, assistant_message)
            self.stats["total_questions"] += 1

            return {
                "answer": result.answer,
                "sources": result.sources if include_sources else [],
                "session_id": session_id,
                "question_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "confidence_score": result.confidence_score,
                "processing_time": result.processing_time,
                "total_documents": result.retrieved_count,
                "retrieved_count": result.reranked_count
            }

        except Exception as e:
            logger.error(f"❌ Error processing question: {str(e)}")
            error_message = {
                "role": "assistant",
                "content": f"❌ حدث خطأ: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            self._add_message(session_id, error_message)
            raise

    def process_question_sync(self, question: str, session_id=None, **kwargs) -> Dict[str, Any]:
        """معالجة السؤال بشكل متزامن"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            self.process_question(question=question, session_id=session_id, **kwargs)
        )

    def _add_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """إضافة رسالة إلى المحادثة"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
            self.stats["total_conversations"] += 1
        self.conversations[session_id].append(message)
        self.stats["total_messages"] += 1
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]

    def _get_conversation_context(self, session_id: str, max_messages: int = 3) -> str:
        """الحصول على سياق المحادثة"""
        if session_id not in self.conversations:
            return ""
        messages = self.conversations[session_id]
        recent = messages[-max_messages * 2:]
        context_parts = []
        for msg in recent:
            role = "المستخدم" if msg["role"] == "user" else "المساعد"
            context_parts.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(context_parts)

    def get_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """الحصول على محادثة كاملة"""
        return self.conversations.get(session_id, [])

    def clear_conversation(self, session_id: str) -> bool:
        """مسح محادثة"""
        if session_id in self.conversations:
            self.conversations[session_id] = []
            return True
        return False

    def get_suggested_questions(self, limit: int = 6) -> List[Dict[str, Any]]:
        """الحصول على أسئلة زراعية مقترحة"""
        suggestions = [
            {"question": "ما هي أفضل طرق إدارة المحاصيل؟", "category": "crops"},
            {"question": "كيف أتعامل مع آفة الحشائش في الزراعة؟", "category": "pests"},
            {"question": "ما هي طرق الري الحديثة الموفرة للمياه؟", "category": "irrigation"},
            {"question": "كيف أحلل التربة قبل الزراعة؟", "category": "soil"},
            {"question": "ما هي العناصر الغذائية الأساسية للمحاصيل؟", "category": "fertilizers"},
            {"question": "ما هي أفضل أنواع الأسمدة لمحصول القمح؟", "category": "fertilizers"},
        ]
        return suggestions[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الخدمة"""
        return {**self.stats, "active_conversations": len(self.conversations)}
