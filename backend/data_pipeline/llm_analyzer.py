"""
LLM 分析器 - 使用 Gemini API 进行深度分析
输出：词汇、搭配、句型分析
"""
import os
import logging
from typing import Optional, List

import google.generativeai as genai
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Pydantic 模型定义 (Enhanced)
class VocabularyItem(BaseModel):
    """词汇项"""
    word: str = Field(description="The single word or compound word exactly as it appears in the text (no extra notes)")
    pronunciation: str = Field(description="IPA pronunciation")
    definition: str = Field(description="Concise definition in the target language (and optionally English)")


class Collocation(BaseModel):
    """搭配短语"""
    phrase: str = Field(description="The fixed phrase/collocation (e.g., 'cast a ballot')")
    meaning: str = Field(description="Meaning in the target language")
    usage_tag: str = Field(description="Tag: Formal, Idiom, Business, etc.")
    original_sentence: str = Field(description="Full sentence from the text containing the phrase")


class SentencePattern(BaseModel):
    """句型结构"""
    skeleton: str = Field(description="Abstracted sentence structure (e.g., 'Not only ..., but also ...')")
    explanation: str = Field(description="Function explanation in the target language")
    source_sentence: str = Field(description="Original sentence from the text")
    new_example: str = Field(description="A new example sentence mimicking the pattern (with target language translation)")
    anchors: List[str] = Field(description="List of fixed word strings that form the pattern skeleton (e.g., ['Not only', 'but also']). These must exist verbatim in the source sentence.")


class ArticleAnalysisResult(BaseModel):
    """文章分析结果"""
    summary: str = Field(description="Article summary in the target language (approx. 20-30 words)")
    # level: str = Field(description="CEFR Level (B1, B2, C1, etc.)") # We use calculated level for now
    vocabulary: List[VocabularyItem] = Field(default_factory=list)
    collocations: List[Collocation] = Field(default_factory=list)
    sentence_patterns: List[SentencePattern] = Field(default_factory=list)


class LLMAnalyzer:
    """Gemini AI 分析器"""

    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=self.api_key)
        
        # 使用 Gemini 2.5 Flash (As used in sample)
        self.model_name = model_name or "models/gemini-2.5-flash"

    def _calculate_counts(self, word_count: int) -> dict:
        """Calculate analysis item counts based on word count"""
        count = word_count or 500
        # More aggressive ratios: ~1 vocab per 30 words, 1 collocation per 60 words
        vocab_target = max(10, min(30, int(count / 30)))
        colloc_target = max(5, min(15, int(count / 60)))
        patterns_target = max(3, min(8, int(count / 100)))
        
        return {
            "vocab": vocab_target,
            "colloc": colloc_target,
            "patterns": patterns_target
        }

    def get_system_prompt(self, target_language: str, counts: dict) -> str:
        """生成系统提示 (Enhanced from jzq_sample)"""
        return f"""
You are an expert ESL (English as a Second Language) teacher. Your task is to analyze English news articles to help advanced learners improve their reading, vocabulary, and writing skills.

You must analyze the provided Markdown text and output a JSON object strictly matching the requested schema.

**CRITICAL INSTRUCTION: TARGET LANGUAGE IS {target_language.upper()}**
For all fields involving explanations, definitions, translations, or summaries, you **MUST** provide the content in **{target_language}**.

**Analysis Scope:**
*   **Analyze the ENTIRE article from start to finish.** Do not stop after the first few paragraphs.
*   **Distribution**: Distribute your selected vocabulary and patterns evenly across the Introduction, Body, and Conclusion.

**Quantity Requirements:**
*   **Vocabulary**: Extract at least **{counts['vocab']}** significant words.
*   **Collocations**: Extract at least **{counts['colloc']}** useful phrases.
*   **Sentence Patterns**: Extract at least **{counts['patterns']}** key sentence structures.

**Analysis Requirements:**

1.  **Summary**:
    *   Provide a very concise summary of the article in **{target_language}**.
    *   **Length Constraint**: Strictly **20 to 30 words**.

2.  **Vocabulary**:
    *   Extract words that are specific to the estimated CEFR Level.
    *   Focus on challenging or academic words that an advanced learner should know.
    *   **Constraint**: 'word' field MUST be the word only. No brackets.
    *   Provide definitions in {target_language}.

3.  **Collocations** (Fixed Local Phrases):
    *   Identify fixed, native-like word combinations (e.g., 'cast a ballot', 'pose a threat', 'in stark contrast').
    *   Focus on phrases that make speech sound natural and "local".

4.  **Sentence Patterns** (Advanced Fixed Expressions):
    *   Identify **advanced fixed sentence structures** and rhetorical patterns.
    *   Examples: "Not only ... but also ...", "It remains to be seen whether ...", "No sooner ... than ...".
    *   Do NOT just pick long sentences. Look for **grammatical frames** that students can reuse in writing.
    *   **Anchors**: Identify the **fixed strings** that make up the pattern skeleton.
        *   Example for "Not only X, but also Y": `["Not only", "but also"]`
        *   These anchors MUST appear **verbatim** in the source sentence.

**CRITICAL: Data Integrity**
*   Ensure `anchors` are exact substrings of the `source_sentence`.
*   Ensure the `vocabulary` words actually exist in the text.
"""

    async def analyze_article(
        self,
        content: str,
        target_language: str = "English",
        difficulty_level: str = "B1",
        word_count: int = None
    ) -> Optional[ArticleAnalysisResult]:
        """
        分析文章
        """
        if not content or len(content) < 50:
            logger.warning("Content too short for analysis")
            return None

        try:
            logger.info("Starting LLM analysis with enhanced prompt...")

            if word_count is None:
                word_count = len(content.split())
            
            counts = self._calculate_counts(word_count)
            logger.info(f"Target counts: {counts}")

            system_prompt = self.get_system_prompt(target_language, counts)

            # 截取前 6000 字符 (increased from 4000 to cover more of longer articles)
            content_truncated = content[:6000]

            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
                generation_config={
                    "temperature": 0.3, # Increased slightly to avoid loops
                    "max_output_tokens": 8192, # Increased max tokens
                    "response_mime_type": "application/json",
                    "response_schema": ArticleAnalysisResult
                }
            )

            response = await model.generate_content_async(
                f"Analyze this WHOLE article carefully:\n\n{content_truncated}"
            )

            if not response.text:
                logger.warning("Empty Gemini response")
                return None

            # Validate using Pydantic
            try:
                analysis = ArticleAnalysisResult.model_validate_json(response.text)
                
                logger.info(f"LLM analysis complete: {len(analysis.vocabulary)} vocab, "
                           f"{len(analysis.collocations)} collocations, "
                           f"{len(analysis.sentence_patterns)} patterns")
                
                return analysis

            except Exception as parse_error:
                logger.error(f"JSON parse/validate failed: {parse_error}")
                logger.error(f"Raw response: {response.text[:500]}... [truncated]") # Log first 500 chars
                return None

        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return None

    def analyze_article_sync(
        self,
        content: str,
        target_language: str = "English",
        difficulty_level: str = "B1",
        word_count: int = None
    ) -> Optional[ArticleAnalysisResult]:
        """同步版本的分析方法"""
        import asyncio
        return asyncio.run(self.analyze_article(
            content, target_language, difficulty_level, word_count
        ))
