"""
题目生成器模块
使用 LLM 为文章生成完形填空和判断题
"""
import os
import json
import random
from typing import List, Dict, Any, Optional
from huggingface_hub import InferenceClient


class QuestionGenerator:
    """题目生成器"""
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-72B-Instruct", token: str = None):
        """
        初始化题目生成器
        
        Args:
            model_name: HuggingFace 模型名称
            token: HuggingFace API Token
        """
        self.model_name = model_name
        self.token = token or os.environ.get("HF_TOKEN", "")
        
        # 新版本huggingface_hub会自动路由到正确的endpoint
        self.client = InferenceClient(model=self.model_name, token=self.token)
    
    def generate_cloze_questions(
        self, 
        article_content: str, 
        num_questions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        生成完形填空题
        
        Args:
            article_content: 文章内容
            num_questions: 生成题目数量
            
        Returns:
            题目列表，每个题目包含 target_word, options, explanation
        """
        prompt = self._build_cloze_prompt(article_content, num_questions)
        return self._call_llm(prompt)
    
    def generate_true_false_questions(
        self, 
        article_content: str, 
        num_questions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        生成判断题
        
        Args:
            article_content: 文章内容
            num_questions: 生成题目数量
            
        Returns:
            题目列表，每个题目包含 statement, answer, explanation
        """
        prompt = self._build_true_false_prompt(article_content, num_questions)
        return self._call_llm(prompt)
    
    def _build_cloze_prompt(self, article_content: str, num_questions: int) -> str:
        """构建完形填空题 Prompt"""
        seed = random.randint(1, 100000)
        return f"""
You are an English test generator. [Random Seed: {seed}]
Task: Identify {num_questions} distinct words in the article for Cloze questions.
Requirements:
0. Select {num_questions} content words from DIFFERENT parts.
1. Target Word: Must be a content word (verb, noun, adjective) from the text.
2. Distractor (Grammar Trap): A word with DIFFERENT part of speech of a Synonym (NOT with the same root) (e.g., if target is 'powerful', use 'strength').
3. Distractor (Antonym): A word with the OPPOSITE meaning.
4. Distractor (Context Trap): A word that fits grammatically but makes NO SENSE in context.
5. Distractor (Antonym & Grammar Trap): A word with different part of speech of an Antonym.
6. Distractor (Context & Grammar Trap): A word with different part of speech of a word make NO sense in context.
7. Any disractor must be one type only from (Grammar Trap),(Antonym),(Context Trap),(Antonym & Grammar Trap),or (Context & Grammar Trap).
6. The correct answer could be any one from A,B,C,D, and the other three are all distractors.
7. Besides the correct answer, the other options can never be a Synonym with the same part of speech.
8. Output STRICT JSON list.

Article: \"\"\"{article_content}\"\"\"

Output JSON Format:
[
  {{
    "target_word": "original_word",
    "options": ["wrong1", "original_word", "wrong2", "wrong3"],
    "explanation": "..."
  }}
]
""".strip()
    
    def _build_true_false_prompt(self, article_content: str, num_questions: int) -> str:
        """构建判断题 Prompt"""
        seed = random.randint(1, 100000)
        return f"""
You are an English reading comprehension generator. [Random Seed: {seed}]
Task: Create {num_questions} TRUE/FALSE statements based on the article.

Requirements:
1. Cover different paragraphs.
2. For "false" statements, make them **subtly incorrect** (e.g. change a specific detail), not obviously wrong.
3. Balance true and false statements if possible.
4. Output STRICT JSON list.

Article: \"\"\"{article_content}\"\"\"

Output JSON Format:
[
  {{
    "statement": "The article claims that sleep is unnecessary.",
    "answer": "false",
    "explanation": "The article states sleep is essential."
  }}
]
""".strip()
    
    def _call_llm(self, prompt: str) -> List[Dict[str, Any]]:
        """
        调用 LLM 生成题目
        
        Args:
            prompt: 提示词
            
        Returns:
            题目列表
        """
        full_prompt = "You are a JSON generator. Output only JSON.\n" + prompt
        
        print(f"[QuestionGenerator] 调用LLM生成题目...")
        
        try:
            resp = self.client.chat_completion(
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=1024, 
                temperature=0.7
            )
            raw = resp.choices[0].message.content.strip()
            
            print(f"[QuestionGenerator] LLM返回原始响应长度: {len(raw)}")
            
            # 提取 JSON
            if "[" in raw and "]" in raw:
                start = raw.find("[")
                end = raw.rfind("]") + 1
                raw = raw[start:end]
            
            result = json.loads(raw)
            print(f"[QuestionGenerator] 成功解析 {len(result)} 道题目")
            return result
        
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
            if 'raw' in locals():
                print(f"原始响应: {raw[:200]}...")
            import traceback
            traceback.print_exc()
            return []


if __name__ == "__main__":
    # 测试
    generator = QuestionGenerator()
    
    test_content = """
    Coffee is a brewed drink prepared from roasted coffee beans, the seeds of berries from certain Coffea species. 
    From the coffee fruit, the seeds are separated to produce a stable, raw product: unroasted green coffee. 
    The seeds are then roasted, a process which transforms them into a consumable product.
    """
    
    print("生成完形填空题...")
    cloze = generator.generate_cloze_questions(test_content, 2)
    print(json.dumps(cloze, indent=2, ensure_ascii=False))
    
    print("\n生成判断题...")
    tf = generator.generate_true_false_questions(test_content, 2)
    print(json.dumps(tf, indent=2, ensure_ascii=False))
