import { useEffect, Suspense } from 'react';
import { ErrorBoundary } from './src/components/ErrorBoundary';
import { TopBar } from './src/components/TopBar';
import { UploadCard } from './src/components/UploadCard';
import { QuestionCard } from './src/components/QuestionCard';
import { AnswerPanel } from './src/components/AnswerPanel';
import { EvidenceList } from './src/components/EvidenceList';
import { HistoryPanel } from './src/components/HistoryPanel';
import { PdfToolbar } from './src/components/PdfToolbar';
import { PdfViewer } from './src/components/PdfViewer';
import { ToastContainer } from './src/components/Toast';
import { useStore } from './src/lib/store';
import { toast } from './src/lib/toast';

function AppContent() {
  const { setZoom, theme } = useStore();

  // Sync theme to document for Tailwind dark mode
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K: Focus question input
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const input = document.querySelector('textarea') as HTMLTextAreaElement;
        input?.focus();
      }

      // Escape: Clear highlights
      if (e.key === 'Escape') {
        useStore.getState().setSelectedEvidence(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleFitWidth = () => {
    setZoom(1.0);
    toast.info('Fit to width');
  };

  return (
    <div className={`h-screen flex flex-col ${theme === 'dark' ? 'bg-[hsl(var(--background))]' : 'bg-daylight-main'}`}>
      <TopBar />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Assistant */}
        <div className={`w-[450px] flex-shrink-0 border-r overflow-y-auto ${theme === 'dark' ? 'border-border bg-muted/30 backdrop-blur-sm' : 'border-[hsl(var(--border))] bg-daylight-sidebar shadow-[2px_0_8px_rgba(0,0,0,0.06)]'}`}>
          <div className="p-6 space-y-6">
            <UploadCard />
            <QuestionCard />
            <AnswerPanel />
            <EvidenceList />
            <HistoryPanel />
          </div>
        </div>

        {/* Right Panel - PDF Viewer */}
        <div className="flex-1 flex flex-col">
          <PdfToolbar onFitWidth={handleFitWidth} />
          <div className="flex-1 overflow-hidden">
            <Suspense fallback={
              <div className={`h-full flex items-center justify-center ${theme === 'dark' ? 'bg-muted/30' : 'bg-daylight-main'}`}>
                <p className="text-muted-foreground">Loading PDF viewer...</p>
              </div>
            }>
              <PdfViewer />
            </Suspense>
          </div>
        </div>
      </div>

      <ToastContainer />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
