"use client";

import { useState, useRef, useEffect } from 'react';
import { Home, BrainCircuit, Settings, History, Menu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Premium Components
import HomeTab from '@/components/HomeTab';
import TherapyTab from '@/components/TherapyTab';
import VaultTab from '@/components/VaultTab';
import HistorySidebar from '@/components/HistorySidebar';

export default function SanctuaryJournal() {
  // State
  const [activeTab, setActiveTab] = useState<'home' | 'therapy' | 'vault'>('home');
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [typingCadence, setTypingCadence] = useState<number[]>([]);
  const [lastKeystrokeTime, setLastKeystrokeTime] = useState<number | null>(null);
  const [messages, setMessages] = useState<Array<{
    role: 'user' | 'assistant', 
    text: string, 
    distortions?: Array<{name: string, description: string}>
  }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [telemetryLogs, setTelemetryLogs] = useState<string[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  
  // Refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  // --- Premium Feature: IndexedDB Persistence for Drafts ---
  useEffect(() => {
    const initDB = async () => {
      const request = indexedDB.open('SanctuaryVault', 1);
      request.onupgradeneeded = (e: any) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains('drafts')) {
          db.createObjectStore('drafts');
        }
      };
      request.onsuccess = (e: any) => {
        const db = e.target.result;
        const tx = db.transaction('drafts', 'readonly');
        const store = tx.objectStore('drafts');
        const getReq = store.get('current_draft');
        getReq.onsuccess = () => {
          if (getReq.result && text === '') setText(getReq.result);
        };
      };
    };
    initDB();
  }, []);

  // Save draft whenever text changes
  useEffect(() => {
    if (!text) return;
    const request = indexedDB.open('SanctuaryVault', 1);
    request.onsuccess = (e: any) => {
      const db = e.target.result;
      const tx = db.transaction('drafts', 'readwrite');
      const store = tx.objectStore('drafts');
      store.put(text, 'current_draft');
    };
  }, [text]);

  const clearDraft = () => {
    const request = indexedDB.open('SanctuaryVault', 1);
    request.onsuccess = (e: any) => {
      const db = e.target.result;
      const tx = db.transaction('drafts', 'readwrite');
      const store = tx.objectStore('drafts');
      store.delete('current_draft');
    };
  };

  // Helpers
  const triggerHaptic = (duration: number | number[] = 50) => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(duration as VibratePattern);
    }
  };

  const addTelemetryLog = (log: string) => {
    setTelemetryLogs(prev => [log, ...prev].slice(0, 50));
  };

  // --- Session Management ---
  const startNewChat = () => {
    setMessages([]);
    setActiveSessionId(null);
    setText('');
    setTypingCadence([]);
    setActiveTab('therapy');
    triggerHaptic([10, 30]);
  };

  const loadSession = async (sessionId: string) => {
    setIsLoading(true);
    setActiveSessionId(sessionId);
    setActiveTab('therapy');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/sessions/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.map((m: any) => ({ role: m.role, text: m.text })));
      }
    } catch (err) {
      console.error("Failed to load session", err);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Audio Logic ---
  const startRecording = async () => {
    triggerHaptic(50);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mediaRecorderRef.current.start();
      setIsRecording(true);

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;
    } catch (err) { console.error("Mic access failed", err); }
  };

  const stopRecording = () => {
    triggerHaptic(30);
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
      if (audioContextRef.current) audioContextRef.current.close();
    }
  };

  const handleKeyDown = () => {
    const now = Date.now();
    if (lastKeystrokeTime) setTypingCadence(prev => [...prev, now - lastKeystrokeTime].slice(-50));
    setLastKeystrokeTime(now);
  };

  const handleSubmit = async () => {
    if (!text.trim() && audioChunksRef.current.length === 0) return;
    triggerHaptic([20, 40, 20]);

    const userText = text;
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setText('');
    clearDraft();
    setIsLoading(true);
    
    const formData = new FormData();
    formData.append('text', userText);
    formData.append('typing', JSON.stringify({ avg_interval: typingCadence.length > 0 ? typingCadence.reduce((a, b) => a + b, 0) / typingCadence.length : 0 }));
    formData.append('history', JSON.stringify(messages.slice(-6)));
    if (activeSessionId) formData.append('session_id', activeSessionId);

    if (audioChunksRef.current.length > 0) {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      formData.append('audio', audioBlob, 'recording.wav');
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyze/stream`, {
        method: 'POST',
        body: formData,
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = ""; 
      if (!reader) throw new Error("Stream failed");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ') || trimmed.includes('[DONE]')) continue;
          
          try {
            const data = JSON.parse(trimmed.slice(6));
            if (data.type === 'metadata') {
              if (data.session_id && !activeSessionId) setActiveSessionId(data.session_id);
              setMessages(prev => [...prev, { role: 'assistant', text: '', distortions: data.distortions }]);
            } else if (data.type === 'token') {
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = { ...last, text: last.text + data.text };
                }
                return updated;
              });
            }
          } catch (e) { }
        }
      }
      setTypingCadence([]);
      setLastKeystrokeTime(null);
      audioChunksRef.current = [];

      // Periodically trigger summarization for long-term memory (every 5 messages)
      if (messages.length > 0 && messages.length % 5 === 0) {
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/sessions/${activeSessionId}/summarize`, { method: 'POST' }).catch(() => {});
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Core disconnected. Please check your local server.' }]);
    } finally { setIsLoading(false); }
  };

  return (
    <div className="bg-black min-h-[100dvh] relative overflow-hidden font-sans text-white">
      <div className="mesh-bg"></div>
      
      <HistorySidebar 
        isOpen={isHistoryOpen} 
        onClose={() => setIsHistoryOpen(false)} 
        onSelectSession={loadSession}
        onNewChat={startNewChat}
        activeSessionId={activeSessionId}
      />

      <main className="relative z-10 h-[100dvh] flex flex-col">
        {/* Header with History Trigger */}
        <header className="pt-8 px-6 flex justify-between items-center z-20">
          <button 
            onClick={() => { triggerHaptic(10); setIsHistoryOpen(true); }}
            className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <Menu size={20} />
          </button>
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-bold tracking-[0.3em] uppercase text-accent-primary">Sanctuary</span>
            <span className="text-xs text-text-muted font-medium">Industry Core v3.2.8</span>
          </div>
          <button 
            onClick={startNewChat}
            className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-colors text-accent-primary"
          >
            <History size={20} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto pb-24 hide-scrollbar">
          <AnimatePresence mode="wait">
            {activeTab === 'home' && (
              <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <HomeTab 
                  onStartSession={() => setActiveTab('therapy')} 
                  triggerHaptic={triggerHaptic}
                  selectedMood={selectedMood}
                  setSelectedMood={setSelectedMood}
                />
              </motion.div>
            )}
            {activeTab === 'therapy' && (
              <motion.div key="therapy" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                <TherapyTab 
                  messages={messages}
                  isLoading={isLoading}
                  isRecording={isRecording}
                  text={text}
                  setText={setText}
                  onStartRecording={startRecording}
                  onStopRecording={stopRecording}
                  onSubmit={handleSubmit}
                  onKeyDown={handleKeyDown}
                  analyser={analyserRef.current}
                  selectedMood={selectedMood}
                />
              </motion.div>
            )}
            {activeTab === 'vault' && (
              <motion.div key="vault" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <VaultTab 
                  telemetryLogs={telemetryLogs}
                  typingCadence={typingCadence}
                  isRecording={isRecording}
                  isLoading={isLoading}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <nav className="fixed bottom-0 left-0 w-full bg-black/40 backdrop-blur-3xl border-t border-white/5 pt-3 pb-8 px-8 z-50">
          <div className="max-w-md mx-auto flex justify-between items-center h-14">
            <button onClick={() => { triggerHaptic(15); setActiveTab('home'); }} className={`flex flex-col items-center gap-1.5 transition-all ${activeTab === 'home' ? 'text-white scale-110' : 'text-text-muted hover:text-white'}`}>
              <Home size={24} className={activeTab === 'home' ? 'fill-white' : ''} />
              <span className="text-[10px] font-bold tracking-widest uppercase">Home</span>
            </button>
            <button onClick={() => { triggerHaptic(15); setActiveTab('therapy'); }} className={`flex flex-col items-center gap-1.5 transition-all ${activeTab === 'therapy' ? 'text-accent-primary scale-110' : 'text-text-muted hover:text-white'}`}>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center -mt-6 bg-brand-800 border-2 transition-all ${activeTab === 'therapy' ? 'border-accent-primary shadow-[0_0_20px_rgba(29,185,84,0.3)]' : 'border-white/5'}`}>
                <BrainCircuit size={24} />
              </div>
              <span className="text-[10px] font-bold tracking-widest uppercase mt-1">Session</span>
            </button>
            <button onClick={() => { triggerHaptic(15); setActiveTab('vault'); }} className={`flex flex-col items-center gap-1.5 transition-all ${activeTab === 'vault' ? 'text-white scale-110' : 'text-text-muted hover:text-white'}`}>
              <Settings size={24} className={activeTab === 'vault' ? 'fill-white' : ''} />
              <span className="text-[10px] font-bold tracking-widest uppercase">Vault</span>
            </button>
          </div>
        </nav>
      </main>
    </div>
  );
}
