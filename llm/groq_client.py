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
        start_time = time.time()

        logger.info(f"🌾 Generating agricultural response for: {question[:50]}...")

        if not self.api_key:
            error_msg = "❌ GROQ_API_KEY not set. أضفه في Streamlit Secrets"
            logger.error(error_msg)
            return f"⚠️ {error_msg}"

        # ✅ تقليل حجم السياق إلى 3000 حرف كحد أقصى
        if len(context) > 3000:
            context = context[:3000] + "\n...(context truncated)"

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
                "content": f"Agricultural context:\n{context}\n\nQuestion: {question}"
            })
        else:
            messages.append({
                "role": "user",
                "content": question
            })

        return messages

    def _get_default_system_prompt(self, context: str) -> str:
        """
        ✅ System prompt محايد يرد بنفس لغة السؤال تلقائياً
        """
        if context and context.strip():
            return """You are SmartAgri, an intelligent assistant specialized in agriculture, crops, soil, irrigation, and fertilizers.

Instructions:
1. Answer ONLY based on the information provided in the context
2. If the information is not in the context, clearly say so
3. Be accurate and concise
4. CRITICAL: Always respond in the same language the user used. If the question is in Arabic, respond in Arabic. If in English, respond in English.
5. If you mention numbers (quantities, yields, areas), ensure their accuracy
6. You can organize the answer in bullet points
7. Use precise agricultural terminology
"""
        else:
            return """You are SmartAgri, an intelligent assistant specialized in agriculture, crops, soil, irrigation, and fertilizers.

Instructions:
1. Answer the user's agricultural questions as helpfully as possible
2. If you don't know the answer, say so clearly
3. Be accurate and concise
4. CRITICAL: Always respond in the same language the user used. If the question is in Arabic, respond in Arabic. If in English, respond in English.
5. Use precise agricultural terminology
6. You can provide general agricultural information when helpful
"""

    def _update_stats(self, tokens: int, elapsed: float) -> None:
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
        return {
            **self.stats,
            "model": self.model,
            "api_url": self.api_url,
            "timeout": self.timeout
        }

    def reset_stats(self) -> None:
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "avg_response_time": 0,
            "last_request_time": 0
        }
        logger.info("🔄 Groq Client stats reset")

    def set_api_key(self, api_key: str) -> None:
        self.api_key = api_key
        self.headers["Authorization"] = f"Bearer {api_key}"
        logger.info("🔑 Groq API key updated")

    def set_model(self, model: str) -> None:
        self.model = model
        logger.info(f"🔄 Groq model updated to: {model}")
