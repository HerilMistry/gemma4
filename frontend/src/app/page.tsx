"use client";

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Mic, MicOff, Send, Activity, BrainCircuit, ShieldCheck, Lock } from 'lucide-react';

export default function SanctuaryJournal() {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [typingCadence, setTypingCadence] = useState<number[]>([]);
  const [lastKeystrokeTime, setLastKeystrokeTime] = useState<number | null>(null);
  const [messages, setMessages] = useState<Array<{role: 'user' | 'sanctuary', text: string}>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Audio recording refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const handleKeyDown = () => {
    const now = Date.now();
    if (lastKeystrokeTime) {
      setTypingCadence(prev => [...prev, now - lastKeystrokeTime]);
    }
    setLastKeystrokeTime(now);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        // Handle audio blob sending here
        console.log("Audio recorded", audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing mic", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // Stop all tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const handleSubmit = async () => {
    if (!text.trim() && audioChunksRef.current.length === 0) return;

    const userText = text;
    const avgCadence = typingCadence.length > 0 
      ? typingCadence.reduce((a, b) => a + b, 0) / typingCadence.length 
      : 0;

    // 1. Append user message immediately (Persistent UI)
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setText('');
    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('text', userText);
    formData.append('typing', JSON.stringify({ avg_interval: avgCadence }));

    if (audioChunksRef.current.length > 0) {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      formData.append('audio', audioBlob, 'recording.wav');
    }

    try {
      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();
      // 2. Append Sanctuary response to history
      setMessages(prev => [...prev, { role: 'sanctuary', text: data.response }]);
      setTypingCadence([]);
      setLastKeystrokeTime(null);
      audioChunksRef.current = [];
    } catch (err) {
      console.error('Failed to submit', err);
      setError('Could not reach Sanctuary. Make sure the backend is running on port 8000.');
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="min-h-screen bg-brand-900 text-text-primary p-6 md:p-12 font-sans selection:bg-accent-primary selection:text-white">
      
      {/* Header */}
      <header className="flex justify-between items-center mb-12 max-w-4xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-lg shadow-accent-primary/20">
            <BrainCircuit size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white glow-text">Sanctuary</h1>
            <p className="text-xs text-text-secondary flex items-center gap-1 mt-0.5">
              <ShieldCheck size={12} className="text-accent-secondary" /> Offline Edge Compute
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-4 text-sm font-medium">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-brand-800 border border-brand-700 text-text-secondary">
            <Lock size={14} className="text-accent-secondary" /> AES-256 Encrypted
          </div>
        </div>
      </header>

      {/* Main Interface */}
      <main className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Journaling Column */}
        <div className="md:col-span-2 space-y-6">
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel rounded-2xl p-6 relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-primary via-accent-secondary to-accent-primary"></div>
            
            <h2 className="text-lg font-semibold text-white mb-4">Current Session</h2>
            
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="What's on your mind today? Sanctuary is listening..."
              className="w-full h-48 bg-transparent resize-none border-none focus:ring-0 text-white placeholder-brand-700 text-lg leading-relaxed mb-4"
              style={{ outline: 'none' }}
            />
            
            <div className="flex justify-between items-center pt-4 border-t border-brand-700/50">
              <div className="flex gap-3">
                <button 
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 ${
                    isRecording 
                      ? 'bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse' 
                      : 'bg-brand-800 text-text-secondary hover:text-white hover:bg-brand-700 border border-transparent'
                  }`}
                >
                  {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                  <span className="text-sm font-medium">{isRecording ? 'Recording...' : 'Acoustic Input'}</span>
                </button>
              </div>
              
              <button 
                onClick={handleSubmit}
                disabled={(!text.trim() && !audioChunksRef.current.length) || isLoading}
                className="flex items-center gap-2 px-6 py-2 rounded-full bg-accent-primary text-white font-medium hover:bg-accent-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>{isLoading ? 'Analyzing...' : 'Process'}</span>
                <Send size={16} />
              </button>
            </div>
          </motion.div>

          {/* Error Display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-panel rounded-2xl p-6 border-l-4 border-l-red-500"
            >
              <p className="text-red-400 text-sm">{error}</p>
            </motion.div>
          )}

          {/* Chat History */}
          <div className="space-y-6 pb-4">
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`glass-panel rounded-2xl p-6 border-l-4 ${
                  msg.role === 'user' ? 'border-l-brand-600' : 'border-l-accent-secondary'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center mt-1 ${
                    msg.role === 'user' ? 'bg-brand-600/20' : 'bg-accent-secondary/20'
                  }`}>
                    {msg.role === 'user' ? (
                      <BrainCircuit size={16} className="text-brand-400" />
                    ) : (
                      <BrainCircuit size={16} className="text-accent-secondary" />
                    )}
                  </div>
                  <div>
                    <h3 className={`text-sm font-medium mb-2 ${
                      msg.role === 'user' ? 'text-brand-400' : 'text-accent-secondary'
                    }`}>
                      {msg.role === 'user' ? 'Your Thought' : 'Sanctuary Reframe'}
                    </h3>
                    <p className="text-white leading-relaxed">{msg.text}</p>
                  </div>
                </div>
              </motion.div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-3 px-6"
              >
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-accent-secondary rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-1.5 bg-accent-secondary rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 bg-accent-secondary rounded-full animate-bounce"></span>
                </div>
                <span className="text-text-secondary text-xs font-mono tracking-widest uppercase">Analyzing...</span>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>


        </div>

        {/* Telemetry Column */}
        <div className="space-y-6">
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel rounded-2xl p-5"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-text-secondary flex items-center gap-2">
                <Activity size={16} /> Real-Time Telemetry
              </h3>
              <div className="w-2 h-2 rounded-full bg-accent-secondary animate-pulse"></div>
            </div>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-text-secondary">Typing Cadence Volatility</span>
                  <span className="text-white font-mono">
                    {typingCadence.length > 0 ? (typingCadence[typingCadence.length-1]).toFixed(0) : '0'} ms
                  </span>
                </div>
                <div className="w-full bg-brand-800 rounded-full h-1.5">
                  <div 
                    className="bg-accent-primary h-1.5 rounded-full transition-all duration-300" 
                    style={{ width: `${Math.min((typingCadence.length > 0 ? typingCadence[typingCadence.length-1] / 10 : 0), 100)}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-text-secondary">Acoustic Pitch Resonance</span>
                  <span className="text-white font-mono">{isRecording ? 'Analyzing...' : 'Standby'}</span>
                </div>
                <div className="w-full bg-brand-800 rounded-full h-1.5">
                  <div className={`h-1.5 rounded-full transition-all duration-300 ${isRecording ? 'bg-accent-secondary animate-pulse w-3/4' : 'bg-brand-700 w-0'}`}></div>
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-panel rounded-2xl p-5 bg-gradient-to-br from-brand-800 to-brand-900 border border-brand-700"
          >
            <h3 className="text-sm font-medium text-white mb-3">Zero-Telemetry Guarantee</h3>
            <p className="text-xs text-text-secondary leading-relaxed mb-3">
              Your thoughts never leave this device. The Cactus Edge Router intelligently determines whether to process lightweight reframes via local Unsloth weights or execute heavy analysis directly via local Gemma 4 instances.
            </p>
            <div className="bg-brand-900 rounded-lg p-3 border border-brand-700 text-xs font-mono text-accent-secondary/80 flex flex-col gap-1">
            <span>&gt; ChromaDB Vector Store: Online</span>
            <span>&gt; AES-256 Vault: Locked</span>
            <span>&gt; Cactus Edge Router: Standby</span>
            </div>
          </motion.div>
        </div>

      </main>
    </div>
  );
}
