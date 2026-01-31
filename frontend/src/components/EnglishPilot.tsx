import { useEffect, useMemo, useRef, useState } from 'react';
import { Sparkles, Send, ShieldCheck, Loader2, Mic, Square, Play, Pause } from 'lucide-react';
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
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [ttsAudioUrl, setTtsAudioUrl] = useState<string | null>(null);
  const [voiceDraft, setVoiceDraft] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState('');
  const [ttsError, setTtsError] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSpeechPaused, setIsSpeechPaused] = useState(false);
  const [ttsVolume, setTtsVolume] = useState(1);
  const [ttsRate, setTtsRate] = useState(1);
  const [ttsEngine, setTtsEngine] = useState<'speech' | 'google' | 'none'>('none');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef<string | null>(null);
  const speechUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const lastSpokenRef = useRef<string | null>(null);
  const ttsAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!audioUrl) return;
    return () => {
      URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  useEffect(() => {
    if (!ttsAudioUrl) return;
    return () => {
      if (ttsAudioUrl.startsWith('blob:')) {
        URL.revokeObjectURL(ttsAudioUrl);
      }
    };
  }, [ttsAudioUrl]);

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

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

  const latestAssistantMessage = useMemo(
    () => [...messages].reverse().find((message) => message.role === 'assistant')?.content ?? '',
    [messages],
  );

  const stopTts = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause();
      ttsAudioRef.current.currentTime = 0;
    }
    setIsSpeaking(false);
    setIsSpeechPaused(false);
  };

  const startSpeechSynthesis = (text: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      return false;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = ttsRate;
    utterance.volume = ttsVolume;
    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsSpeechPaused(false);
      setTtsEngine('speech');
    };
    utterance.onend = () => {
      setIsSpeaking(false);
      setIsSpeechPaused(false);
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      setIsSpeechPaused(false);
      setTtsError('Text-to-speech failed. You can try again or use another browser.');
    };
    speechUtteranceRef.current = utterance;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    return true;
  };

  const startGoogleTts = (text: string) => {
    const url = `https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q=${encodeURIComponent(text)}`;
    setTtsAudioUrl(url);
    setTtsEngine('google');
    setIsSpeechPaused(false);
    return true;
  };

  const startTts = (text: string) => {
    setTtsError('');
    stopTts();
    const speechStarted = startSpeechSynthesis(text);
    if (!speechStarted) {
      startGoogleTts(text);
    }
  };

  const togglePlayPause = () => {
    if (!latestAssistantMessage) return;
    if (ttsEngine === 'speech') {
      if (isSpeaking && !isSpeechPaused) {
        window.speechSynthesis.pause();
        setIsSpeechPaused(true);
        return;
      }
      if (isSpeechPaused) {
        window.speechSynthesis.resume();
        setIsSpeechPaused(false);
        return;
      }
      startTts(latestAssistantMessage);
      return;
    }
    if (!ttsAudioRef.current) {
      startTts(latestAssistantMessage);
      return;
    }
    if (isSpeaking) {
      ttsAudioRef.current.pause();
      setIsSpeechPaused(true);
    } else {
      void ttsAudioRef.current.play();
      setIsSpeechPaused(false);
    }
  };

  useEffect(() => {
    if (!latestAssistantMessage) return;
    if (lastSpokenRef.current === latestAssistantMessage) return;
    lastSpokenRef.current = latestAssistantMessage;
    startTts(latestAssistantMessage);
  }, [latestAssistantMessage]);

  useEffect(() => {
    if (ttsAudioRef.current) {
      ttsAudioRef.current.volume = ttsVolume;
      ttsAudioRef.current.playbackRate = ttsRate;
    }
  }, [ttsVolume, ttsRate]);

  useEffect(() => {
    if (!ttsAudioUrl || !ttsAudioRef.current) return;
    ttsAudioRef.current.src = ttsAudioUrl;
    void ttsAudioRef.current.play().catch(() => {
      setTtsError('Audio autoplay was blocked. Please press play to hear the response.');
      setIsSpeaking(false);
      setIsSpeechPaused(true);
    });
  }, [ttsAudioUrl]);

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
    lastSpokenRef.current = null;
    stopTts();
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
      if (typeof MediaRecorder === 'undefined') {
        setError('This browser does not support audio recording. Please try another browser.');
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferredTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
      ];
      const supportedType = preferredTypes.find((type) => MediaRecorder.isTypeSupported(type));
      const mediaRecorder = supportedType
        ? new MediaRecorder(stream, { mimeType: supportedType })
        : new MediaRecorder(stream);
      mimeTypeRef.current = supportedType ?? null;
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      mediaRecorder.onstop = () => {
        const blobType = chunksRef.current[0]?.type || mimeTypeRef.current || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: blobType });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        setVoiceDraft('');
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
    setIsTranscribing(true);
    setError('');
    try {
      const { transcription } = await transcribeEnglishPilotAudio(audioBlob);
      if (!transcription || transcription.startsWith('[')) {
        setError('Unable to transcribe audio. Please try again.');
        return;
      }
      setVoiceDraft(transcription.trim());
    } catch (err) {
      console.error('STT error:', err);
      setError('Unable to transcribe audio. Please check the backend.');
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleVoiceSend = async () => {
    if (!voiceDraft.trim()) {
      setError('Please transcribe your recording before sending.');
      return;
    }
    const nextMessages = [...messages, { role: 'user', content: voiceDraft.trim() }];
    setMessages(nextMessages);
    setAudioBlob(null);
    setAudioUrl(null);
    setVoiceDraft('');
    await sendMessage(nextMessages);
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

          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-800 dark:bg-slate-800/40">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase text-slate-500">Response Audio</p>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  {isSpeaking && !isSpeechPaused && 'Playing now'}
                  {isSpeechPaused && 'Paused'}
                  {!isSpeaking && !isSpeechPaused && 'Ready to play'}
                  {ttsEngine !== 'none' && ` • ${ttsEngine === 'speech' ? 'Web Speech' : 'Google TTS'}`}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={togglePlayPause}
                  disabled={!latestAssistantMessage}
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-3 py-2 text-xs font-semibold text-white shadow-lg transition hover:bg-indigo-700 disabled:opacity-60"
                >
                  {isSpeaking && !isSpeechPaused ? <Pause size={14} /> : <Play size={14} />}
                  {isSpeaking && !isSpeechPaused ? 'Pause' : 'Play'}
                </button>
                <button
                  onClick={stopTts}
                  disabled={!latestAssistantMessage}
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-300 disabled:opacity-60 dark:bg-slate-700 dark:text-slate-200"
                >
                  <Square size={14} />
                  Stop
                </button>
              </div>
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <label className="text-xs font-semibold uppercase text-slate-500">
                Volume
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={ttsVolume}
                  onChange={(event) => setTtsVolume(Number(event.target.value))}
                  className="mt-2 w-full"
                />
              </label>
              <label className="text-xs font-semibold uppercase text-slate-500">
                Speed
                <input
                  type="range"
                  min="0.6"
                  max="1.4"
                  step="0.1"
                  value={ttsRate}
                  onChange={(event) => setTtsRate(Number(event.target.value))}
                  className="mt-2 w-full"
                />
              </label>
            </div>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
              {latestAssistantMessage
                ? `Now reading: ${latestAssistantMessage}`
                : 'Send a message to hear the response read aloud.'}
            </p>
            {ttsError && (
              <p className="mt-2 text-xs text-red-600 dark:text-red-300">{ttsError}</p>
            )}
            <audio
              ref={ttsAudioRef}
              onPlay={() => {
                setIsSpeaking(true);
                setIsSpeechPaused(false);
              }}
              onPause={() => {
                if (ttsAudioRef.current?.currentTime === 0 || ttsAudioRef.current?.ended) {
                  setIsSpeaking(false);
                } else {
                  setIsSpeechPaused(true);
                }
              }}
              onEnded={() => {
                setIsSpeaking(false);
                setIsSpeechPaused(false);
              }}
              onError={() => {
                setIsSpeaking(false);
                setIsSpeechPaused(false);
                setTtsError('Unable to play audio. Please try again.');
              }}
              className="hidden"
            />
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
                {audioBlob && <span className="text-xs text-slate-500">Recording ready.</span>}
              </div>
              {audioUrl && (
                <audio controls src={audioUrl} className="w-full" />
              )}
              <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                <button
                  onClick={() => void handleVoiceSubmit()}
                  disabled={!audioBlob || isTranscribing}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-300 disabled:opacity-60 dark:bg-slate-800 dark:text-slate-200"
                >
                  {isTranscribing ? <Loader2 className="animate-spin" size={16} /> : <Mic size={16} />}
                  {isTranscribing ? 'Transcribing...' : 'Transcribe Recording'}
                </button>
                <button
                  onClick={() => void handleVoiceSend()}
                  disabled={!voiceDraft || isLoading}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-indigo-700 disabled:opacity-60"
                >
                  <Send size={16} />
                  Send Reply
                </button>
              </div>
              <textarea
                value={voiceDraft}
                onChange={(event) => setVoiceDraft(event.target.value)}
                placeholder="Transcription will appear here. You can edit before sending."
                rows={3}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
