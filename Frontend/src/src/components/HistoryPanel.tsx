import { motion, AnimatePresence } from 'motion/react';
import { History, Clock } from 'lucide-react';
import { useStore } from '../lib/store';

export function HistoryPanel() {
  const { history, restoreFromHistory } = useStore();

  if (history.length === 0) {
    return null;
  }

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="p-6 rounded-xl bg-card dark:bg-gradient-to-br dark:from-white/5 dark:to-white/[0.02] border-2 border-[hsl(var(--border))] dark:border-white/10 shadow-sm dark:shadow-none backdrop-blur-sm"
    >
      <div className="flex items-center gap-2 mb-4">
        <History className="w-5 h-5 text-muted-foreground" />
        <h2 className="font-semibold text-foreground">Recent Questions</h2>
      </div>

      <div className="space-y-2">
        <AnimatePresence>
          {history.map((item) => (
            <motion.button
              key={item.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => restoreFromHistory(item.id)}
              className="w-full text-left p-3 rounded-lg bg-muted/50 dark:bg-white/5 border border-border dark:border-white/10 hover:bg-muted dark:hover:bg-white/10 dark:hover:border-white/20 transition-all"
            >
              <div className="flex items-start gap-2">
                <Clock className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-foreground line-clamp-2">{item.question}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatTime(item.timestamp)}
                  </p>
                </div>
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
