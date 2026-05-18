"use client";

import { useEffect, useRef } from 'react';
import { Mic, Send, StopCircle, Sparkles, User, Brain, Heart, ArrowRight } from 'lucide-react';
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
  selectedMood: string | null;
}

export default function TherapyTab({ 
  messages, isLoading, isRecording, text, setText, 
  onStartRecording, onStopRecording, onSubmit, onKeyDown, analyser, selectedMood 
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

  const getMoodPrompt = (mood: string) => {
    switch (mood.toLowerCase()) {
      case 'stressed':
        return "I am feeling stressed and overwhelmed today. Let's work together to challenge some of these thoughts.";
      case 'down':
        return "I've been feeling down and low on energy. I'd love a gentle check-in to reflect on what's on my mind.";
      case 'neutral':
        return "Feeling balanced but want to reflect on my day to maintain my mental grounding.";
      case 'balanced':
        return "I'm in a great head space today! I want to write down some positive patterns and practice gratitude.";
      case 'inspired':
        return "I have a lot of positive energy and inspiration! Let's talk about how to channel it constructively.";
      default:
        return `I am feeling ${mood.toLowerCase()} today and want to explore this feeling.`;
    }
  };

  return (
    <div className="flex flex-col h-full pt-4 max-w-lg mx-auto">
      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-5 space-y-6 pt-4 pb-12 hide-scrollbar"
      >
        {messages.length === 0 && !isLoading && (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <motion.div 
              initial={{ opacity: 0, y: 15, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="glass-panel p-6 rounded-3xl w-full max-w-sm border-white/10 relative overflow-hidden shadow-2xl"
            >
              <div className="absolute -top-10 -left-10 w-28 h-28 bg-accent-primary/10 blur-2xl rounded-full"></div>
              
              {selectedMood ? (
                <>
                  <div className="w-12 h-12 rounded-2xl bg-accent-primary/10 flex items-center justify-center mx-auto mb-4 border border-accent-primary/20">
                    <Heart size={22} className="text-accent-primary animate-pulse" />
                  </div>
                  <h3 className="text-lg font-bold mb-2 text-white">Let's explore feeling "{selectedMood}"</h3>
                  <p className="text-xs text-text-secondary leading-relaxed mb-6">
                    Our Socratic CBT reasoning model is ready to support you. Tap below to focus on this feeling, or share anything else.
                  </p>
                  <button 
                    onClick={() => setText(getMoodPrompt(selectedMood))}
                    className="w-full py-3 rounded-2xl bg-accent-primary hover:bg-accent-secondary text-black font-bold text-xs flex items-center justify-center gap-1.5 hover:scale-[1.02] active:scale-95 transition-all shadow-lg cursor-pointer"
                  >
                    Start with "{selectedMood}" focus <ArrowRight size={14} />
                  </button>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4 border border-white/10">
                    <Sparkles size={20} className="text-accent-primary animate-pulse" />
                  </div>
                  <h3 className="text-lg font-bold mb-2 text-white">Your Sanctuary is Open</h3>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    Begin typing what's on your mind, or tap the microphone to run a secure voice-to-text session locally on your device.
                  </p>
                </>
              )}
            </motion.div>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.4 }}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1.5 px-2">
                {msg.role === 'assistant' ? (
                  <>
                    <div className="w-5 h-5 rounded-full bg-accent-primary/20 flex items-center justify-center">
                      <Brain size={11} className="text-accent-primary" />
                    </div>
                    <span className="text-[9px] font-bold uppercase tracking-widest text-text-muted font-mono">Sanctuary Core</span>
                  </>
                ) : (
                  <>
                    <span className="text-[9px] font-bold uppercase tracking-widest text-text-muted font-mono">You</span>
                    <div className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center">
                      <User size={11} className="text-white" />
                    </div>
                  </>
                )}
              </div>

              <div className={`max-w-[85%] p-4.5 rounded-2xl text-sm leading-relaxed shadow-xl ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-br from-accent-primary to-accent-secondary text-black font-semibold rounded-tr-none' 
                  : 'glass-panel text-white rounded-tl-none border-white/10'
              }`}>
                <ReactMarkdown 
                  components={{
                    p: ({children}) => <p className="mb-2.5 last:mb-0 leading-relaxed">{children}</p>,
                    strong: ({children}) => <strong className={msg.role === 'user' ? 'text-black font-extrabold underline decoration-2' : 'text-accent-primary font-bold'}>{children}</strong>,
                    ul: ({children}) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                    li: ({children}) => <li className="text-xs leading-relaxed">{children}</li>
                  }}
                >
                  {msg.text}
                </ReactMarkdown>

                {msg.distortions && msg.distortions.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-white/5 flex flex-col gap-2">
                    <span className="text-[8px] font-bold text-text-muted uppercase tracking-wider font-mono">Identified Cognitive Distortions:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.distortions.map((d, i) => (
                        <motion.span 
                          whileHover={{ scale: 1.05 }}
                          key={i} 
                          className="text-[9px] font-bold uppercase tracking-tight px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 shadow-inner"
                          title={d.description}
                        >
                          ⚠️ {d.name.replace(/_/g, ' ')}
                        </motion.span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div 
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-3"
          >
            <div className="w-5 h-5 rounded-full bg-accent-primary/20 flex items-center justify-center animate-spin">
              <Sparkles size={11} className="text-accent-primary" />
            </div>
            <div className="glass-panel p-4 rounded-2xl rounded-tl-none border-white/5 shadow-md">
              <div className="flex gap-1.5 items-center py-1">
                <div className="w-2 h-2 rounded-full bg-accent-primary/50 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-accent-primary/50 animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 rounded-full bg-accent-primary/50 animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input Section */}
      <div className="p-5 bg-gradient-to-t from-black via-black/90 to-transparent">
        <div className="relative">
          {/* Visualizer Overlay */}
          {isRecording && (
            <div className="absolute -top-16 left-0 w-full h-12 flex items-center justify-center">
              <div className="w-32 h-full rounded-2xl overflow-hidden bg-white/5 backdrop-blur-md border border-white/10 p-2 shadow-2xl">
                <Visualizer isRecording={isRecording} analyser={analyser} />
              </div>
            </div>
          )}

          <div className="glass-panel rounded-[24px] p-2 flex items-center gap-2 shadow-2xl border-white/10">
            <motion.button 
              whileTap={{ scale: 0.9 }}
              onClick={isRecording ? onStopRecording : onStartRecording}
              className={`w-11 h-11 rounded-full flex items-center justify-center transition-all duration-500 cursor-pointer ${
                isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-white/5 text-text-muted hover:text-white'
              }`}
            >
              {isRecording ? <StopCircle size={22} /> : <Mic size={22} />}
            </motion.button>

            <input 
              type="text" 
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => { if(e.key === 'Enter') { onSubmit(); onKeyDown(); } }}
              placeholder="What's on your mind?"
              className="flex-1 bg-transparent border-none outline-none text-sm px-2 text-white placeholder:text-text-muted/40 font-medium"
            />

            <motion.button 
              whileTap={{ scale: 0.9 }}
              onClick={onSubmit}
              disabled={!text.trim() && !isRecording}
              className={`w-11 h-11 rounded-full flex items-center justify-center transition-all cursor-pointer ${
                text.trim() ? 'bg-accent-primary text-black scale-100 shadow-lg shadow-accent-primary/20' : 'bg-white/5 text-text-muted scale-90 opacity-40'
              }`}
            >
              <Send size={18} />
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
}
