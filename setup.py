"""
安装和初始化脚本
"""
import os
import sys
import subprocess

def install_dependencies():
    """安装依赖"""
    print("Installing Python dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✓ Dependencies installed")

def download_nltk_data():
    """下载NLTK数据"""
    print("\nDownloading NLTK data...")
    import nltk
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        print("✓ NLTK data downloaded")
    except Exception as e:
        print(f"Warning: {e}")

def download_spacy_model():
    """下载Spacy模型"""
    print("\nDownloading Spacy English model...")
    try:
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                      check=False, capture_output=True)
        print("✓ Spacy model downloaded")
    except Exception as e:
        print(f"Note: Spacy model download skipped ({e})")

def init_database():
    """初始化数据库"""
    print("\nInitializing database...")
    from backend.models import init_db
    init_db()
    print("✓ Database initialized")

def main():
    """主函数"""
    print("=" * 60)
    print("English Learning App - Setup")
    print("=" * 60)
    
    try:
        # 1. 安装依赖
        install_dependencies()
        
        # 2. 下载NLTK数据
        download_nltk_data()
        
        # 3. 下载Spacy模型（可选）
        download_spacy_model()
        
        # 4. 初始化数据库
        init_database()
        
        print("\n" + "=" * 60)
        print("✓ Setup completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Import articles: python scripts/import_articles.py")
        print("2. Start the server: python backend/app.py")
        print("3. Open frontend/index.html in your browser")
        print("\nFor more details, see README.md")
        
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

