#!/bin/bash

# 启动服务脚本

echo "Starting English Learning App Server..."

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# 检查数据库是否存在
if [ ! -f "backend/english_learning.db" ]; then
    echo "Database not found. Running setup..."
    python setup.py
fi

# 检查是否有文章
ARTICLE_COUNT=$(python -c "from backend.models import init_db, get_session, Article; engine = init_db(); session = get_session(engine); print(session.query(Article).count())" 2>/dev/null || echo "0")

if [ "$ARTICLE_COUNT" = "0" ]; then
    echo ""
    echo "No articles found in database."
    read -p "Do you want to import articles now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python scripts/import_articles.py
    else
        echo "You can import articles later by running: python scripts/import_articles.py"
    fi
fi

# 启动服务器
echo ""
echo "Starting API server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""
python backend/app.py

