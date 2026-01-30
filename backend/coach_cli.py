"""
AI 英语私教 - 主程序入口
提供写作和口语训练的命令行交互界面
"""
import sys
from typing import Optional
from fastapi.testclient import TestClient


def print_menu():
    """打印主菜单"""
    print(f"\n{'='*20} ✨ AI 英语私教系统 {'='*20}")
    print("\n请选择功能:")
    print("  1. 📝 写作训练 (Writing Coach)")
    print("  2. 🗣️ 口语训练 (Speaking Coach)")
    print("  3. 🚀 启动 API 服务器")
    print("  4. ❌ 退出")
    print("="*60)


def start_writing_coach():
    """启动写作私教"""
    from writing_coach import (
        create_app, setup_routes, init_database,
        print_progress, print_report
    )
    
    # 初始化
    init_database()
    app = create_app()
    setup_routes(app)
    client = TestClient(app)
    
    print(f"\n{'='*15} ✍️  AI 写作私教 {'='*15}")
    print("功能：输入一段英语，获取 [雅思标准] & [通用标准] 双重评分 + 润色。")
    
    # 模式选择
    print("\n请选择写作模式:")
    print("   1. 🕊️  自由写作 (Free Writing)")
    print("   2. 🎯 话题写作 (Topic Writing)")
    
    mode = ""
    while mode not in ["1", "2"]:
        mode = input("👉 请输入 1 或 2: ").strip()
    
    current_topic = None
    
    # 话题处理
    if mode == "2":
        print("\n🔍 正在获取题库...")
        topics = client.get("/topics").json()
        
        print(f"\n{'='*10} 题库列表 {'='*10}")
        for t in topics:
            print(f"   [{t['id']}] 【{t['category']}】 {t['title']}")
        print(f"{'='*30}")
        
        valid_ids = [str(t['id']) for t in topics]
        while True:
            tid = input("👉 请输入话题 ID: ").strip()
            if tid in valid_ids:
                topic_id = int(tid)
                selected_t = next(t for t in topics if t['id'] == topic_id)
                current_topic = selected_t['description']
                print(f"\n✅ 已锁定话题:\n📢 \"{current_topic}\"")
                break
            print("❌ ID 无效")
    else:
        print("\n✅ 已进入自由模式，想写什么就写什么！")
    
    print("-" * 60)
    print("请输入你的作文 (输入 'back' 返回主菜单, 'history' 查看历史)。\n")
    
    # 写作循环
    while True:
        if current_topic:
            print(f"\n📝 当前题目: {current_topic[:50]}...")
        
        user_input = input("\n👉 请输入/粘贴作文: \n").strip()
        
        if not user_input:
            continue
        if user_input.lower() == "back":
            return
        if user_input.lower() == "history":
            h = client.get("/history").json()
            print("\n📜 历史记录:")
            for item in h:
                print(f"   [ID {item['id']}] Score: {item.get('score')} | {item['preview']}")
            continue
        
        print("\n🤖 AI 考官正在评分中 (Analyzing)...")
        
        try:
            payload = {"text": user_input}
            if current_topic:
                payload["topic"] = current_topic
            
            resp = client.post("/evaluate", json=payload)
            
            if resp.status_code != 200:
                print(f"❌ 错误: {resp.text}")
                continue
            
            data = resp.json()["report"]
            print_report(data)
            
        except Exception as e:
            print(f"❌ 系统错误: {e}")


def start_speaking_coach():
    """启动口语私教"""
    from speaking_coach import evaluate_speaking, print_speaking_report, start_speaking_coach_browser
    
    print(f"\n{'='*15} 🗣️ AI 口语私教 {'='*15}")
    print("请选择录音方式:")
    print("  1. 🎙️  使用浏览器麦克风录音 (需要 Jupyter Notebook 环境)")
    print("  2. 📁 使用本地音频文件")
    print("  3. ⬅️  返回主菜单\n")
    
    choice = input("👉 请选择 (1-3): ").strip()
    
    if choice == "1":
        try:
            start_speaking_coach_browser()
        except Exception as e:
            print(f"❌ 浏览器录音失败: {e}")
            print("提示: 此功能需要在 Jupyter Notebook 环境中运行")
    elif choice == "2":
        print("\n请提供音频文件路径进行评分。")
        print("(输入 'back' 返回主菜单)\n")
        
        while True:
            audio_path = input("👉 请输入音频文件路径: ").strip()
            
            if audio_path.lower() == "back":
                return
            
            if not audio_path:
                continue
            
            try:
                report = evaluate_speaking(audio_path)
                if report:
                    print_speaking_report(report)
            except Exception as e:
                print(f"❌ 错误: {e}")
    elif choice == "3":
        return
    else:
        print("❌ 无效选择")


def start_api_server():
    """启动 API 服务器"""
    from writing_coach import create_app, setup_routes, init_database
    import uvicorn
    
    print("\n🚀 正在启动 API 服务器...")
    
    # 初始化
    init_database()
    app = create_app()
    setup_routes(app)
    
    print("✅ 服务器将在 http://localhost:8000 启动")
    print("   API 文档: http://localhost:8000/docs")
    print("   按 Ctrl+C 停止服务器\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    """主函数"""
    while True:
        print_menu()
        choice = input("\n👉 请选择 (1-4): ").strip()
        
        if choice == "1":
            start_writing_coach()
        elif choice == "2":
            start_speaking_coach()
        elif choice == "3":
            start_api_server()
            break  # API 服务器会阻塞
        elif choice == "4":
            print("\n👋 再见！")
            sys.exit(0)
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
        sys.exit(0)
