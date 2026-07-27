"""
🌾 عميل Groq API - SmartAgri

يتواصل مع واجهة Groq API لتوليد الإجابات على الأسئلة الزراعية
(Groq متوافق مع صيغة OpenAI Chat Completions)
"""

import json
import time
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime

from core.config import settings
from utils.logger import logger


class GroqClient:
    """
    عميل Groq API للمجال الزراعي

    يدعم:
    - توليد الإجابات الزراعية
    - تدفق الإجابات (Streaming)
    - متابعة المحادثات
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        """
        تهيئة عميل Groq للزراعة

        Args:
            api_key: مفتاح API (يؤخذ من الإعدادات إذا لم يتم توفيره)
            api_url: رابط API (يؤخذ من الإعدادات إذا لم يتم توفيره)
            model: اسم النموذج (يؤخذ من الإعدادات إذا لم يتم توفيره)
            timeout: مهلة الطلب بالثواني
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        self.api_url = api_url or settings.GROQ_API_URL
        self.model = model or settings.GROQ_MODEL
        self.timeout = timeout

        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "avg_response_time": 0,
            "last_request_time": 0
        }

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if not self.api_key or self.api_key == "":
            logger.warning(
                "⚠️ GROQ_API_KEY not set! "
                "محليًا: أضفه في .streamlit/secrets.toml — "
                "على Streamlit Cloud: أضفه من Manage app → Settings → Secrets"
            )

        logger.info(f"🌾 Groq Client initialized with model: {self.model} for SmartAgri")

    # ============================================================
    # الطريقة الرئيسية - توليد الإجابة
    # ============================================================

    async def generate(
        self,
        question: str,
        context: str = "",
        temperature: float = 0.7,
        max_tokens: int = 500,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        توليد إجابة زراعية باستخدام Groq API

        Args:
            question: سؤال المستخدم عن الزراعة
            context: السياق (النصوص المسترجعة الزراعية)
            temperature: درجة الإبداع (0-1)
            max_tokens: الحد الأقصى لعدد الرموز
            system_prompt: توجيه النظام (يؤخذ من الإعدادات إذا لم يتم توفيره)
            stream: تدفق الإجابة

        Returns:
            الإجابة النصية الزراعية
        """
        start_time = time.time()

        logger.info(f"🌾 Generating agricultural response for: {question[:50]}...")

        if not self.api_key:
            error_msg = "❌ GROQ_API_KEY not set. أضفه في Streamlit Secrets"
            logger.error(error_msg)
            return f"⚠️ {error_msg}"

        # ✅ تقليل حجم السياق إلى 3000 حرف كحد أقصى
        if len(context) > 3000:
            context = context[:3000] + "\n...(تم اختصار السياق لتقليل حجم الطلب)"

        messages = self._build_messages(
            question=question,
            context=context,
            system_prompt=system_prompt
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }

        try:
            if stream:
                response_text = await self._stream_request(payload)
            else:
                response_text = await self._sync_request(payload)

            elapsed = time.time() - start_time
            self._update_stats(len(response_text), elapsed)

            logger.info(f"✅ Agricultural response generated in {elapsed:.2f}s")

            return response_text

        except Exception as e:
            logger.error(f"❌ Error generating response: {str(e)}")
            return f"❌ خطأ: {str(e)}"

    # ============================================================
    # طرق الطلب
    # ============================================================

    async def _sync_request(self, payload: Dict[str, Any]) -> str:
        """
        إرسال طلب عادي (غير متدفق)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )

            if response.status_code != 200:
                error_msg = f"❌ API Error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg

            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                return "⚠️ لم يتم العثور على إجابة من النموذج"

    async def _stream_request(self, payload: Dict[str, Any]) -> str:
        """
        إرسال طلب مع تدفق
        """
        full_response = ""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                self.api_url,
                headers=self.headers,
                json=payload
            ) as response:

                if response.status_code != 200:
                    error_msg = f"❌ API Error: {response.status_code}"
                    logger.error(error_msg)
                    return error_msg

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_response += content
                        except json.JSONDecodeError:
                            continue

        return full_response

    # ============================================================
    # طرق مساعدة
    # ============================================================

    def _build_messages(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        بناء قائمة الرسائل للطلب
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            messages.append({
                "role": "system",
                "content": self._get_default_system_prompt(context)
            })

        if context and context.strip():
            messages.append({
                "role": "user",
                "content": f"المعلومات الزراعية المتاحة:\n{context}\n\nالسؤال: {question}"
            })
        else:
            messages.append({
                "role": "user",
                "content": f"{question}\n\nملاحظة: لا توجد معلومات زراعية كافية للإجابة على هذا السؤال."
            })

        return messages

    def _get_default_system_prompt(self, context: str) -> str:
        """
        الحصول على توجيه النظام الافتراضي للمجال الزراعي
        """
        if context and context.strip():
            return """أنت مساعد ذكي متخصص في مجال الزراعة والمحاصيل والتربة والري والأسمدة.
المهمة: استخدم المعلومات المتاحة في السياق للإجابة على أسئلة المستخدم الزراعية.
التعليمات:
1. أجب فقط بناءً على المعلومات الموجودة في السياق الزراعي
2. إذا لم تجد المعلومة في السياق، قل ذلك بوضوح
3. كن دقيقاً ومختصراً في الإجابة
4. استخدم اللغة العربية الفصحى
5. إذا ذكرت أرقاماً (كميات، إنتاجية، مساحات)، تأكد من دقتها
6. يمكنك تنظيم الإجابة في نقاط لتوضيح المعلومات الزراعية
7. استخدم مصطلحات زراعية دقيقة
"""
        else:
            return """أنت مساعد ذكي متخصص في مجال الزراعة والمحاصيل والتربة والري والأسمدة.
المهمة: أجب على أسئلة المستخدم الزراعية بأفضل طريقة ممكنة.
التعليمات:
1. إذا لم تعرف الإجابة، قل ذلك بوضوح
2. كن دقيقاً ومختصراً
3. استخدم اللغة العربية الفصحى
4. استخدم مصطلحات زراعية دقيقة
5. اقترح على المستخدم توفير معلومات إضافية إذا لزم الأمر
6. يمكنك تقديم معلومات عامة عن الزراعة إذا كانت مفيدة للسؤال
"""

    def _update_stats(self, tokens: int, elapsed: float) -> None:
        """
        تحديث الإحصائيات
        """
        self.stats["total_requests"] += 1
        self.stats["total_tokens"] += tokens
        self.stats["last_request_time"] = elapsed

        total = self.stats["total_requests"]
        if total > 0:
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (total - 1) + elapsed) / total
            )

    # ============================================================
    # طرق إضافية
    # ============================================================

    async def check_health(self) -> bool:
        """
        التحقق من صحة الاتصال بـ Groq API
        """
        if not self.api_key:
            return False

        try:
            test_response = await self.generate(
                question="Hello",
                context="",
                temperature=0.1,
                max_tokens=50
            )

            if not test_response.startswith("❌") and not test_response.startswith("⚠️"):
                logger.info("✅ Groq API health check passed")
                return True
            else:
                logger.warning(f"⚠️ Groq API health check failed: {test_response[:100]}")
                return False

        except Exception as e:
            logger.error(f"❌ Groq API health check error: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات العميل
        """
        return {
            **self.stats,
            "model": self.model,
            "api_url": self.api_url,
            "timeout": self.timeout
        }

    def reset_stats(self) -> None:
        """إعادة تعيين الإحصائيات"""
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "avg_response_time": 0,
            "last_request_time": 0
        }
        logger.info("🔄 Groq Client stats reset")

    def set_api_key(self, api_key: str) -> None:
        """
        تحديث مفتاح API
        """
        self.api_key = api_key
        self.headers["Authorization"] = f"Bearer {api_key}"
        logger.info("🔑 Groq API key updated")

    def set_model(self, model: str) -> None:
        """
        تحديث النموذج
        """
        self.model = model
        logger.info(f"🔄 Groq model updated to: {model}")
