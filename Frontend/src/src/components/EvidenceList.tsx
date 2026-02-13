import { motion, AnimatePresence } from 'motion/react';
import { FileText, ChevronRight } from 'lucide-react';
import { useStore } from '../lib/store';

export function EvidenceList() {
  const { evidence, selectedEvidenceIndex, setSelectedEvidence, setCurrentPage, highlights } =
    useStore();

  if (evidence.length === 0) {
    return null;
  }

  const handleEvidenceClick = (index: number) => {
    setSelectedEvidence(index);
    const page = evidence[index].page;
    setCurrentPage(page);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="p-6 rounded-xl bg-card dark:bg-gradient-to-br dark:from-white/5 dark:to-white/[0.02] border-2 border-[hsl(var(--border))] dark:border-white/10 shadow-sm dark:shadow-none backdrop-blur-sm"
    >
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-[hsl(var(--primary))]" />
        <h2 className="font-semibold text-foreground">Evidence</h2>
        <span className="px-2 py-0.5 rounded-full bg-primary/10 text-[hsl(var(--primary))] text-xs font-medium border border-primary/20">
          {evidence.length}
        </span>
      </div>

      <div className="space-y-2">
        <AnimatePresence>
          {evidence.map((item, index) => (
            <motion.button
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => handleEvidenceClick(index)}
              className={`
                w-full text-left p-4 rounded-lg border transition-all
                ${
                  selectedEvidenceIndex === index
                    ? 'bg-primary/10 border-primary/30 shadow-lg'
                    : 'bg-muted/50 dark:bg-white/5 border-border dark:border-white/10 hover:bg-muted dark:hover:bg-white/10 dark:hover:border-white/20'
                }
              `}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`
                  px-2 py-1 rounded text-xs font-medium mt-0.5 flex-shrink-0
                  ${
                    selectedEvidenceIndex === index
                      ? 'bg-primary/20 text-[hsl(var(--primary))] border border-primary/30'
                      : 'bg-muted text-muted-foreground border border-border dark:bg-white/10 dark:text-gray-400 dark:border-white/10'
                  }
                `}
                >
                  Page {item.page}
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm text-foreground line-clamp-2">{item.text}</p>
                </div>

                <ChevronRight
                  className={`
                    w-5 h-5 flex-shrink-0 transition-transform
                    ${
                      selectedEvidenceIndex === index
                        ? 'text-[hsl(var(--primary))] translate-x-1'
                        : 'text-muted-foreground'
                    }
                  `}
                />
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>

      {evidence.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <p className="text-sm">No evidence found</p>
        </div>
      )}
    </motion.div>
  );
}
