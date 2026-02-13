import { motion } from 'motion/react';
import { Send, Sparkles } from 'lucide-react';
import { useStore } from '../lib/store';
import { askQuestion } from '../lib/api';
import { toast } from '../lib/toast';

const EXAMPLE_QUESTIONS = [
  "Who signed the discharge for the patient from the post-anaesthesia care unit on April 6?",
  "What medications does the patient take for sleep?",
  "When was the patient discharged?",
];

export function QuestionCard() {
  const {
    docId,
    question,
    askStatus,
    setQuestion,
    setAskStatus,
    setAnswer,
    addToHistory,
  } = useStore();

  const handleAsk = async () => {
    if (!docId) {
      toast.error('Please upload a PDF first');
      return;
    }

    if (!question.trim()) {
      toast.error('Please enter a question');
      return;
    }

    setAskStatus('loading');

    try {
      const response = await askQuestion(docId, question);
      setAnswer(response.answer, response.evidence, response.highlights);
      addToHistory(question, response.answer);
      toast.success('Answer generated');
    } catch (error) {
      setAskStatus('error', 'Failed to get answer. Please try again.');
      toast.error('Failed to get answer');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleAsk();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="p-6 rounded-xl bg-card dark:bg-gradient-to-br dark:from-white/5 dark:to-white/[0.02] border-2 border-[hsl(var(--border))] dark:border-white/10 shadow-sm dark:shadow-none backdrop-blur-sm"
    >
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-[hsl(var(--primary))]" />
        <h2 className="font-semibold text-foreground">Ask a Question</h2>
      </div>

      {/* Example Questions */}
      {!question && (
        <div className="flex flex-wrap gap-2 mb-4">
          {EXAMPLE_QUESTIONS.map((example, i) => (
            <motion.button
              key={i}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setQuestion(example)}
              className="px-3 py-1.5 text-sm rounded-lg bg-[hsl(var(--secondary))] dark:bg-muted hover:bg-[hsl(var(--muted))] dark:hover:bg-muted/80 border-2 border-[hsl(var(--primary))]/50 dark:border-border transition-colors text-muted-foreground hover:text-foreground hover:border-[hsl(var(--primary))]/70 dark:hover:border-white/20"
            >
              {example}
            </motion.button>
          ))}
        </div>
      )}

      {/* Question Input */}
      <div className="relative">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question here..."
          rows={3}
          disabled={askStatus === 'loading'}
          className="w-full px-4 py-3 bg-[hsl(var(--secondary))] dark:bg-black/20 border-2 border-[hsl(var(--primary))]/50 dark:border-white/10 rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-[hsl(var(--primary))]/50 focus:border-[hsl(var(--primary))] resize-none transition-all disabled:opacity-50"
        />

        {/* Character count */}
        <div className="absolute bottom-3 right-3 text-xs text-muted-foreground">
          {question.length} / 500
        </div>
      </div>

      {/* Ask Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleAsk}
        disabled={askStatus === 'loading' || !question.trim()}
        className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[hsl(var(--primary))] hover:opacity-90 dark:bg-gradient-to-r dark:from-blue-600 dark:to-purple-600 dark:hover:from-blue-500 dark:hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium text-primary-foreground"
      >
        {askStatus === 'loading' ? (
          <>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              <Sparkles className="w-5 h-5" />
            </motion.div>
            <span>Analyzing...</span>
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            <span>Ask</span>
          </>
        )}
      </motion.button>

      <p className="text-xs text-muted-foreground text-center mt-3">
        Press <kbd className="px-1.5 py-0.5 rounded bg-muted">⌘</kbd> +{' '}
        <kbd className="px-1.5 py-0.5 rounded bg-muted">Enter</kbd> to ask
      </p>
    </motion.div>
  );
}
