import { motion } from 'motion/react';
import { Copy, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { useStore } from '../lib/store';
import { toast } from '../lib/toast';

export function AnswerPanel() {
  const { answer, askStatus, evidence } = useStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!answer) return;

    try {
      await navigator.clipboard.writeText(answer);
      setCopied(true);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy');
    }
  };

  if (askStatus === 'idle' && !answer) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-8 rounded-xl bg-card dark:bg-gradient-to-br dark:from-white/5 dark:to-white/[0.02] border-2 border-[hsl(var(--border))] dark:border-white/10 shadow-sm dark:shadow-none backdrop-blur-sm flex flex-col items-center justify-center gap-4 text-center min-h-[300px]"
      >
        <div className="p-4 rounded-full bg-primary/10 border border-primary/20">
          <Sparkles className="w-8 h-8 text-[hsl(var(--primary))]" />
        </div>
        <div>
          <p className="font-medium text-foreground">Ready to answer</p>
          <p className="text-sm text-muted-foreground mt-1">
            Upload a PDF and ask a question to get started
          </p>
        </div>
      </motion.div>
    );
  }

  if (askStatus === 'loading') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 rounded-xl bg-card dark:bg-gradient-to-br dark:from-white/5 dark:to-white/[0.02] border-2 border-[hsl(var(--border))] dark:border-white/10 shadow-sm dark:shadow-none backdrop-blur-sm"
      >
        <div className="flex items-center gap-3 mb-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <Sparkles className="w-5 h-5 text-[hsl(var(--primary))]" />
          </motion.div>
          <h2 className="font-semibold text-foreground">Generating Answer...</h2>
        </div>

        {/* Skeleton */}
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: [0.3, 0.6, 0.3] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
              className="h-4 bg-muted dark:bg-white/5 rounded"
              style={{ width: `${100 - i * 10}%` }}
            />
          ))}
        </div>
      </motion.div>
    );
  }

  if (askStatus === 'error') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 rounded-xl bg-gradient-to-br from-red-500/10 to-red-500/5 border border-red-500/20 backdrop-blur-sm"
      >
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <div>
            <p className="font-medium text-red-300">Failed to get answer</p>
            <p className="text-sm text-red-400/80 mt-1">
              Please try again or check your connection
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  if (!answer) return null;

  const confidence = evidence.length > 0 ? 'High' : 'Low';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="p-6 rounded-xl bg-card dark:bg-gradient-to-br dark:from-white/5 dark:to-white/[0.02] border-2 border-[hsl(var(--border))] dark:border-white/10 shadow-sm dark:shadow-none backdrop-blur-sm"
    >
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
          <h2 className="font-semibold text-foreground">Answer</h2>
        </div>

        <div className="flex items-center gap-2">
          {/* Confidence */}
          <div
            className={`px-2 py-1 rounded text-xs font-medium ${
              confidence === 'High'
                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
            }`}
          >
            {confidence} Confidence
          </div>

          {/* Copy Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCopy}
            className="p-2 rounded-lg hover:bg-muted transition-colors"
            aria-label="Copy answer"
          >
            {copied ? (
              <CheckCircle2 className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4 text-muted-foreground" />
            )}
          </motion.button>
        </div>
      </div>

      <div className="prose dark:prose-invert max-w-none">
        <p className="text-foreground leading-relaxed whitespace-pre-wrap">{answer}</p>
      </div>
    </motion.div>
  );
}
