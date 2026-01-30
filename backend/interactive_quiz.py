"""
交互式测验模块
提供完形填空和判断题的命令行交互界面
"""
import random
from typing import List, Dict, Any


class InteractiveQuiz:
    """交互式测验"""
    
    @staticmethod
    def run_cloze_test(article: Dict[str, Any], questions: List[Dict[str, Any]]) -> int:
        """
        运行完形填空测试
        
        Args:
            article: 文章字典 {id, title, content, difficulty_level, ...}
            questions: 题目列表
            
        Returns:
            得分
        """
        print(f"\n{'='*20} 📖 阅读时间 ({article.get('difficulty_level', 'Unknown')}) {'='*20}\n")
        
        # 1. 显示带挖空的文章
        display_text = article["content"]
        for index, q in enumerate(questions, 1):
            target_word = q["answer"]
            # 只替换第一次出现
            display_text = display_text.replace(target_word, f" [___{index}___] ", 1)
        
        print(display_text)
        print(f"\n{'='*60}")
        
        # 2. 逐题作答
        score = 0
        letters = ['A', 'B', 'C', 'D']
        
        print(f"\n👇 请选择正确的选项填入空白处:\n")
        
        for index, q in enumerate(questions, 1):
            print(f"\n🔹 空白 {index}:")
            
            # 显示选项
            opt_map = {}
            for i, opt in enumerate(q['options']):
                if i < 4:
                    print(f"   {letters[i]}. {opt}")
                    opt_map[letters[i]] = opt
            
            # 输入循环
            while True:
                user_input = input(f"👉 请输入空白 {index} 的答案 (A/B/C/D): ").strip().upper()
                if user_input in ['A', 'B', 'C', 'D']:
                    break
                print("⚠️ 输入无效，请输入 A、B、C 或 D。")
            
            # 判分
            selected_word = opt_map[user_input]
            correct_word = q['answer']
            
            if selected_word == correct_word:
                print(f"✅ 正确！(答案: {correct_word})")
                score += 1
            else:
                print(f"❌ 错误。正确答案: {correct_word}")
                if q.get('explanation'):
                    print(f"   💡 解析: {q['explanation']}")
            
            print("-" * 30)
        
        print(f"\n🎉 完形填空测试结束！得分: {score}/{len(questions)}")
        return score
    
    @staticmethod
    def run_true_false_test(article: Dict[str, Any], questions: List[Dict[str, Any]]) -> int:
        """
        运行判断题测试
        
        Args:
            article: 文章字典
            questions: 题目列表
            
        Returns:
            得分
        """
        print(f"\n{'='*20} 📖 阅读时间 ({article.get('difficulty_level', 'Unknown')}) {'='*20}\n")
        print(article["content"])
        print(f"\n{'='*60}")
        
        score = 0
        print(f"\n👇 请判断以下陈述的对错 (输入 T 表示正确，F 表示错误)\n")
        
        for index, q in enumerate(questions, 1):
            print(f"\n🔹 第 {index} 题:")
            print(f"   \"{q['question_text']}\"")
            
            # 输入循环
            while True:
                user_input = input(f"👉 这句话是正确还是错误? (T/F): ").strip().upper()
                if user_input in ['T', 'F', 'TRUE', 'FALSE']:
                    break
                print("⚠️ 输入无效，请输入 T 或 F。")
            
            # 判分
            user_bool = "true" if user_input.startswith("T") else "false"
            correct_ans = q['answer']
            
            if user_bool == correct_ans:
                print(f"✅ 正确！")
                score += 1
            else:
                print(f"❌ 错误。")
                print(f"   正确答案: {correct_ans.upper()}")
                if q.get('explanation'):
                    print(f"   💡 解析: {q['explanation']}")
            
            print("-" * 30)
        
        print(f"\n🎉 判断题测试结束！得分: {score}/{len(questions)}")
        return score


def demo():
    """演示功能"""
    # 模拟数据
    article = {
        "id": 1,
        "title": "Coffee History",
        "content": "Coffee is a brewed drink prepared from roasted coffee beans. It is darkly colored and bitter.",
        "difficulty_level": "B1"
    }
    
    cloze_questions = [
        {
            "question_text": "Question 1 for: brewed",
            "options": ["mixed", "brewed", "frozen", "boiled"],
            "answer": "brewed",
            "explanation": "Brewed means prepared by soaking in hot water."
        }
    ]
    
    tf_questions = [
        {
            "question_text": "Coffee is a sweet drink.",
            "answer": "false",
            "explanation": "The article says coffee is bitter, not sweet."
        }
    ]
    
    quiz = InteractiveQuiz()
    
    print("=== 完形填空测试演示 ===")
    quiz.run_cloze_test(article, cloze_questions)
    
    print("\n=== 判断题测试演示 ===")
    quiz.run_true_false_test(article, tf_questions)


if __name__ == "__main__":
    demo()
