"use client";

import { motion, AnimatePresence } from 'framer-motion';
import { Play, Clock, User, BrainCircuit, Frown, CloudRain, Meh, Smile, Sparkles, ArrowRight } from 'lucide-react';

interface HomeTabProps {
  onStartSession: () => void;
  triggerHaptic: (d: number) => void;
  selectedMood: string | null;
  setSelectedMood: (mood: string | null) => void;
}

export default function HomeTab({ onStartSession, triggerHaptic, selectedMood, setSelectedMood }: HomeTabProps) {
  
  const MOODS = [
    { 
      label: "Stressed", 
      icon: Frown, 
      color: "text-sky-400 border-sky-500/20 bg-sky-500/5", 
      selectedStyle: "bg-sky-500/10 border-sky-400/50 text-sky-300 shadow-[0_0_20px_rgba(56,189,248,0.2)]",
      feedback: "Honoring your stress. You're carrying a lot, but you are safe to slow down and unpack it here."
    },
    { 
      label: "Down", 
      icon: CloudRain, 
      color: "text-indigo-400 border-indigo-500/20 bg-indigo-500/5", 
      selectedStyle: "bg-indigo-500/10 border-indigo-400/50 text-indigo-300 shadow-[0_0_20px_rgba(129,140,248,0.2)]",
      feedback: "It's okay to feel low. Let's take things slow and gently explore what your mind needs today."
    },
    { 
      label: "Neutral", 
      icon: Meh, 
      color: "text-slate-400 border-slate-500/20 bg-slate-500/5", 
      selectedStyle: "bg-slate-500/10 border-slate-400/50 text-slate-300 shadow-[0_0_20px_rgba(203,213,225,0.2)]",
      feedback: "A quiet, steady baseline. An excellent space to reflect, ground yourself, and find balance."
    },
    { 
      label: "Balanced", 
      icon: Smile, 
      color: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5", 
      selectedStyle: "bg-emerald-500/10 border-emerald-400/50 text-emerald-300 shadow-[0_0_20px_rgba(52,211,153,0.2)]",
      feedback: "Splendid! Let's capture this mental clarity and reinforce healthy, positive cognitive pathways."
    },
    { 
      label: "Inspired", 
      icon: Sparkles, 
      color: "text-amber-400 border-amber-500/20 bg-amber-500/5", 
      selectedStyle: "bg-amber-500/10 border-amber-400/50 text-amber-300 shadow-[0_0_20px_rgba(251,191,36,0.25)]",
      feedback: "High creative energy! Let's channel this inspiration into your therapeutic reflection today."
    }
  ];

  const handleMoodSelect = (moodLabel: string) => {
    triggerHaptic(20);
    if (selectedMood === moodLabel) {
      setSelectedMood(null); // Deselect
    } else {
      setSelectedMood(moodLabel);
    }
  };

  const selectedMoodData = MOODS.find(m => m.label === selectedMood);

  return (
    <div className="px-4 pt-12 pb-6 animate-slide-up max-w-lg mx-auto">
      {/* Header Panel */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-[0.25em] mb-1.5 font-mono">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-white leading-tight">
            {new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 17 ? 'Good afternoon' : 'Good evening'}
          </h1>
        </div>
        <motion.div 
          whileHover={{ scale: 1.05, rotate: 5 }}
          className="w-12 h-12 rounded-2xl bg-brand-800 border border-white/10 flex items-center justify-center shadow-lg cursor-pointer hover:bg-brand-700/80 transition-colors"
        >
          <User size={20} className="text-accent-primary" />
        </motion.div>
      </div>

      {/* Mood Check-in */}
      <div className="mb-10 p-5 rounded-3xl bg-brand-800/20 border border-white/5 relative overflow-hidden backdrop-blur-md">
        <div className="absolute -top-12 -right-12 w-28 h-28 bg-accent-primary/5 blur-2xl rounded-full"></div>
        
        <h2 className="text-xs font-bold text-text-secondary uppercase tracking-widest mb-4 font-mono">
          How are you feeling today?
        </h2>
        
        <div className="flex justify-between gap-2 overflow-x-auto hide-scrollbar pb-1">
          {MOODS.map((m, idx) => {
            const Icon = m.icon;
            const isSelected = selectedMood === m.label;
            return (
              <motion.button 
                key={idx}
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handleMoodSelect(m.label)}
                className={`flex-shrink-0 flex flex-col items-center justify-center gap-2 w-[72px] h-[84px] rounded-2xl border transition-all duration-300 cursor-pointer ${
                  isSelected ? m.selectedStyle : `${m.color} hover:bg-white/5 hover:border-white/15`
                }`}
              >
                <Icon size={24} className="stroke-[2px]" />
                <span className="text-[10px] font-bold uppercase tracking-wider font-sans">{m.label}</span>
              </motion.button>
            );
          })}
        </div>

        {/* Dynamic Socratic Feedback with Framer Motion */}
        <AnimatePresence mode="wait">
          {selectedMoodData && (
            <motion.div 
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="mt-5 pt-4 border-t border-white/5 flex flex-col gap-2"
            >
              <p className="text-xs font-medium text-text-secondary leading-relaxed italic">
                "{selectedMoodData.feedback}"
              </p>
              <motion.span 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={() => { triggerHaptic(30); onStartSession(); }}
                className="text-[10px] font-bold uppercase tracking-widest text-accent-primary flex items-center gap-1.5 cursor-pointer mt-1 hover:text-accent-secondary transition-colors"
              >
                Let's process this in your session <ArrowRight size={12} className="animate-pulse" />
              </motion.span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-2 gap-4 mb-10">
        <motion.div 
          whileHover={{ scale: 1.03, y: -2 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => { triggerHaptic(35); onStartSession(); }}
          className="premium-card flex items-center p-1.5 overflow-hidden cursor-pointer group shadow-xl hover:shadow-[0_8px_30px_rgba(0,0,0,0.4)]"
        >
          <div className="w-14 h-14 rounded-2xl bg-accent-primary flex items-center justify-center group-hover:bg-accent-secondary transition-colors duration-500 shadow-lg shadow-accent-primary/20">
            <Play size={20} className="text-black fill-black ml-0.5 stroke-[2.5px]" />
          </div>
          <div className="flex flex-col gap-0.5 px-3">
            <span className="font-bold text-sm text-white">Start Session</span>
            <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider font-mono">Gemma 4 IT</span>
          </div>
        </motion.div>
        
        <motion.div 
          whileHover={{ scale: 1.03, y: -2 }}
          whileTap={{ scale: 0.97 }}
          className="premium-card flex items-center p-1.5 overflow-hidden cursor-pointer group shadow-xl hover:shadow-[0_8px_30px_rgba(0,0,0,0.4)]"
        >
          <div className="w-14 h-14 rounded-2xl bg-brand-800 flex items-center justify-center group-hover:bg-brand-700/80 transition-colors shadow-lg">
            <Clock size={20} className="text-accent-primary stroke-[2px]" />
          </div>
          <div className="flex flex-col gap-0.5 px-3">
            <span className="font-bold text-sm text-white">History</span>
            <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider font-mono">14 Logs Stored</span>
          </div>
        </motion.div>
      </div>

      {/* Jump back in Section */}
      <div className="mb-10">
        <div className="flex justify-between items-end mb-4">
          <h2 className="text-xl font-bold text-white tracking-tight">Recent Sessions</h2>
          <span className="text-[10px] font-bold text-accent-primary uppercase tracking-widest cursor-pointer hover:text-accent-secondary transition-colors font-mono">Show all</span>
        </div>
        <div className="flex overflow-x-auto gap-4 pb-3 hide-scrollbar -mx-4 px-4">
          {[1, 2, 3].map((i) => (
            <motion.div 
              key={i} 
              whileHover={{ y: -4, scale: 1.02 }}
              className="min-w-[150px] flex flex-col gap-3 cursor-pointer group"
            >
              <div className="w-full aspect-square bg-brand-800/40 rounded-2xl p-4.5 flex flex-col justify-between border border-white/5 group-hover:bg-brand-800/80 group-hover:border-white/10 transition-all duration-500 relative overflow-hidden shadow-lg">
                <div className="absolute -top-12 -right-12 w-20 h-20 bg-accent-primary/5 blur-xl rounded-full"></div>
                <BrainCircuit size={24} className="text-accent-primary group-hover:scale-110 transition-transform stroke-[2px]" />
                <span className="text-[9px] font-mono font-bold text-text-muted tracking-widest uppercase">May 1{i} • 14:00</span>
              </div>
              <span className="text-xs font-semibold text-white line-clamp-2 leading-relaxed group-hover:text-accent-primary transition-colors">
                {i === 1 ? "Deconstructing exam-related anxiety..." : i === 2 ? "Reframing impostor feelings..." : "Processing social frustration..."}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
      
      {/* Recommended Socratic CBT Module */}
      <motion.div 
        whileHover={{ y: -4 }}
        onClick={() => { triggerHaptic(15); onStartSession(); if(!selectedMood) setSelectedMood("Stressed"); }}
        className="relative w-full rounded-3xl overflow-hidden border border-white/5 hover:border-white/10 group cursor-pointer shadow-2xl backdrop-blur-md"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-brand-800/80 to-brand-950/90 z-0"></div>
        <div className="absolute -bottom-24 -right-24 w-60 h-60 bg-accent-primary/10 blur-[80px] rounded-full z-10 group-hover:bg-accent-primary/20 transition-all duration-700"></div>
        
        <div className="relative z-20 p-7 flex flex-col justify-center max-w-[85%]">
           <span className="text-[9px] font-bold text-accent-primary uppercase tracking-[0.25em] mb-2 font-mono">Recommended for you</span>
           <h3 className="text-2xl font-bold text-white mb-2 tracking-tight">Socratic Thought Diary</h3>
           <p className="text-xs text-text-secondary mb-5 leading-relaxed">
             A guided 5-step CBT framework to challenge cognitive distortions and recover peaceful perspective.
           </p>
           <div>
             <button className="bg-white text-black px-6 py-2.5 rounded-full font-bold text-xs tracking-wider hover:scale-105 active:scale-95 transition-all shadow-lg hover:bg-accent-secondary hover:text-black">
               Start Reflection
             </button>
           </div>
        </div>
      </motion.div>
    </div>
  );
}
