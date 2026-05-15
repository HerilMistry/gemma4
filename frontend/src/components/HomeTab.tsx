"use client";

import { motion } from 'framer-motion';
import { Play, Clock, User, BrainCircuit } from 'lucide-react';

interface HomeTabProps {
  onStartSession: () => void;
  triggerHaptic: (d: number) => void;
}

export default function HomeTab({ onStartSession, triggerHaptic }: HomeTabProps) {
  return (
    <div className="px-4 pt-12 pb-6 animate-slide-up">
      <div className="flex justify-between items-center mb-8">
        <div>
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em] mb-2">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-white leading-tight">
            {new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 17 ? 'Good afternoon' : 'Good evening'}
          </h1>
        </div>
        <div className="w-12 h-12 rounded-full bg-brand-800 border border-white/5 flex items-center justify-center shadow-inner">
          <User size={22} className="text-text-secondary" />
        </div>
      </div>

      {/* Mood Check-in */}
      <div className="mb-10">
        <h2 className="text-sm font-bold text-text-secondary uppercase tracking-widest mb-4">How are you feeling?</h2>
        <div className="flex gap-3 overflow-x-auto hide-scrollbar -mx-4 px-4">
          {['😔', '😐', '🙂', '🤩', '😤'].map((mood, idx) => (
            <button 
              key={idx}
              onClick={() => triggerHaptic(10)}
              className="flex-shrink-0 w-16 h-16 rounded-2xl bg-brand-800/40 border border-white/5 flex items-center justify-center text-2xl hover:bg-brand-700/60 hover:scale-105 transition-all duration-300"
            >
              {mood}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-2 gap-4 mb-12">
        <motion.div 
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => { triggerHaptic(30); onStartSession(); }}
          className="premium-card flex items-center overflow-hidden cursor-pointer group"
        >
          <div className="w-16 h-16 bg-accent-primary flex items-center justify-center group-hover:bg-accent-secondary transition-colors duration-500">
            <Play size={24} className="text-black fill-black ml-1" />
          </div>
          <span className="font-bold text-sm px-4 text-white">Start Session</span>
        </motion.div>
        
        <motion.div 
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="premium-card flex items-center overflow-hidden cursor-pointer group"
        >
          <div className="w-16 h-16 bg-brand-800 flex items-center justify-center group-hover:bg-brand-700 transition-colors">
            <Clock size={24} className="text-text-secondary" />
          </div>
          <span className="font-bold text-sm px-4 text-white">History</span>
        </motion.div>
      </div>

      {/* Jump back in Section */}
      <div className="mb-10">
        <div className="flex justify-between items-end mb-5">
          <h2 className="text-2xl font-bold text-white tracking-tight">Jump back in</h2>
          <span className="text-xs font-bold text-accent-primary uppercase tracking-widest cursor-pointer">Show all</span>
        </div>
        <div className="flex overflow-x-auto gap-5 pb-6 hide-scrollbar -mx-4 px-4">
          {[1, 2, 3].map((i) => (
            <motion.div 
              key={i} 
              whileHover={{ y: -5 }}
              className="min-w-[160px] flex flex-col gap-4 cursor-pointer group"
            >
              <div className="w-full aspect-square bg-brand-800/60 rounded-2xl p-5 flex flex-col justify-between border border-white/5 group-hover:bg-brand-800 transition-all duration-500 relative overflow-hidden">
                <div className="absolute -top-10 -right-10 w-24 h-24 bg-accent-primary/10 blur-2xl rounded-full"></div>
                <BrainCircuit size={28} className="text-accent-primary group-hover:scale-110 transition-transform" />
                <span className="text-[10px] font-mono font-bold text-text-muted tracking-widest uppercase">May 1{i} • 14:00</span>
              </div>
              <span className="text-sm font-semibold text-white line-clamp-2 leading-snug group-hover:text-accent-secondary transition-colors">Processing anxiety about upcoming deadline...</span>
            </motion.div>
          ))}
        </div>
      </div>
      
      {/* Featured Module */}
      <div className="relative w-full h-56 rounded-3xl overflow-hidden border border-white/5 group cursor-pointer">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-800 to-brand-950 z-0"></div>
        <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-accent-primary/20 blur-[80px] rounded-full z-10 group-hover:bg-accent-primary/30 transition-all duration-700"></div>
        
        <div className="relative z-20 h-full p-8 flex flex-col justify-center max-w-[80%]">
           <span className="text-[10px] font-bold text-accent-primary uppercase tracking-[0.3em] mb-3">Recommended for you</span>
           <h3 className="text-3xl font-bold text-white mb-3 tracking-tight">Cognitive Reframing</h3>
           <p className="text-sm text-text-secondary mb-6 leading-relaxed">A 10-minute guided protocol to challenge distorted thoughts and find balance.</p>
           <div>
             <button className="bg-white text-black px-8 py-3 rounded-full font-bold text-sm tracking-wide hover:scale-105 active:scale-95 transition-all shadow-xl">Start Module</button>
           </div>
        </div>
      </div>
    </div>
  );
}
