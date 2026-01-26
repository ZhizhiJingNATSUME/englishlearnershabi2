// src/components/SpeakingCoach.tsx
import { useState, useRef, useEffect } from 'react';
import { Mic, Square, Loader2, Volume2, TrendingUp, CheckCircle, Sparkles, History } from 'lucide-react';
import type { SpeakingEvaluation, SpeakingSubmission } from '../types';

interface SpeakingCoachProps {
  userId: number;
}

export default function SpeakingCoach({ userId }: SpeakingCoachProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [transcription, setTranscription] = useState('');
  const [evaluation, setEvaluation] = useState<SpeakingEvaluation | null>(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<SpeakingSubmission[]>([]);
  const [activeView, setActiveView] = useState<'practice' | 'result' | 'history'>('practice');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/speaking/history?user_id=${userId}&limit=10`);
      const data = await response.json();
      setHistory(data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  // 开始录音
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      setError('');
      setEvaluation(null);
      setTranscription('');
    } catch (err) {
      setError('Unable to access microphone. Please check browser permissions.');
      console.error('Microphone error:', err);
    }
  };

  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // 提交评分
  const submitForEvaluation = async () => {
    if (!audioBlob) return;
    
    setIsProcessing(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('user_id', userId.toString());
      
      const response = await fetch('http://localhost:5000/api/speaking/evaluate', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Scoring failed');
      }
      
      const data = await response.json();
      
      if (data.transcription) {
        setTranscription(data.transcription);
        // 后端返回的数据已经匹配 SpeakingEvaluation 接口
        setEvaluation(data);
        setActiveView('result');
        fetchHistory();
      } else {
        setError('Recording too short or could not be recognized. Please try again.');
      }
    } catch (err) {
      setError('Could not reach the scoring service. Please ensure the backend is running.');
      console.error('Evaluation error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  // 重新开始
  const reset = () => {
    setAudioBlob(null);
    setTranscription('');
    setEvaluation(null);
    setError('');
    setActiveView('practice');
  };

  const renderScoreBar = (score: number, label: string) => {
    const percentage = (score / 9) * 100;
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-slate-600 dark:text-slate-400">{label}</span>
          <span className="font-bold text-purple-600 dark:text-purple-400">{score}/9</span>
        </div>
        <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight">
            AI Speaking Coach
          </h1>
          <p className="text-slate-500 mt-2">IELTS Speaking AI Coach - speech recognition & instant scoring</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveView('practice')}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              activeView === 'practice'
                ? 'bg-purple-600 text-white shadow-lg'
                : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
            }`}
          >
            <Mic className="inline mr-2" size={18} />
            Practice
          </button>
          <button
            onClick={() => setActiveView('history')}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              activeView === 'history'
                ? 'bg-purple-600 text-white shadow-lg'
                : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
            }`}
          >
            <History className="inline mr-2" size={18} />
            History
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* 录音控制 */}
      {activeView === 'practice' && !evaluation && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-800">
          <div className="text-center space-y-6">
            <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full transition-all duration-300 ${
              isRecording 
                ? 'bg-red-500 animate-pulse' 
                : 'bg-purple-100 dark:bg-purple-900/30'
            }`}>
              {isRecording ? (
                <Square size={56} className="text-white" />
              ) : (
                <Mic size={56} className="text-purple-600 dark:text-purple-400" />
              )}
            </div>

            <div>
              <h3 className="text-xl font-bold dark:text-white mb-2">
                {isRecording ? 'Recording...' : audioBlob ? 'Recording ready' : 'Ready to start'}
              </h3>
              <p className="text-slate-500">
                {isRecording 
                  ? 'Click stop to finish recording' 
                  : audioBlob 
                  ? 'Submit for scoring or record again' 
                  : 'Click start to record'
                }
              </p>
            </div>

            <div className="flex gap-3 justify-center">
              {!isRecording && !audioBlob && (
                <button
                  onClick={startRecording}
                  className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold rounded-xl shadow-lg transition-all flex items-center gap-2"
                >
                  <Mic size={20} />
                  Start recording
                </button>
              )}

              {isRecording && (
                <button
                  onClick={stopRecording}
                  className="px-8 py-4 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl shadow-lg transition-all flex items-center gap-2"
                >
                  <Square size={20} />
                  Stop recording
                </button>
              )}

              {audioBlob && !isRecording && (
                <>
                  <button
                    onClick={reset}
                    className="px-6 py-4 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 font-semibold rounded-xl transition-all"
                  >
                    Record again
                  </button>
                  <button
                    onClick={submitForEvaluation}
                    disabled={isProcessing}
                    className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold rounded-xl shadow-lg transition-all flex items-center gap-2 disabled:opacity-50"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 size={20} className="animate-spin" />
                        AI scoring...
                      </>
                    ) : (
                      <>
                        <TrendingUp size={20} />
                        Submit for scoring
                      </>
                    )}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 评分结果 */}
      {activeView === 'result' && evaluation && (
        <div className="space-y-6">
          <button
            onClick={reset}
            className="text-purple-600 hover:underline font-semibold"
          >
            ← Record again
          </button>

          {/* 总分 */}
          <div className="bg-gradient-to-br from-purple-600 to-pink-700 rounded-2xl p-8 text-white shadow-xl">
            <div className="text-sm font-semibold mb-2 opacity-90">Estimated IELTS score</div>
            <div className="text-6xl font-black mb-4">{evaluation.overall_band}</div>
            <div className="text-sm opacity-75">IELTS Speaking Band Score</div>
          </div>

          {/* 转录文本 */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 mb-4">
              <Volume2 size={20} className="text-purple-600" />
              <h3 className="font-bold text-lg dark:text-white">Transcription</h3>
            </div>
            <p className="text-slate-700 dark:text-slate-300 italic">"{transcription}"</p>
          </div>

          {/* 详细评分 */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
            <h3 className="font-bold text-lg mb-4 dark:text-white flex items-center gap-2">
              <CheckCircle size={20} className="text-purple-600" />
              Scoring criteria
            </h3>
            <div className="space-y-4">
              {renderScoreBar(evaluation.feedback.fluency.score, 'Fluency & coherence')}
              {renderScoreBar(evaluation.feedback.vocabulary.score, 'Lexical resource')}
              {renderScoreBar(evaluation.feedback.grammar.score, 'Grammar accuracy')}
            </div>
            <div className="mt-4 space-y-2">
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <div className="text-xs font-bold text-slate-500 mb-1">Fluency feedback</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  {evaluation.feedback.fluency.comment}
                </div>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <div className="text-xs font-bold text-slate-500 mb-1">Vocabulary feedback</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  {evaluation.feedback.vocabulary.comment}
                </div>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <div className="text-xs font-bold text-slate-500 mb-1">Grammar feedback</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  {evaluation.feedback.grammar.comment}
                </div>
              </div>
            </div>
          </div>

          {/* 地道表达建议 */}
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-2xl p-6 border border-amber-200 dark:border-amber-800">
            <h3 className="font-bold text-lg mb-4 dark:text-white flex items-center gap-2">
              <Sparkles size={20} className="text-amber-600" />
              Natural phrasing suggestions
            </h3>
            <p className="text-slate-700 dark:text-slate-300">
              {evaluation.native_suggestion}
            </p>
          </div>
        </div>
      )}

      {/* 历史记录 */}
      {activeView === 'history' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
          <h3 className="font-bold text-lg mb-4 dark:text-white">Speaking history</h3>
          {history.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              No practice history yet. Start your first session!
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                        {item.transcription}
                      </div>
                      <div className="flex gap-4 text-xs text-slate-500">
                        <span>Fluency: {item.fluency_score}</span>
                        <span>Vocabulary: {item.vocabulary_score}</span>
                        <span>Grammar: {item.grammar_score}</span>
                      </div>
                      <div className="text-xs text-slate-400 mt-2">
                        {new Date(item.created_at).toLocaleString('en-US')}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-purple-600">{item.overall_band}</div>
                      <div className="text-xs text-slate-500">Overall</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
