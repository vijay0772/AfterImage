import { useEffect } from 'react';
import { TopBar } from './components/TopBar';
import { UploadCard } from './components/UploadCard';
import { QuestionCard } from './components/QuestionCard';
import { AnswerPanel } from './components/AnswerPanel';
import { EvidenceList } from './components/EvidenceList';
import { HistoryPanel } from './components/HistoryPanel';
import { PdfToolbar } from './components/PdfToolbar';
import { PdfViewer } from './components/PdfViewer';
import { ToastContainer } from './components/Toast';
import { useStore } from './lib/store';
import { toast } from './lib/toast';

export default function App() {
  const { setZoom } = useStore();

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
    <div className="h-screen flex flex-col bg-[#0a0a0f]">
      <TopBar />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Assistant */}
        <div className="w-[450px] flex-shrink-0 border-r border-white/10 bg-black/10 backdrop-blur-sm overflow-y-auto">
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
            <PdfViewer />
          </div>
        </div>
      </div>

      <ToastContainer />
    </div>
  );
}
