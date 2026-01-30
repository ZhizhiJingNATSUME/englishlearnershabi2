"""
阅读测试系统 - 主程序
整合文章数据库、题目生成、交互测试
"""
import os
import sys
import random
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

# 导入项目模块
from models import Article, init_db, get_session
from question_generator import QuestionGenerator
from interactive_quiz import InteractiveQuiz


class ReadingTestSystem:
    """阅读测试系统"""
    
    def __init__(self, db_path: str = 'sqlite:///english_learning.db'):
        """
        初始化系统
        
        Args:
            db_path: 数据库路径
        """
        self.engine = init_db(db_path)
        self.session = get_session(self.engine)
        self.generator = QuestionGenerator()
        self.quiz = InteractiveQuiz()
        
        # 题目缓存（避免重复生成）
        self.question_cache = {}
    
    def get_articles_by_level(self, level: str) -> List[Article]:
        """
        按难度获取文章
        
        Args:
            level: CEFR 等级 (A1, A2, B1, B2, C1, C2)
            
        Returns:
            文章列表
        """
        return self.session.query(Article).filter(
            Article.difficulty_level == level.upper()
        ).all()
    
    def get_random_article(self, level: Optional[str] = None) -> Optional[Article]:
        """
        获取随机文章
        
        Args:
            level: 可选的难度等级
            
        Returns:
            文章对象或 None
        """
        query = self.session.query(Article)
        
        if level:
            query = query.filter(Article.difficulty_level == level.upper())
        
        articles = query.all()
        
        if not articles:
            return None
        
        return random.choice(articles)
    
    def generate_questions_for_article(
        self, 
        article_id: int, 
        question_type: str = "cloze", 
        num_questions: int = 3,
        force_regenerate: bool = False
    ) -> List[Dict[str, Any]]:
        """
        为文章生成题目
        
        Args:
            article_id: 文章ID
            question_type: 题目类型 ("cloze" 或 "true_false")
            num_questions: 题目数量
            force_regenerate: 是否强制重新生成
            
        Returns:
            题目列表
        """
        cache_key = f"{article_id}_{question_type}"
        
        # 检查缓存
        if not force_regenerate and cache_key in self.question_cache:
            return self.question_cache[cache_key]
        
        # 获取文章
        article = self.session.query(Article).filter(Article.id == article_id).first()
        
        if not article:
            print(f"❌ 文章 ID {article_id} 不存在")
            return []
        
        print(f"\n🤖 AI 正在分析文章并生成题目 (预计 10-15 秒)...")
        
        # 生成题目
        if question_type == "cloze":
            raw_questions = self.generator.generate_cloze_questions(
                article.content, 
                num_questions
            )
        elif question_type == "true_false":
            raw_questions = self.generator.generate_true_false_questions(
                article.content, 
                num_questions
            )
        else:
            print(f"❌ 未知题目类型: {question_type}")
            return []
        
        # 处理题目
        processed_questions = []
        
        for idx, q in enumerate(raw_questions):
            if question_type == "cloze":
                target_word = q.get("target_word", "").strip()
                options = [str(o).strip() for o in q.get("options", [])]
                
                # 验证目标词在原文中
                if target_word not in article.content:
                    print(f"⚠️ [跳过] 第 {idx+1} 题: '{target_word}' 不在原文中")
                    continue
                
                # 确保正确答案在选项中
                if target_word not in options:
                    options.append(target_word)
                    random.shuffle(options)
                
                processed_questions.append({
                    "question_text": f"Question {idx+1} for: {target_word}",
                    "options": options[:4],  # 最多4个选项
                    "answer": target_word,
                    "explanation": q.get("explanation", "")
                })
            
            elif question_type == "true_false":
                statement = q.get("statement") or q.get("question")
                raw_ans = str(q.get("answer", "")).lower().strip()
                
                if not statement:
                    print(f"⚠️ [跳过] 第 {idx+1} 题: 缺少题干")
                    continue
                
                # 标准化答案
                if "true" in raw_ans:
                    answer = "true"
                elif "false" in raw_ans:
                    answer = "false"
                else:
                    print(f"⚠️ [跳过] 第 {idx+1} 题: 无法识别答案 '{raw_ans}'")
                    continue
                
                processed_questions.append({
                    "question_text": statement,
                    "answer": answer,
                    "explanation": q.get("explanation", "")
                })
        
        # 缓存结果
        self.question_cache[cache_key] = processed_questions
        
        print(f"✅ 成功生成 {len(processed_questions)} 道题目")
        return processed_questions
    
    def start_test(self):
        """启动测试流程"""
        print(f"\n{'='*12} 🚀 AI 分级阅读测试系统 {'='*12}")
        
        # 1. 选择难度等级
        print("\n可用等级: A1, A2, B1, B2, C1, C2")
        selected_level = "B1"
        
        while True:
            user_input = input("👉 请输入你的等级 (直接回车默认 B1): ").strip().upper()
            if user_input == "":
                break
            if user_input in ["A1", "A2", "B1", "B2", "C1", "C2"]:
                selected_level = user_input
                break
            print("❌ 无效等级，请重新输入")
        
        # 2. 获取文章
        print(f"\n🔍 正在查找 {selected_level} 级别的文章...")
        article = self.get_random_article(selected_level)
        
        if not article:
            print(f"❌ 未找到 {selected_level} 级别的文章")
            print("提示: 请先运行爬虫或导入文章数据")
            return
        
        print(f"✅ 选中文章: 《{article.title}》")
        print(f"   来源: {article.source_name or article.source}")
        print(f"   难度: {article.difficulty_level} (评分: {article.difficulty_score})")
        print(f"   字数: {article.word_count} 词")
        
        # 3. 选择测试类型
        print("\n请选择测试类型:")
        print("   1. 📝 完形填空 (Cloze Test)")
        print("   2. ✅ 判断题 (True/False)")
        
        choice = ""
        while choice not in ["1", "2"]:
            choice = input("👉 请输入 1 或 2: ").strip()
        
        question_type = "cloze" if choice == "1" else "true_false"
        
        # 4. 生成题目
        questions = self.generate_questions_for_article(
            article.id, 
            question_type, 
            num_questions=3
        )
        
        if not questions:
            print("❌ 题目生成失败，请重试")
            return
        
        # 5. 开始测试
        article_dict = {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "difficulty_level": article.difficulty_level
        }
        
        if question_type == "cloze":
            score = self.quiz.run_cloze_test(article_dict, questions)
        else:
            score = self.quiz.run_true_false_test(article_dict, questions)
        
        # 6. 评价
        percentage = (score / len(questions)) * 100
        
        print(f"\n{'='*20} 📊 测试总结 {'='*20}")
        print(f"文章: 《{article.title}》")
        print(f"难度: {article.difficulty_level}")
        print(f"得分: {score}/{len(questions)} ({percentage:.1f}%)")
        
        if percentage >= 80:
            print("🎉 太棒了！你可以尝试更高难度的文章")
        elif percentage >= 60:
            print("👍 不错！继续练习这个难度")
        else:
            print("💪 加油！建议多读几篇同级别文章")
        
        print("="*60)
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()


def main():
    """主函数"""
    system = ReadingTestSystem()
    
    try:
        system.start_test()
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
    finally:
        system.close()


if __name__ == "__main__":
    main()
