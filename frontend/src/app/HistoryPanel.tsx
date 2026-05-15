import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, BrainCircuit } from 'lucide-react';

type Distortion = {
  name: string;
  description: string;
};

type Message = {
  role: string;
  text: string;
  distortions?: Distortion[];
};

type Props = {
  history: Record<string, Message[]>;
};

const HistoryPanel: React.FC<Props> = ({ history }) => {
  const [expandedDate, setExpandedDate] = useState<string | null>(null);

  const sortedDates = Object.keys(history).sort((a, b) => (a < b ? 1 : -1)); // newest first

  const toggle = (date: string) => {
    setExpandedDate(expandedDate === date ? null : date);
  };

  return (
    <div className="space-y-4 mb-6">
      {sortedDates.map((date) => (
        <motion.div
          key={date}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel rounded-2xl"
        >
          <button
            onClick={() => toggle(date)}
            className="w-full flex justify-between items-center p-4 text-left"
          >
            <div className="flex items-center gap-2">
              <BrainCircuit size={16} className="text-accent-primary" />
              <span className="font-medium text-text-primary">{date}</span>
            </div>
            {expandedDate === date ? (
              <ChevronUp size={16} className="text-text-secondary" />
            ) : (
              <ChevronDown size={16} className="text-text-secondary" />
            )}
          </button>
          <AnimatePresence>
            {expandedDate === date && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="border-t border-brand-700/30 p-4"
              >
                {history[date].map((msg, idx) => (
                  <div key={idx} className="mb-3">
                    <div className="flex items-start gap-3">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center mt-1 ${
                          msg.role === 'user' ? 'bg-brand-600/20' : 'bg-accent-secondary/20'
                        }`}
                      >
                        <BrainCircuit size={14} className={msg.role === 'user' ? 'text-brand-400' : 'text-accent-secondary'} />
                      </div>
                      <div>
                        <h4 className={`text-sm font-medium mb-1 ${msg.role === 'user' ? 'text-brand-400' : 'text-accent-secondary'}`}>
                          {msg.role === 'user' ? 'You' : 'Sanctuary'}
                        </h4>
                        <p className="text-white whitespace-pre-wrap text-sm">{msg.text}</p>
                        {msg.distortions && msg.distortions.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-brand-700/30">
                            <div className="text-[10px] text-text-secondary uppercase tracking-widest mb-1 font-semibold">
                              Distortions Identified
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {msg.distortions.map((d, i) => (
                                <div
                                  key={i}
                                  className="px-2 py-1 rounded bg-accent-primary/10 border border-accent-primary/30 text-accent-primary text-[10px] font-bold uppercase cursor-help"
                                  title={d.description}
                                >
                                  {d.name.replace('_', ' ')}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      ))}
    </div>
  );
};

export default HistoryPanel;
