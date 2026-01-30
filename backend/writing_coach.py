"""
AI 写作私教模块 - 提供雅思写作评分和话题训练功能
"""
import os
import json
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON as SA_JSON, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from huggingface_hub import InferenceClient


# ================= 1. 配置模型 =================
HF_MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"
HF_TOKEN = os.environ.get("HF_TOKEN", "")
hf_client = InferenceClient(model=HF_MODEL_NAME, token=HF_TOKEN)

# ================= 2. 数据库配置 =================
DATABASE_URL = "sqlite:///./writing_coach.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- 表定义 ---
class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    topic_title = Column(String(255), nullable=True)  # 记录题目(如果是话题写作)
    user_text = Column(Text)
    evaluation = Column(SA_JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))      # 话题标题
    description = Column(Text)       # 具体问题描述
    category = Column(String(50))    # 类别 (Technology, Environment...)


# ================= 3. 数据模型 =================
class TopicOut(BaseModel):
    id: int
    title: str
    description: str
    category: str


class WritingRequest(BaseModel):
    text: str
    topic: Optional[str] = None  # 允许传入题目，辅助AI评分


class WritingResponse(BaseModel):
    status: str
    id: int
    report: Dict[str, Any]


# ================= 4. Prompt 逻辑 =================
def build_examiner_prompt(text: str, topic: str = None) -> str:
    """构建雅思写作评分的 Prompt"""
    topic_context = ""
    if topic:
        topic_context = f'The user is writing based on this TOPIC:\n"{topic}"\nCheck if the response addresses this topic relevantly.\n'

    return f"""
    You are an expert IELTS examiner and English editor.
    {topic_context}

    Evaluate the following text strictly.
    Input Text:
    \"\"\"{text}\"\"\"

    Task:
    1. Score based on **IELTS Writing Criteria** (0-9 scale):
       - Task Response (Did they answer the topic? If no topic provided, assume open topic)
       - Coherence & Cohesion
       - Lexical Resource
       - Grammatical Range & Accuracy

    2. Score based on **General Quality** (0-9 scale):
       - Idiomatic/Native-like Phrasing
       - Grammar Accuracy
       - Spelling

    3. Provide a **Native-level Rewrite**.

    Output STRICT JSON format:
    {{
      "ielts": {{
        "overall": 6.5,
        "criteria": {{
            "task_response": {{ "score": 6.0, "comment": "..." }},
            "coherence": {{ "score": 6.5, "comment": "..." }},
            "lexical": {{ "score": 7.0, "comment": "..." }},
            "grammar": {{ "score": 6.0, "comment": "..." }}
        }}
      }},
      "general": {{
        "overall": 7.0,
        "criteria": {{
            "native_phrasing": {{ "score": 6.0, "comment": "..." }},
            "grammar_accuracy": {{ "score": 7.5, "comment": "..." }},
            "spelling": {{ "score": 9.0, "comment": "..." }}
        }}
      }},
      "overall_feedback": "Summary...",
      "improved_version": "Rewritten text..."
    }}
    """


def call_llm(prompt: str) -> Optional[Dict]:
    """调用 LLM 获取评分报告"""
    full_prompt = "You are a JSON generator. Output only JSON.\n" + prompt
    try:
        resp = hf_client.chat_completion(
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=2500, 
            temperature=0.5
        )
        raw = resp.choices[0].message.content.strip()
        if "[" in raw:
            raw = raw[raw.find("["):raw.rfind("]")+1]
        elif "{" in raw:
            raw = raw[raw.find("{"):raw.rfind("}")+1]
        return json.loads(raw)
    except Exception as e:
        print(f"LLM Error: {e}")
        return None


# ================= 5. FastAPI 应用 =================
def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(title="AI Writing Coach")
    app.add_middleware(
        CORSMiddleware, 
        allow_origins=["*"], 
        allow_credentials=True, 
        allow_methods=["*"], 
        allow_headers=["*"]
    )
    
    return app


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库和话题库"""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if db.query(Topic).count() == 0:
            print("🌱 正在初始化话题库...")
            topics = [
                {
                    "category": "Education", 
                    "title": "Online Education vs Classroom", 
                    "description": "Some people believe that online education is better than traditional classroom learning. To what extent do you agree or disagree?"
                },
                {
                    "category": "Technology", 
                    "title": "AI in Workplace", 
                    "description": "Artificial Intelligence is replacing many human jobs. Is this a positive or negative development?"
                },
                {
                    "category": "Environment", 
                    "title": "Plastic Waste", 
                    "description": "Plastic pollution is a major problem. What are the causes and what solutions can you suggest?"
                },
                {
                    "category": "Society", 
                    "title": "Work-Life Balance", 
                    "description": "Many people nowadays work longer hours and have less time for leisure. What are the effects of this trend?"
                },
                {
                    "category": "Culture", 
                    "title": "Tourism Impacts", 
                    "description": "International tourism creates tension between people from different cultures. Do you agree or disagree?"
                },
                {
                    "category": "Health", 
                    "title": "Sugar Tax", 
                    "description": "Governments should impose a tax on sugary drinks to improve public health. Discuss the advantages and disadvantages."
                }
            ]
            for t in topics:
                db.add(Topic(**t))
            db.commit()
            print("✅ 话题库初始化完成")
    finally:
        db.close()


# ================= 6. API 路由 =================
def setup_routes(app: FastAPI):
    """设置 API 路由"""
    
    @app.get("/topics", response_model=List[TopicOut])
    def get_topics(db: Session = Depends(get_db)):
        """获取话题列表"""
        return db.query(Topic).all()

    @app.post("/evaluate", response_model=WritingResponse)
    def evaluate_text(req: WritingRequest, db: Session = Depends(get_db)):
        """评价写作文本"""
        if len(req.text.split()) < 3:
            raise HTTPException(status_code=400, detail="Text too short.")

        # 构建 Prompt (如果选了话题，把话题也传进去)
        prompt = build_examiner_prompt(req.text, req.topic)
        report = call_llm(prompt)

        if not report:
            raise HTTPException(status_code=500, detail="AI failed to generate report.")

        sub = Submission(user_text=req.text, topic_title=req.topic, evaluation=report)
        db.add(sub)
        db.commit()
        db.refresh(sub)

        return {"status": "ok", "id": sub.id, "report": report}

    @app.get("/history")
    def get_history(limit: int = 10, db: Session = Depends(get_db)):
        """获取历史记录"""
        subs = db.query(Submission).order_by(Submission.id.desc()).limit(limit).all()
        return [
            {
                "id": s.id, 
                "preview": s.user_text[:50] + "...", 
                "topic": s.topic_title,
                "score": s.evaluation.get("ielts", {}).get("overall"),
                "created_at": s.created_at.isoformat() if s.created_at else None
            } 
            for s in subs
        ]


# ================= 7. 辅助函数 =================
def print_progress(score, label):
    """打印评分条"""
    if score is None:
        score = 0
    score = float(score)
    bar_len = 10
    filled = int((score / 9.0) * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"   {label.ljust(22)}: {score}/9.0  [{bar}]")


def print_report(data: Dict):
    """打印评分报告"""
    print(f"\n{'='*20} 📝 评分报告 {'='*20}")

    # 雅思
    ielts = data.get("ielts", {})
    print(f"\n【📚 雅思评分 (Overall: {ielts.get('overall')})】")
    crit = ielts.get("criteria", {})
    print_progress(crit.get("task_response", {}).get("score"), "Task Response")
    print_progress(crit.get("coherence", {}).get("score"), "Coherence")
    print_progress(crit.get("lexical", {}).get("score"), "Lexical")
    print_progress(crit.get("grammar", {}).get("score"), "Grammar")

    # 通用
    gen = data.get("general", {})
    print(f"\n【🌍 通用评分 (Overall: {gen.get('overall')})】")
    crit_g = gen.get("criteria", {})
    print_progress(crit_g.get("native_phrasing", {}).get("score"), "地道程度")
    print_progress(crit_g.get("grammar_accuracy", {}).get("score"), "语法准确")
    print_progress(crit_g.get("spelling", {}).get("score"), "拼写")

    # 反馈 & 润色
    print(f"\n【💬 点评】 {data.get('overall_feedback')}")
    print(f"\n【✨ 润色】 {data.get('improved_version')}")
    print("\n" + "="*60)


if __name__ == "__main__":
    # 初始化数据库
    init_database()
    
    # 创建应用
    app = create_app()
    setup_routes(app)
    
    # 启动服务器
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
