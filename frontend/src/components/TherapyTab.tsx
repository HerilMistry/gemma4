"use client";

import { useEffect, useRef } from 'react';
import { Mic, Send, StopCircle, Sparkles, User, Brain } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import Visualizer from './Visualizer';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  distortions?: Array<{name: string, description: string}>;
}

interface TherapyTabProps {
  messages: Message[];
  isLoading: boolean;
  isRecording: boolean;
  text: string;
  setText: (text: string) => void;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onSubmit: () => void;
  onKeyDown: () => void;
  analyser: AnalyserNode | null;
}

export default function TherapyTab({ 
  messages, isLoading, isRecording, text, setText, 
  onStartRecording, onStopRecording, onSubmit, onKeyDown, analyser 
}: TherapyTabProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-full pt-4">
      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 space-y-6 pt-4 pb-12 hide-scrollbar"
      >
        {messages.length === 0 && !isLoading && (
          <div className="h-full flex flex-col items-center justify-center text-center px-8 opacity-40">
            <Sparkles size={48} className="mb-4 text-accent-primary animate-pulse" />
            <h3 className="text-xl font-bold mb-2">How are you feeling?</h3>
            <p className="text-sm">Start typing or tap the mic to begin your therapeutic session.</p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1 px-1">
                {msg.role === 'assistant' ? (
                  <>
                    <div className="w-5 h-5 rounded-full bg-accent-primary/20 flex items-center justify-center">
                      <Brain size={12} className="text-accent-primary" />
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Sanctuary</span>
                  </>
                ) : (
                  <>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">You</span>
                    <div className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center">
                      <User size={12} className="text-white" />
                    </div>
                  </>
                )}
              </div>

              <div className={`max-w-[85%] p-4 rounded-3xl text-sm leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-brand-800 text-white rounded-tr-none shadow-lg' 
                  : 'bg-white/5 border border-white/10 text-white rounded-tl-none'
              }`}>
                <ReactMarkdown 
                  components={{
                    p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                    strong: ({children}) => <strong className="text-accent-primary font-bold">{children}</strong>
                  }}
                >
                  {msg.text}
                </ReactMarkdown>

                {msg.distortions && msg.distortions.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-2">
                    {msg.distortions.map((d, i) => (
                      <span key={i} className="text-[9px] font-bold uppercase tracking-tighter px-2 py-0.5 rounded-full bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
                        {d.name.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-start gap-3"
          >
            <div className="w-5 h-5 rounded-full bg-accent-primary/20 flex items-center justify-center animate-spin">
              <Sparkles size={12} className="text-accent-primary" />
            </div>
            <div className="bg-white/5 border border-white/10 p-4 rounded-3xl rounded-tl-none">
              <div className="flex gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-primary/40 animate-bounce" />
                <div className="w-1.5 h-1.5 rounded-full bg-accent-primary/40 animate-bounce [animation-delay:0.2s]" />
                <div className="w-1.5 h-1.5 rounded-full bg-accent-primary/40 animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input Section */}
      <div className="p-6 bg-gradient-to-t from-black via-black/80 to-transparent">
        <div className="max-w-md mx-auto relative">
          {/* Visualizer Overlay */}
          {isRecording && (
            <div className="absolute -top-16 left-0 w-full h-12 flex items-center justify-center">
              <div className="w-32 h-full rounded-2xl overflow-hidden bg-white/5 backdrop-blur-md border border-white/10 p-2">
                <Visualizer isRecording={isRecording} analyser={analyser} />
              </div>
            </div>
          )}

          <div className="glass-panel rounded-[32px] p-2 flex items-center gap-2 shadow-2xl border-white/10">
            <button 
              onClick={isRecording ? onStopRecording : onStartRecording}
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 ${
                isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-white/5 text-text-muted hover:text-white'
              }`}
            >
              {isRecording ? <StopCircle size={24} /> : <Mic size={24} />}
            </button>

            <input 
              type="text" 
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => { if(e.key === 'Enter') { onSubmit(); onKeyDown(); } }}
              placeholder="What's on your mind?"
              className="flex-1 bg-transparent border-none outline-none text-sm px-2 text-white placeholder:text-text-muted/50"
            />

            <button 
              onClick={onSubmit}
              disabled={!text.trim() && !isRecording}
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                text.trim() ? 'bg-accent-primary text-black scale-100' : 'bg-white/5 text-text-muted scale-90 opacity-50'
              }`}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
