import { motion } from 'motion/react';
import { Sparkles, RefreshCw, Moon, Sun } from 'lucide-react';
import { useStore } from '../lib/store';

export function TopBar() {
  const { isMockMode, theme, toggleTheme, reset } = useStore();

  return (
    <div className={`h-16 border-b flex items-center justify-between px-6 ${theme === 'dark' ? 'border-border bg-muted/50 backdrop-blur-xl' : 'border-[hsl(var(--border))] bg-[hsl(var(--sidebar-bg))] shadow-sm'}`}>
      <div className="flex items-center gap-3">
        <Sparkles className={`w-6 h-6 ${theme === 'dark' ? 'text-blue-400' : 'text-[hsl(var(--primary))]'}`} />
        <h1 className={`text-xl font-semibold ${theme === 'dark' ? 'bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent' : 'text-[hsl(var(--primary))]'}`}>
          Afterimage
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {/* Status Indicator */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${theme === 'dark' ? 'bg-muted border border-border' : 'bg-[hsl(var(--secondary))] border-2 border-[hsl(var(--border))]'}`}>
          <div
            className={`w-2 h-2 rounded-full ${
              isMockMode ? 'bg-yellow-400' : 'bg-green-400'
            } animate-pulse`}
          />
          <span className="text-sm text-muted-foreground">
            {isMockMode ? 'Mock Mode' : 'Connected'}
          </span>
        </div>

        {/* Theme Toggle */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-muted transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <Sun className="w-5 h-5 text-muted-foreground" />
          ) : (
            <Moon className="w-5 h-5 text-muted-foreground" />
          )}
        </motion.button>

        {/* Reset Button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={reset}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${theme === 'dark' ? 'bg-muted hover:bg-muted/80 border border-border' : 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--muted))] border-2 border-[hsl(var(--border))]'}`}
        >
          <RefreshCw className="w-4 h-4" />
          <span className="text-sm">Reset</span>
        </motion.button>
      </div>
    </div>
  );
}
