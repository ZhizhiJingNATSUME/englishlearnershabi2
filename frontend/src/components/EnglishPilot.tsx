import { useEffect, useMemo, useRef, useState } from 'react';
import { Sparkles, Send, ShieldCheck, Loader2, Mic, Square } from 'lucide-react';
import type { EnglishPilotMessage, EnglishPilotScenario, User } from '../types';
import { chatEnglishPilot, transcribeEnglishPilotAudio } from '../services/api';

interface EnglishPilotProps {
  user: User;
}

const scenarioCatalog = {
  daily: [
    {
      id: 'ordering_food',
      title: 'Ordering Food',
      description: 'Practice ordering meals, asking for recommendations, and handling bills.',
      defaultGoal: 'Use polite requests and confirm your order.',
    },
    {
      id: 'making_appointments',
      title: 'Making Appointments',
      description: 'Schedule or reschedule appointments, confirm availability, and share details.',
      defaultGoal: 'Practice time expressions and polite confirmations.',
    },
    {
      id: 'casual_chat',
      title: 'Casual Chat',
      description: 'Warm, friendly conversations with neighbors or new friends.',
      defaultGoal: 'Use natural small talk and ask follow-up questions.',
    },
  ],
  academic: [
    {
      id: 'research_discussion',
      title: 'Discussing Research',
      description: 'Explain your research topic, methodology, and findings.',
      defaultGoal: 'Practice structured explanations and academic vocabulary.',
    },
    {
      id: 'lecture_followup',
      title: 'Lecture Follow-up',
      description: 'Ask for clarification after a lecture and summarize key points.',
      defaultGoal: 'Practice paraphrasing and clarification questions.',
    },
    {
      id: 'group_discussion',
      title: 'Group Discussion',
      description: 'Share opinions in a seminar and respond to peers.',
      defaultGoal: 'Practice agreeing, disagreeing, and adding evidence.',
    },
  ],
  professional: [
    {
      id: 'job_interview',
      title: 'Job Interview',
      description: 'Answer common interview questions and highlight your experience.',
      defaultGoal: 'Practice confident, structured answers.',
    },
    {
      id: 'business_meeting',
      title: 'Business Meeting',
      description: 'Discuss updates, propose ideas, and align on next steps.',
      defaultGoal: 'Use professional phrasing and clear summaries.',
    },
    {
      id: 'client_support',
      title: 'Client Support',
      description: 'Handle customer questions and resolve issues politely.',
      defaultGoal: 'Practice empathetic language and problem-solving.',
    },
  ],
};

const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export default function EnglishPilot({ user }: EnglishPilotProps) {
  const [category, setCategory] = useState<EnglishPilotScenario['category']>('daily');
  const [scenarioId, setScenarioId] = useState(scenarioCatalog.daily[0].id);
  const [customContext, setCustomContext] = useState('');
  const [goal, setGoal] = useState(scenarioCatalog.daily[0].defaultGoal);
  const [level, setLevel] = useState(user.english_level || 'B1');
  const [messages, setMessages] = useState<EnglishPilotMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const nextScenario = scenarioCatalog[category][0];
    setScenarioId(nextScenario.id);
    setGoal(nextScenario.defaultGoal);
  }, [category]);

  const selectedScenario = useMemo(() => {
    return scenarioCatalog[category].find((scenario) => scenario.id === scenarioId) ?? scenarioCatalog[category][0];
  }, [category, scenarioId]);

  const scenarioPayload: EnglishPilotScenario = useMemo(() => ({
    category,
    title: selectedScenario.title,
    description: selectedScenario.description,
    context: customContext.trim(),
    goal: goal.trim(),
  }), [category, selectedScenario, customContext, goal]);

  const sendMessage = async (nextMessages: EnglishPilotMessage[]) => {
    setIsLoading(true);
    setError('');
    try {
      const response = await chatEnglishPilot({
        user_id: user.id,
        scenario: scenarioPayload,
        level,
        messages: nextMessages,
      });
      const assistantMessage: EnglishPilotMessage = {
        role: 'assistant',
        content: response.reply,
        tips: response.tips,
        follow_up: response.follow_up,
        refusal: response.refusal,
      };
      setMessages([...nextMessages, assistantMessage]);
    } catch (err) {
      console.error('English Pilot error:', err);
      setError('Unable to reach English Pilot. Please ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = () => {
    const starterMessages: EnglishPilotMessage[] = [];
    setMessages([]);
    void sendMessage(starterMessages);
  };

  const handleSubmit = async () => {
    if (!input.trim()) return;
    const nextMessages = [...messages, { role: 'user', content: input.trim() }];
    setMessages(nextMessages);
    setInput('');
    await sendMessage(nextMessages);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
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
    } catch (err) {
      console.error('Microphone error:', err);
      setError('Unable to access microphone. Please check browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleVoiceSubmit = async () => {
    if (!audioBlob) return;
    setIsLoading(true);
    setError('');
    try {
      const { transcription } = await transcribeEnglishPilotAudio(audioBlob);
      if (!transcription || transcription.startsWith('[')) {
        setError('Unable to transcribe audio. Please try again.');
        return;
      }
      const nextMessages = [...messages, { role: 'user', content: transcription }];
      setMessages(nextMessages);
      setAudioBlob(null);
      await sendMessage(nextMessages);
    } catch (err) {
      console.error('STT error:', err);
      setError('Unable to transcribe audio. Please check the backend.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight">
              English Pilot
            </h1>
            <span className="inline-flex items-center gap-2 rounded-full bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300 px-3 py-1 text-xs font-semibold uppercase">
              <ShieldCheck size={14} />
              Role-Locked
            </span>
          </div>
          <p className="text-slate-500 mt-2 max-w-2xl">
            Practice scenario-based English conversations with a role-consistent learning assistant.
            Configure the situation, set your goal, and start chatting.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setIsVoiceMode((prev) => !prev)}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition ${
              isVoiceMode
                ? 'bg-emerald-600 text-white shadow-lg hover:bg-emerald-700'
                : 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-200'
            }`}
          >
            <Mic size={16} />
            {isVoiceMode ? 'Voice Mode' : 'Text Mode'}
          </button>
          <button
            onClick={handleStart}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-3 text-white font-semibold shadow-lg transition hover:from-indigo-700 hover:to-purple-700"
          >
            <Sparkles size={18} />
            Start Scenario
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1.8fr] gap-6">
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Scenario Configuration</h2>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Category</label>
                <select
                  value={category}
                  onChange={(event) => setCategory(event.target.value as EnglishPilotScenario['category'])}
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-800"
                >
                  <option value="daily">Daily Life</option>
                  <option value="academic">Academic</option>
                  <option value="professional">Professional</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Scenario</label>
                <select
                  value={scenarioId}
                  onChange={(event) => {
                    const nextId = event.target.value;
                    setScenarioId(nextId);
                    const nextScenario = scenarioCatalog[category].find((scenario) => scenario.id === nextId);
                    if (nextScenario) {
                      setGoal(nextScenario.defaultGoal);
                    }
                  }}
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-800"
                >
                  {scenarioCatalog[category].map((scenario) => (
                    <option key={scenario.id} value={scenario.id}>
                      {scenario.title}
                    </option>
                  ))}
                </select>
                <p className="mt-2 text-xs text-slate-500">{selectedScenario.description}</p>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Customization Notes</label>
                <textarea
                  value={customContext}
                  onChange={(event) => setCustomContext(event.target.value)}
                  placeholder="Add details like setting, roles, or special requests."
                  rows={3}
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Learning Goal</label>
                <input
                  value={goal}
                  onChange={(event) => setGoal(event.target.value)}
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Language Level</label>
                <select
                  value={level}
                  onChange={(event) => setLevel(event.target.value)}
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-800"
                >
                  {levels.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-indigo-50 p-5 text-sm text-indigo-700 dark:border-slate-800 dark:bg-indigo-900/20 dark:text-indigo-200">
            <p className="font-semibold">Identity Enforcement</p>
            <p className="mt-2">
              English Pilot always identifies itself, stays within the learning role, and refuses non-educational requests.
              Use this to keep your practice focused.
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 flex flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto max-h-[520px] pr-2">
            {messages.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center text-center text-slate-400">
                <Sparkles size={32} className="mb-3" />
                <p className="text-sm">Start a scenario to see English Pilot in action.</p>
              </div>
            )}
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  message.role === 'assistant'
                    ? 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
                    : 'bg-indigo-600 text-white'
                }`}
              >
                <p>{message.content}</p>
                {message.tips && message.tips.length > 0 && (
                  <div className="mt-3 rounded-xl bg-white/80 px-3 py-2 text-xs text-slate-700 dark:bg-slate-900/40 dark:text-slate-200">
                    <p className="font-semibold">Tips</p>
                    <ul className="mt-1 list-disc pl-4 space-y-1">
                      {message.tips.map((tip, tipIndex) => (
                        <li key={`${tip}-${tipIndex}`}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {message.follow_up && (
                  <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    Next prompt: {message.follow_up}
                  </p>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Loader2 className="animate-spin" size={16} />
                English Pilot is responding...
              </div>
            )}
          </div>

          {!isVoiceMode && (
            <div className="mt-4 flex items-center gap-3 border-t border-slate-200 pt-4 dark:border-slate-800">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    void handleSubmit();
                  }
                }}
                placeholder="Type your reply here..."
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-800"
              />
              <button
                onClick={() => void handleSubmit()}
                disabled={isLoading}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-indigo-700 disabled:opacity-60"
              >
                <Send size={16} />
                Send
              </button>
            </div>
          )}
          {isVoiceMode && (
            <div className="mt-4 space-y-3 border-t border-slate-200 pt-4 dark:border-slate-800">
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-lg transition ${
                    isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-emerald-600 hover:bg-emerald-700'
                  }`}
                >
                  {isRecording ? <Square size={16} /> : <Mic size={16} />}
                  {isRecording ? 'Stop Recording' : 'Start Recording'}
                </button>
                {audioBlob && (
                  <span className="text-xs text-slate-500">Recording ready. Submit to transcribe.</span>
                )}
              </div>
              <button
                onClick={() => void handleVoiceSubmit()}
                disabled={!audioBlob || isLoading}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-indigo-700 disabled:opacity-60"
              >
                <Send size={16} />
                Send Voice Reply
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
