import { useState } from 'react';
import { motion } from 'motion/react';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCw,
  Download,
} from 'lucide-react';
import { useStore } from '../lib/store';
import { downloadHighlightedPdf, IS_MOCK } from '../lib/api';
import { toast } from '../lib/toast';

interface PdfToolbarProps {
  onFitWidth: () => void;
}

export function PdfToolbar({ onFitWidth }: PdfToolbarProps) {
  const {
    currentPage,
    pageCount,
    zoom,
    rotation,
    setCurrentPage,
    setZoom,
    setRotation,
    pdfUrl,
    filename,
    docId,
    highlights,
  } = useStore();
  const [downloading, setDownloading] = useState(false);

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < pageCount) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handleZoomIn = () => {
    setZoom(Math.min(zoom + 0.1, 3.0));
  };

  const handleZoomOut = () => {
    setZoom(Math.max(zoom - 0.1, 0.5));
  };

  const handleRotate = () => {
    setRotation((rotation + 90) % 360);
  };

  const handleDownload = async () => {
    if (!pdfUrl || !docId) return;

    setDownloading(true);
    try {
      if (highlights.length > 0 && !IS_MOCK) {
        const blob = await downloadHighlightedPdf(docId, highlights);
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = (filename || 'document').replace(/\.pdf$/i, '_highlighted.pdf');
        link.click();
        URL.revokeObjectURL(url);
        toast.success('Downloaded PDF with highlights');
      } else {
        const link = document.createElement('a');
        link.href = pdfUrl;
        link.download = filename || 'document.pdf';
        link.click();
        toast.success(highlights.length > 0 && IS_MOCK ? 'Mock mode: downloaded original PDF' : 'Downloaded PDF');
      }
    } catch (err) {
      toast.error('Download failed');
    } finally {
      setDownloading(false);
    }
  };

  if (!pdfUrl) {
    return (
      <div className="h-14 border-b border-[hsl(var(--border))] bg-[hsl(var(--pdf-area-bg))] dark:bg-black/20 backdrop-blur-xl flex items-center justify-center px-4 text-foreground">
        <span className="text-sm text-muted-foreground">Upload a PDF to view controls</span>
      </div>
    );
  }

  return (
    <div className="h-14 border-b border-[hsl(var(--border))] bg-[hsl(var(--pdf-area-bg))] dark:bg-black/20 backdrop-blur-xl flex items-center justify-between px-4 text-foreground">
      {/* Left: Page Navigation */}
      <div className="flex items-center gap-2">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handlePrevPage}
          disabled={currentPage <= 1}
          className="p-2 rounded-lg hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Previous page"
        >
          <ChevronLeft className="w-5 h-5" />
        </motion.button>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted dark:bg-white/5 border-2 border-[hsl(var(--primary))]/40 dark:border-white/10">
          <input
            type="number"
            value={currentPage}
            onChange={(e) => {
              const page = parseInt(e.target.value);
              if (page >= 1 && page <= pageCount) {
                setCurrentPage(page);
              }
            }}
            min={1}
            max={pageCount}
            className="w-12 bg-transparent text-center focus:outline-none"
          />
          <span className="text-muted-foreground">/</span>
          <span className="text-muted-foreground">{pageCount}</span>
        </div>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleNextPage}
          disabled={currentPage >= pageCount}
          className="p-2 rounded-lg hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Next page"
        >
          <ChevronRight className="w-5 h-5" />
        </motion.button>
      </div>

      {/* Center: Zoom Controls */}
      <div className="flex items-center gap-2">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleZoomOut}
          disabled={zoom <= 0.5}
          className="p-2 rounded-lg hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Zoom out"
        >
          <ZoomOut className="w-5 h-5" />
        </motion.button>

        <div className="px-3 py-1.5 rounded-lg bg-muted dark:bg-white/5 border-2 border-[hsl(var(--primary))]/40 dark:border-white/10 min-w-[70px] text-center">
          <span className="text-sm">{Math.round(zoom * 100)}%</span>
        </div>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleZoomIn}
          disabled={zoom >= 3.0}
          className="p-2 rounded-lg hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Zoom in"
        >
          <ZoomIn className="w-5 h-5" />
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onFitWidth}
          className="p-2 rounded-lg hover:bg-muted transition-colors"
          aria-label="Fit to width"
        >
          <Maximize2 className="w-5 h-5" />
        </motion.button>
      </div>

      {/* Right: Other Controls */}
      <div className="flex items-center gap-2">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleRotate}
          className="p-2 rounded-lg hover:bg-muted transition-colors"
          aria-label="Rotate"
        >
          <RotateCw className="w-5 h-5" />
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleDownload}
          disabled={downloading}
          className="p-2 rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
          aria-label="Download"
        >
          <Download className="w-5 h-5" />
        </motion.button>
      </div>
    </div>
  );
}