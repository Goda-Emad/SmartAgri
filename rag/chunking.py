# app/rag/chunking.py
"""
✂️ تقسيم النصوص إلى أجزاء (Chunking)

يقوم بتقسيم النصوص الطويلة إلى أجزاء صغيرة مناسبة للمعالجة
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib


@dataclass
class Chunk:
    """
    قطعة نصية مع بياناتها الوصفية
    """
    id: str
    text: str
    metadata: Dict[str, Any]
    start_char: int
    end_char: int
    chunk_index: int


class Chunking:
    """
    تقسيم النصوص إلى أجزاء (Chunking)
    
    يدعم:
    - تقسيم حسب عدد الكلمات
    - تقسيم حسب عدد الأحرف
    - تقسيم حسب الجمل
    - تقسيم حسب الفقرات
    - تقسيم ذكي مع تداخل (Overlap)
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 50,
        separator: str = "\n\n",
        language: str = "ar"
    ):
        """
        تهيئة أداة التقسيم
        
        Args:
            chunk_size: حجم القطعة (عدد الكلمات)
            chunk_overlap: عدد الكلمات المتداخلة بين القطع
            min_chunk_size: الحد الأدنى لحجم القطعة
            separator: الفاصل بين الفقرات
            language: لغة النص (ar/en)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.separator = separator
        self.language = language
        
        # علامات الترقيم في العربية
        self.arabic_punctuation = "،؛؟.!"
        # علامات الترقيم في الإنجليزية
        self.english_punctuation = ",;?!."
    
    # ============================================================
    # طرق التقسيم المختلفة
    # ============================================================
    
    def chunk_by_words(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        تقسيم النص حسب عدد الكلمات
        
        Args:
            text: النص المراد تقسيمه
            metadata: بيانات وصفية إضافية
            
        Returns:
            قائمة بالقطع النصية
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # تنظيف النص
        text = self._clean_text(text)
        
        # تقسيم النص إلى كلمات
        words = text.split()
        
        if len(words) == 0:
            return []
        
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            # نهاية القطعة
            end = min(i + self.chunk_size, len(words))
            
            # تجميع الكلمات
            chunk_words = words[i:end]
            chunk_text = " ".join(chunk_words)
            
            # التحقق من الحجم
            if len(chunk_text) < self.min_chunk_size and i > 0:
                continue
            
            # إنشاء معرف فريد للقطعة
            chunk_id_str = self._generate_chunk_id(chunk_text, chunk_id)
            
            # إنشاء بيانات وصفية
            chunk_metadata = {
                "chunk_id": chunk_id,
                "start_word": i,
                "end_word": end - 1,
                "word_count": len(chunk_words),
                "char_count": len(chunk_text),
                "metadata": metadata or {}
            }
            
            # إنشاء القطعة
            chunk = Chunk(
                id=chunk_id_str,
                text=chunk_text,
                metadata=chunk_metadata,
                start_char=self._find_char_position(text, chunk_text, "start"),
                end_char=self._find_char_position(text, chunk_text, "end")
            )
            
            chunks.append(chunk)
            chunk_id += 1
            
            # إذا وصلنا للنهاية
            if end >= len(words):
                break
        
        return chunks
    
    def chunk_by_sentences(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        تقسيم النص حسب الجمل
        
        Args:
            text: النص المراد تقسيمه
            metadata: بيانات وصفية إضافية
            
        Returns:
            قائمة بالقطع النصية
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # تنظيف النص
        text = self._clean_text(text)
        
        # تقسيم إلى جمل
        sentences = self._split_sentences(text)
        
        if len(sentences) == 0:
            return []
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # إذا تجاوزت الجملة حجم القطعة وحدها
            if sentence_words > self.chunk_size:
                # أضف القطعة الحالية إذا كانت غير فارغة
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, chunk_id, text, metadata
                    ))
                    chunk_id += 1
                    current_chunk = []
                    current_length = 0
                
                # قسم الجملة الطويلة إلى أجزاء
                sub_chunks = self.chunk_by_words(sentence, metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata["chunk_id"] = chunk_id
                    chunks.append(sub_chunk)
                    chunk_id += 1
                
                continue
            
            # إذا تجاوزت القطعة الحالية الحجم المطلوب
            if current_length + sentence_words > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk, chunk_id, text, metadata
                ))
                chunk_id += 1
                
                # تداخل (Overlap) - احتفظ ببعض الجمل السابقة
                overlap_count = min(len(current_chunk), self.chunk_overlap // 10)
                current_chunk = current_chunk[-overlap_count:] if overlap_count > 0 else []
                current_length = sum(len(s.split()) for s in current_chunk)
            
            # أضف الجملة الحالية
            current_chunk.append(sentence)
            current_length += sentence_words
        
        # أضف القطعة الأخيرة
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, chunk_id, text, metadata
            ))
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        تقسيم النص حسب الفقرات
        
        Args:
            text: النص المراد تقسيمه
            metadata: بيانات وصفية إضافية
            
        Returns:
            قائمة بالقطع النصية
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # تنظيف النص
        text = self._clean_text(text)
        
        # تقسيم إلى فقرات
        paragraphs = text.split(self.separator)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if len(paragraphs) == 0:
            return []
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        
        for paragraph in paragraphs:
            para_words = len(paragraph.split())
            
            # إذا تجاوزت الفقرة حجم القطعة
            if para_words > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, chunk_id, text, metadata
                    ))
                    chunk_id += 1
                    current_chunk = []
                    current_length = 0
                
                # قسم الفقرة الطويلة إلى جمل
                sub_chunks = self.chunk_by_sentences(paragraph, metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata["chunk_id"] = chunk_id
                    chunks.append(sub_chunk)
                    chunk_id += 1
                
                continue
            
            # إذا تجاوزت القطعة الحالية الحجم
            if current_length + para_words > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk, chunk_id, text, metadata
                ))
                chunk_id += 1
                
                # تداخل (Overlap)
                overlap_count = min(len(current_chunk), self.chunk_overlap // 10)
                current_chunk = current_chunk[-overlap_count:] if overlap_count > 0 else []
                current_length = sum(len(p.split()) for p in current_chunk)
            
            # أضف الفقرة الحالية
            current_chunk.append(paragraph)
            current_length += para_words
        
        # أضف القطعة الأخيرة
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, chunk_id, text, metadata
            ))
        
        return chunks
    
    def chunk_by_characters(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        تقسيم النص حسب عدد الأحرف
        
        Args:
            text: النص المراد تقسيمه
            metadata: بيانات وصفية إضافية
            
        Returns:
            قائمة بالقطع النصية
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # تنظيف النص
        text = self._clean_text(text)
        
        # حجم القطعة بالأحرف
        char_size = self.chunk_size * 5  # تقريباً 5 أحرف لكل كلمة
        
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(text), char_size - self.chunk_overlap * 5):
            end = min(i + char_size, len(text))
            chunk_text = text[i:end]
            
            # حاول التقسيم عند علامات الترقيم
            chunk_text = self._find_good_cut(chunk_text)
            
            # التحقق من الحجم
            if len(chunk_text) < self.min_chunk_size and i > 0:
                continue
            
            # إنشاء معرف فريد للقطعة
            chunk_id_str = self._generate_chunk_id(chunk_text, chunk_id)
            
            # إنشاء بيانات وصفية
            chunk_metadata = {
                "chunk_id": chunk_id,
                "start_char": i,
                "end_char": i + len(chunk_text),
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "metadata": metadata or {}
            }
            
            # إنشاء القطعة
            chunk = Chunk(
                id=chunk_id_str,
                text=chunk_text,
                metadata=chunk_metadata,
                start_char=i,
                end_char=i + len(chunk_text)
            )
            
            chunks.append(chunk)
            chunk_id += 1
            
            if end >= len(text):
                break
        
        return chunks
    
    def chunk_smart(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        تقسيم ذكي - يختار أفضل طريقة حسب النص
        
        Args:
            text: النص المراد تقسيمه
            metadata: بيانات وصفية إضافية
            
        Returns:
            قائمة بالقطع النصية
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # تنظيف النص
        text = self._clean_text(text)
        
        # تحديد عدد الفقرات
        paragraphs = text.split(self.separator)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # إذا كان النص قصيراً
        if len(text.split()) < self.chunk_size:
            return self.chunk_by_words(text, metadata)
        
        # إذا كان النص يحتوي على فقرات
        if len(paragraphs) > 1:
            # تحقق من حجم الفقرات
            avg_para_size = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            
            if avg_para_size < self.chunk_size:
                return self.chunk_by_paragraphs(text, metadata)
        
        # إذا كان النص يحتوي على جمل
        sentences = self._split_sentences(text)
        if len(sentences) > 1:
            avg_sentence_size = sum(len(s.split()) for s in sentences) / len(sentences)
            
            if avg_sentence_size < self.chunk_size / 2:
                return self.chunk_by_sentences(text, metadata)
        
        # افتراضياً، استخدم التقسيم حسب الكلمات
        return self.chunk_by_words(text, metadata)
    
    # ============================================================
    # طرق مساعدة
    # ============================================================
    
    def _clean_text(self, text: str) -> str:
        """تنظيف النص"""
        # إزالة المسافات الزائدة
        text = re.sub(r'\s+', ' ', text)
        # إزالة الأسطر الفارغة المتعددة
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """تقسيم النص إلى جمل"""
        # تحديد علامات نهاية الجملة حسب اللغة
        if self.language == "ar":
            punctuation = self.arabic_punctuation
        else:
            punctuation = self.english_punctuation
        
        # تقسيم حسب علامات الترقيم
        pattern = f'[{punctuation}]'
        sentences = re.split(pattern, text)
        
        # تنظيف الجمل
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # إعادة إضافة علامات الترقيم
        result = []
        for i, sentence in enumerate(sentences):
            if i < len(sentences) - 1:
                # إعادة إضافة علامة الترقيم المناسبة
                if self.language == "ar":
                    sentence += "."
                else:
                    sentence += "."
            result.append(sentence)
        
        return result
    
    def _find_good_cut(self, text: str) -> str:
        """البحث عن مكان جيد للقطع"""
        # محاولة القطع عند نقطة أو فاصلة
        for punct in ['.', '؟', '!', '،', ';', '?', '!', ',']:
            if punct in text:
                cut_pos = text.rfind(punct)
                if cut_pos > len(text) * 0.5:
                    return text[:cut_pos + 1]
        
        # محاولة القطع عند مسافة
        if ' ' in text:
            cut_pos = text.rfind(' ', 0, len(text) - 1)
            if cut_pos > len(text) * 0.5:
                return text[:cut_pos]
        
        return text
    
    def _create_chunk(
        self,
        texts: List[str],
        chunk_id: int,
        original_text: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Chunk:
        """إنشاء قطعة من قائمة نصوص"""
        chunk_text = " ".join(texts)
        chunk_id_str = self._generate_chunk_id(chunk_text, chunk_id)
        
        chunk_metadata = {
            "chunk_id": chunk_id,
            "sentence_count": len(texts),
            "word_count": len(chunk_text.split()),
            "char_count": len(chunk_text),
            "metadata": metadata or {}
        }
        
        # إيجاد موقع القطعة في النص الأصلي
        start_pos = original_text.find(chunk_text[:50])
        if start_pos == -1:
            start_pos = 0
        end_pos = start_pos + len(chunk_text)
        
        return Chunk(
            id=chunk_id_str,
            text=chunk_text,
            metadata=chunk_metadata,
            start_char=start_pos,
            end_char=end_pos
        )
    
    def _generate_chunk_id(self, text: str, index: int) -> str:
        """إنشاء معرف فريد للقطعة"""
        # استخدام نص القطعة لتوليد معرف
        text_hash = hashlib.md5(text[:100].encode()).hexdigest()[:8]
        return f"chunk_{index}_{text_hash}"
    
    def _find_char_position(self, original: str, chunk: str, position: str) -> int:
        """إيجاد موضع القطعة في النص الأصلي"""
        if position == "start":
            return original.find(chunk[:50])
        else:
            # نهاية القطعة
            start = original.find(chunk[:50])
            if start != -1:
                return start + len(chunk)
            return 0
    
    # ============================================================
    # طرق مساعدة إضافية
    # ============================================================
    
    def get_chunk_statistics(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """
        الحصول على إحصائيات عن القطع
        
        Args:
            chunks: قائمة القطع
            
        Returns:
            إحصائيات عن القطع
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_word_count": 0,
                "avg_char_count": 0,
                "min_word_count": 0,
                "max_word_count": 0
            }
        
        word_counts = [chunk.metadata.get("word_count", len(chunk.text.split())) for chunk in chunks]
        char_counts = [chunk.metadata.get("char_count", len(chunk.text)) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_words": sum(word_counts),
            "total_chars": sum(char_counts),
            "avg_word_count": sum(word_counts) / len(chunks),
            "avg_char_count": sum(char_counts) / len(chunks),
            "min_word_count": min(word_counts),
            "max_word_count": max(word_counts),
            "chunk_ids": [chunk.id for chunk in chunks]
        }
    
    def merge_chunks(self, chunks: List[Chunk], max_chunk_size: int = 1000) -> List[Chunk]:
        """
        دمج القطع الصغيرة في قطع أكبر
        
        Args:
            chunks: قائمة القطع
            max_chunk_size: الحد الأقصى لحجم القطعة المدمجة
            
        Returns:
            قائمة بالقطع المدمجة
        """
        if not chunks:
            return []
        
        merged = []
        current_texts = []
        current_word_count = 0
        
        for chunk in chunks:
            word_count = chunk.metadata.get("word_count", len(chunk.text.split()))
            
            if current_word_count + word_count > max_chunk_size and current_texts:
                # دمج القطع الحالية
                merged_text = " ".join(current_texts)
                merged_metadata = {
                    "merged": True,
                    "original_chunks": len(current_texts),
                    "metadata": chunks[0].metadata.get("metadata", {})
                }
                
                merged_chunk = Chunk(
                    id=f"merged_{len(merged)}",
                    text=merged_text,
                    metadata=merged_metadata,
                    start_char=0,
                    end_char=len(merged_text)
                )
                merged.append(merged_chunk)
                current_texts = []
                current_word_count = 0
            
            current_texts.append(chunk.text)
            current_word_count += word_count
        
        # دمج القطع المتبقية
        if current_texts:
            merged_text = " ".join(current_texts)
            merged_metadata = {
                "merged": True,
                "original_chunks": len(current_texts),
                "metadata": chunks[0].metadata.get("metadata", {}) if chunks else {}
            }
            
            merged_chunk = Chunk(
                id=f"merged_{len(merged)}",
                text=merged_text,
                metadata=merged_metadata,
                start_char=0,
                end_char=len(merged_text)
            )
            merged.append(merged_chunk)
        
        return merged

