"""
AI 口语私教模块 - 提供语音识别和雅思口语评分功能
支持浏览器麦克风录音 (需要在 Jupyter Notebook 环境中运行)
"""
import os
import json
from typing import Optional, Dict
from huggingface_hub import InferenceClient


# ================= 1. 配置模型 =================
HF_MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"
HF_TOKEN = os.environ.get("HF_TOKEN", "")
hf_client = InferenceClient(model=HF_MODEL_NAME, token=HF_TOKEN)


# ================= 2. 语音识别 =================
def load_whisper_model(model_size: str = "base"):
    """
    加载 Whisper 语音识别模型
    
    Args:
        model_size: 模型大小 (tiny, base, small, medium, large)
    """
    try:
        import whisper
        print(f"⏳ 正在加载 Whisper {model_size} 模型...")
        model = whisper.load_model(model_size)
        print("✅ Whisper 加载完成！")
        return model
    except ImportError:
        print("❌ 请先安装 openai-whisper: pip install git+https://github.com/openai/whisper.git")
        return None


def transcribe_audio(model, audio_file: str) -> str:
    """
    将音频文件转换为文字
    
    Args:
        model: Whisper 模型
        audio_file: 音频文件路径
    
    Returns:
        识别的文本
    """
    if model is None:
        raise ValueError("Whisper model not loaded")
    
    result = model.transcribe(audio_file)
    return result["text"].strip()


# ================= 3. 口语评价 Prompt =================
def build_speaking_prompt(text: str) -> str:
    """构建雅思口语评分的 Prompt"""
    return f"""
    You are an expert IELTS Speaking Examiner.
    The user has just spoken the following text (transcribed from audio).

    Transcribed Text:
    \"\"\"{text}\"\"\"

    Task:
    Evaluate this response based on **IELTS Speaking Criteria** (Band 0-9).
    Since you cannot hear the audio, assume pronunciation is clear but judge based on:
    1. **Fluency and Coherence**: Is the answer logical? Is it long enough?
    2. **Lexical Resource**: Did they use idiomatic language?
    3. **Grammatical Range and Accuracy**: Are there errors?

    Output STRICT JSON format:
    {{
      "overall_band": 6.5,
      "feedback": {{
        "fluency": {{ "score": 6.0, "comment": "..." }},
        "vocabulary": {{ "score": 7.0, "comment": "..." }},
        "grammar": {{ "score": 6.5, "comment": "..." }}
      }},
      "native_suggestion": "How a native speaker would say this..."
    }}
    """


def get_ai_feedback(text: str) -> Optional[Dict]:
    """
    获取 AI 口语评分反馈
    
    Args:
        text: 识别的文本
    
    Returns:
        评分报告字典
    """
    prompt = build_speaking_prompt(text)
    full_prompt = "You are a JSON generator. Output only JSON.\n" + prompt
    
    try:
        resp = hf_client.chat_completion(
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=1500, 
            temperature=0.7
        )
        raw = resp.choices[0].message.content.strip()
        
        if "[" in raw:
            raw = raw[raw.find("["):raw.rfind("]")+1]
        elif "{" in raw:
            raw = raw[raw.find("{"):raw.rfind("}")+1]
        
        return json.loads(raw)
    except Exception as e:
        print(f"Error: {e}")
        return None


# ================= 4. 报告打印 =================
def print_speaking_report(report: Dict):
    """打印口语评分报告"""
    if not report:
        print("❌ 无法生成评分报告")
        return
    
    print(f"\n{'='*20} 📊 口语成绩单 {'='*20}")
    print(f"🏆 预估雅思分数: {report.get('overall_band')}")

    fb = report.get('feedback', {})
    print(f"\n1. 流利度 (Fluency): {fb.get('fluency', {}).get('score')} - {fb.get('fluency', {}).get('comment')}")
    print(f"2. 词汇 (Vocab):   {fb.get('vocabulary', {}).get('score')} - {fb.get('vocabulary', {}).get('comment')}")
    print(f"3. 语法 (Grammar): {fb.get('grammar', {}).get('score')} - {fb.get('grammar', {}).get('comment')}")

    print(f"\n✨ 地道表达建议: \n{report.get('native_suggestion')}")
    print("="*50)


# ================= 5. 主流程 =================
def evaluate_speaking(audio_file: str, whisper_model=None) -> Optional[Dict]:
    """
    完整的口语评价流程
    
    Args:
        audio_file: 音频文件路径
        whisper_model: Whisper 模型 (如果未提供则会自动加载)
    
    Returns:
        评分报告字典
    """
    # 加载模型
    if whisper_model is None:
        whisper_model = load_whisper_model()
    
    if whisper_model is None:
        return None
    
    # 识别语音
    print("\n🎧 正在识别语音 (Transcribing)...")
    user_text = transcribe_audio(whisper_model, audio_file)
    print(f"\n📝 识别结果: \"{user_text}\"")
    
    if len(user_text) < 5:
        print("⚠️ 没听清，或者说得太短了，请重试。")
        return None
    
    # AI 评分
    print("🤖 考官正在评分 (Evaluating)...")
    report = get_ai_feedback(user_text)
    
    return report


# ================= 6. 浏览器麦克风录音支持 =================
AUDIO_HTML = """
<script>
var my_div = document.createElement('div');
var my_p = document.createElement('p');
var my_btn = document.createElement('button');
var my_status = document.createElement('p');

my_p.innerHTML = '<h3>🎙️ 浏览器麦克风录音</h3>';
my_btn.style.cssText = 'padding: 15px 30px; font-size: 16px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;';
my_status.style.cssText = 'color: #666; margin-top: 10px;';

my_div.appendChild(my_p);
my_div.appendChild(my_btn);
my_div.appendChild(my_status);
document.body.appendChild(my_div);

var base64data = 0;
var reader;
var recorder, gumStream;
var recordButton = my_btn;
var statusText = my_status;

var handleSuccess = function(stream) {
  gumStream = stream;
  var options = {
    mimeType : 'audio/webm;codecs=opus'
  };
  recorder = new MediaRecorder(stream, options);
  recorder.ondataavailable = function(e) {
    var url = URL.createObjectURL(e.data);
    var preview = document.createElement('audio');
    preview.controls = true;
    preview.src = url;
    preview.style.cssText = 'margin-top: 10px; width: 100%;';
    document.body.appendChild(preview);

    reader = new FileReader();
    reader.readAsDataURL(e.data);
    reader.onloadend = function() {
      base64data = reader.result;
    }
  };
  recorder.start();
  };

recordButton.innerText = "🎙️ 点击开始录音";
statusText.innerText = "准备就绪，点击按钮开始录音...";

navigator.mediaDevices.getUserMedia({audio: true}).then(handleSuccess).catch(function(err) {
  statusText.innerText = "❌ 无法访问麦克风: " + err.message;
  recordButton.disabled = true;
});

function toggleRecording() {
  if (recorder && recorder.state == "recording") {
      recorder.stop();
      gumStream.getAudioTracks()[0].stop();
      recordButton.innerText = "⏳ 处理中...";
      recordButton.style.background = "#FF9800";
      statusText.innerText = "正在处理录音，请稍候...";
      return "stop";
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

var data = new Promise(resolve=>{
  recordButton.onclick = ()=>{
    if (recorder.state == "recording") {
        toggleRecording()
        sleep(2000).then(() => {
            resolve(base64data.toString())
        });
    } else {
        recordButton.innerText = "⏹️ 点击停止录音";
        recordButton.style.background = "#f44336";
        statusText.innerText = "🔴 正在录音中...";
    }
  }
});
</script>
"""


def get_audio_from_browser(output_file: str = "user_audio.wav") -> str:
    """
    通过浏览器麦克风录制音频
    
    Args:
        output_file: 输出文件名
    
    Returns:
        音频文件路径
    """
    try:
        from IPython.display import HTML, display
        from base64 import b64decode
    except ImportError:
        raise ImportError("此功能需要在 Jupyter Notebook 环境中运行")
    
    # 尝试导入 eval_js (Colab) 或 使用通用方法
    try:
        from google.colab.output import eval_js
    except ImportError:
        try:
            # 尝试使用 ipywidgets 的方式
            from IPython.display import Javascript
            eval_js = lambda x: Javascript(x)
        except:
            raise ImportError("无法找到 JavaScript 执行环境，请在 Jupyter Notebook 或 Google Colab 中运行")
    
    display(HTML(AUDIO_HTML))
    data = eval_js("data")
    binary = b64decode(data.split(',')[1])

    # 转换音频格式
    try:
        import ffmpeg
        process = (ffmpeg
            .input('pipe:0')
            .output('pipe:1', format='wav')
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True, quiet=True, overwrite_output=True)
        )
        output, err = process.communicate(input=binary)

        riff_chunk_size = len(output) - 8
        q = riff_chunk_size
        b = []
        for i in range(4):
            q, r = divmod(q, 256)
            b.append(r)

        riff = output[:4] + bytes(b) + output[8:]

        with open(output_file, 'wb') as f:
            f.write(riff)
    except ImportError:
        # 如果没有 ffmpeg，直接保存 webm 格式
        print("⚠️ 未安装 ffmpeg，将保存为 webm 格式")
        output_file = output_file.replace('.wav', '.webm')
        with open(output_file, 'wb') as f:
            f.write(binary)
    
    return output_file


def start_speaking_coach_browser():
    """通过浏览器麦克风启动口语私教"""
    print(f"\n{'='*15} 🗣️ AI 口语模拟考官 (Speaking Coach) {'='*15}")
    print("准备通过浏览器麦克风录音...\n")

    # 加载模型
    stt_model = load_whisper_model("base")
    if stt_model is None:
        return

    try:
        # 录音
        print("请在下方点击按钮开始录音，说完后再次点击停止。")
        audio_file = get_audio_from_browser()
        
        # 评价
        report = evaluate_speaking(audio_file, stt_model)
        
        # 打印报告
        if report:
            print_speaking_report(report)
    except Exception as e:
        print(f"❌ 录音被取消或发生错误: {e}")
        print("请重新运行此函数。")


if __name__ == "__main__":
    print("口语私教模块加载完成")
    print("使用方法:")
    print("1. 在 Jupyter Notebook 中: 调用 start_speaking_coach_browser()")
    print("2. 使用本地音频文件: 调用 evaluate_speaking('audio.wav')")
