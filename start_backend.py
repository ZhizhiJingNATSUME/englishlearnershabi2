"""
启动统一后端服务
包含：Reading Test, Writing Coach, Speaking Coach
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
# 同时添加 backend 目录到路径
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

# 加载 .env 文件中的环境变量
def load_env_file():
    """加载 .env 文件中的环境变量"""
    env_file = Path(project_root) / '.env'
    env_file = env_file.resolve()  # 使用绝对路径
    
    if env_file.exists():
        print("📄 正在加载 .env 配置文件...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value:  # 只设置非空值
                        os.environ[key] = value
                        # 不显示完整 token，只显示前几个字符
                        if len(value) > 10:
                            display_value = value[:10] + '...'
                        else:
                            display_value = value
                        print(f"  ✓ {key}: {display_value}")
        print()
    else:
        print(f"⚠️  未找到 .env 文件 (查找路径: {env_file})")
        print("💡 运行 'python configure.py' 来配置 API tokens")
        print()

# 加载环境变量
load_env_file()

# 打印 Python 环境信息（调试用）
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path[:3]}")

# 导入并运行 Flask 应用
from backend.app import app, load_whisper, init_recommender

if __name__ == '__main__':
    # 加载 Whisper 模型
    load_whisper()
    
    # 初始化推荐系统
    print("Initializing recommender system...")
    init_recommender()
    print("Recommender system initialized.")
    
    # 启动服务
    # 使用环境变量控制 debug 模式，生产环境设置为 False
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    print(f"Starting unified backend on http://{host}:{port} (debug={debug_mode})")
    app.run(debug=debug_mode, host=host, port=port, use_reloader=False)
