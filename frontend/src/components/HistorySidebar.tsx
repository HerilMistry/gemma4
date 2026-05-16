"use client";

import { useEffect, useState } from 'react';
import { Clock, MessageSquare, Plus, X } from 'lucide-react';
import { motion } from 'framer-motion';

interface Session {
  id: string;
  start_time: string;
  preview: string;
}

interface HistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  activeSessionId: string | null;
}

export default function HistorySidebar({ isOpen, onClose, onSelectSession, onNewChat, activeSessionId }: HistorySidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSessions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/sessions`);
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (err) {
      console.error("Failed to fetch sessions", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchSessions();
  }, [isOpen]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60]"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <motion.aside
        initial={{ x: '-100%' }}
        animate={{ x: isOpen ? 0 : '-100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed top-0 left-0 h-full w-4/5 max-w-sm bg-black/40 backdrop-blur-3xl border-r border-white/10 z-[70] flex flex-col"
      >
        <div className="p-6 flex justify-between items-center border-b border-white/5">
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Clock size={20} className="text-accent-primary" />
            Chat History
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-text-muted transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-4">
          <button 
            onClick={() => { onNewChat(); onClose(); }}
            className="w-full py-3 px-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center gap-2 transition-all group"
          >
            <Plus size={18} className="group-hover:scale-110 transition-transform" />
            <span className="font-semibold">New Session</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 pb-8 hide-scrollbar">
          {isLoading ? (
            <div className="flex flex-col gap-4 mt-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-20 w-full rounded-2xl bg-white/5 animate-pulse" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center mt-12 text-text-muted px-8">
              <MessageSquare size={40} className="mx-auto mb-4 opacity-20" />
              <p className="text-sm">No past sessions found. Your therapeutic journey starts here.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-2 mt-2">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => { onSelectSession(session.id); onClose(); }}
                  className={`p-4 rounded-2xl text-left transition-all border ${
                    activeSessionId === session.id 
                      ? 'bg-brand-800/20 border-accent-primary/30 shadow-[0_4px_20px_rgba(29,185,84,0.1)]' 
                      : 'bg-white/5 border-transparent hover:bg-white/10'
                  }`}
                >
                  <p className="text-xs font-medium text-text-muted mb-1">{formatDate(session.start_time)}</p>
                  <p className="text-sm font-semibold text-white truncate">{session.preview}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-white/5 text-[10px] uppercase tracking-widest text-center text-text-muted font-bold">
          Sanctuary Vault v3.2.7
        </div>
      </motion.aside>
    </>
  );
}
