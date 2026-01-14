"""
配置向导 - 帮助设置环境变量
"""
import os
from pathlib import Path

def create_env_file():
    """创建或更新 .env 文件"""
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    
    print("=" * 60)
    print("🔧 英语学习平台 - 配置向导")
    print("=" * 60)
    print()
    
    # 读取现有配置
    existing_config = {}
    if env_file.exists():
        print("✓ 发现现有 .env 文件，正在读取...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_config[key.strip()] = value.strip()
        print()
    
    print("请配置以下 API Token（直接回车跳过该项）：")
    print()
    
    # HF_TOKEN
    print("-" * 60)
    print("1️⃣  Hugging Face Token (用于 AI 写作评分和口语评估)")
    print("   获取方式: https://huggingface.co/settings/tokens")
    print(f"   当前值: {existing_config.get('HF_TOKEN', '未配置')[:20]}{'...' if len(existing_config.get('HF_TOKEN', '')) > 20 else ''}")
    hf_token = input("   请输入 HF_TOKEN: ").strip()
    if hf_token:
        existing_config['HF_TOKEN'] = hf_token
    print()
    
    # NEWS_API_KEY
    print("-" * 60)
    print("2️⃣  NewsAPI Key (用于获取英文新闻文章)")
    print("   获取方式: https://newsapi.org/register")
    print(f"   当前值: {existing_config.get('NEWS_API_KEY', '未配置')[:20]}{'...' if len(existing_config.get('NEWS_API_KEY', '')) > 20 else ''}")
    news_key = input("   请输入 NEWS_API_KEY: ").strip()
    if news_key:
        existing_config['NEWS_API_KEY'] = news_key
    print()
    
    # GEMINI_API_KEY
    print("-" * 60)
    print("3️⃣  Gemini API Key (用于内容分析)")
    print("   获取方式: https://makersuite.google.com/app/apikey")
    print(f"   当前值: {existing_config.get('GEMINI_API_KEY', '未配置')[:20]}{'...' if len(existing_config.get('GEMINI_API_KEY', '')) > 20 else ''}")
    gemini_key = input("   请输入 GEMINI_API_KEY: ").strip()
    if gemini_key:
        existing_config['GEMINI_API_KEY'] = gemini_key
    print()
    
    # 保存配置
    print("=" * 60)
    print("💾 正在保存配置到 .env 文件...")
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# 英语学习平台 - 环境变量配置\n")
        f.write("# 此文件由 configure.py 自动生成\n\n")
        
        f.write("# Hugging Face Token (用于 AI 写作评分和口语评估)\n")
        f.write("# 获取方式: https://huggingface.co/settings/tokens\n")
        f.write(f"HF_TOKEN={existing_config.get('HF_TOKEN', '')}\n\n")
        
        f.write("# NewsAPI Key (用于获取英文新闻文章)\n")
        f.write("# 获取方式: https://newsapi.org/register\n")
        f.write(f"NEWS_API_KEY={existing_config.get('NEWS_API_KEY', '')}\n\n")
        
        f.write("# Gemini API Key (用于内容分析)\n")
        f.write("# 获取方式: https://makersuite.google.com/app/apikey\n")
        f.write(f"GEMINI_API_KEY={existing_config.get('GEMINI_API_KEY', '')}\n")
    
    print("✅ 配置已保存到:", env_file)
    print()
    print("=" * 60)
    print("📋 配置摘要:")
    print("=" * 60)
    print(f"HF_TOKEN:        {'✓ 已配置' if existing_config.get('HF_TOKEN') else '✗ 未配置'}")
    print(f"NEWS_API_KEY:    {'✓ 已配置' if existing_config.get('NEWS_API_KEY') else '✗ 未配置'}")
    print(f"GEMINI_API_KEY:  {'✓ 已配置' if existing_config.get('GEMINI_API_KEY') else '✗ 未配置'}")
    print()
    print("💡 提示:")
    print("  • 未配置 HF_TOKEN 时，AI 评分功能将使用模拟数据")
    print("  • 可以随时运行 'python configure.py' 重新配置")
    print("  • 配置完成后需要重启后端服务")
    print()

if __name__ == '__main__':
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\n❌ 配置已取消")
    except Exception as e:
        print(f"\n\n❌ 配置失败: {e}")
