"use client";

import { motion } from 'framer-motion';
import { Activity, Terminal, ShieldCheck, Database, HardDrive } from 'lucide-react';

interface VaultTabProps {
  telemetryLogs: string[];
  typingCadence: number[];
  isRecording: boolean;
  isLoading: boolean;
}

export default function VaultTab({ telemetryLogs, typingCadence, isRecording, isLoading }: VaultTabProps) {
  const avgInterval = typingCadence.length > 0 
    ? (typingCadence.reduce((a, b) => a + b, 0) / typingCadence.length).toFixed(0) 
    : '0';

  return (
    <div className="px-6 pt-16 pb-10 animate-slide-up">
      <div className="mb-10">
        <h1 className="text-4xl font-bold tracking-tight text-white mb-2 leading-tight">Secure Vault</h1>
        <p className="text-text-secondary text-sm">Real-time edge architecture and local data persistence.</p>
      </div>
      
      <div className="space-y-6">
        {/* Telemetry Card */}
        <div className="premium-card p-6 border-accent-primary/5">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-accent-primary/10 flex items-center justify-center">
              <Activity size={20} className="text-accent-primary" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white uppercase tracking-wider">Edge Telemetry</h3>
              <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Biometric Analysis</p>
            </div>
          </div>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-[11px] mb-2.5 font-bold uppercase tracking-widest">
                <span className="text-text-secondary">Keystroke Latency</span>
                <span className="text-accent-primary font-mono">{avgInterval}ms</span>
              </div>
              <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min((Number(avgInterval) / 8), 100)}%` }}
                  className="bg-accent-primary h-full rounded-full shadow-[0_0_10px_rgba(29,185,84,0.5)] transition-all duration-1000"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[11px] mb-2.5 font-bold uppercase tracking-widest">
                <span className="text-text-secondary">Inference Stream</span>
                <span className="text-accent-secondary font-mono">{isLoading ? 'Processing' : 'Idle'}</span>
              </div>
              <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                <motion.div 
                  animate={{ 
                    width: isLoading ? '100%' : '0%',
                    opacity: isLoading ? [1, 0.5, 1] : 1
                  }}
                  transition={{ 
                    width: { duration: 0.5 },
                    opacity: { repeat: Infinity, duration: 1.5 }
                  }}
                  className="bg-accent-secondary h-full rounded-full"
                />
              </div>
            </div>
          </div>
        </div>

        {/* HUD Card */}
        <div className="premium-card p-6 h-[320px] flex flex-col border-white/5">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-900 border border-white/5 flex items-center justify-center">
                <Terminal size={20} className="text-text-muted" />
              </div>
              <h3 className="text-base font-bold text-white uppercase tracking-wider">System Logs</h3>
            </div>
            <div className="px-2 py-1 rounded-md bg-brand-950 border border-white/5 text-[9px] font-mono text-text-muted">
              v3.2.0-STABLE
            </div>
          </div>
          
          <div className="bg-[#050505] rounded-2xl p-5 border border-white/5 text-[10px] font-mono text-accent-secondary/60 flex flex-col gap-3 flex-1 overflow-y-auto hide-scrollbar shadow-inner">
            <div className="flex items-center gap-2">
              <ShieldCheck size={10} className="text-accent-primary" />
              <span>&gt; AES-256 GCM ENCRYPTION INITIALIZED</span>
            </div>
            <div className="flex items-center gap-2">
              <Database size={10} className="text-accent-primary" />
              <span>&gt; LOCAL CHROMA_DB ATTACHED (154 RECORDS)</span>
            </div>
            <div className="flex items-center gap-2">
              <HardDrive size={10} className="text-accent-primary" />
              <span>&gt; PERSISTENT INDEXED_DB MOUNTED</span>
            </div>
            
            {telemetryLogs.map((log, i) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, x: -5 }} 
                animate={{ opacity: 1, x: 0 }} 
                className={`flex gap-2 ${log.includes('[Inference]') ? 'text-accent-primary font-bold' : ''}`}
              >
                <span>&gt;</span>
                <span>{log}</span>
              </motion.div>
            ))}
            {isLoading && <span className="animate-pulse-subtle">_</span>}
          </div>
        </div>

        {/* Security Info */}
        <div className="p-4 flex items-center gap-4 text-text-muted opacity-60">
           <ShieldCheck size={32} />
           <p className="text-[10px] leading-relaxed uppercase tracking-[0.2em] font-bold">
             All data is stored locally in an encrypted vault. No telemetry leaves this device. 
             Sanctuary is designed for absolute clinical privacy.
           </p>
        </div>
      </div>
    </div>
  );
}
