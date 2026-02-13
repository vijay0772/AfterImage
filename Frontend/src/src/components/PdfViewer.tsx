import { useEffect, useRef, useState } from 'react';
import { Document, Page, pdfjs, usePageContext } from 'react-pdf';
import { motion } from 'motion/react';
import { useStore } from '../lib/store';
import { pdfToScreenCoords } from '../lib/pdfCoords';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set up the worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export function PdfViewer() {
  const {
    pdfUrl,
    currentPage,
    zoom,
    rotation,
    highlights,
    selectedEvidenceIndex,
    evidence,
    pageCount: storedPageCount,
    setCurrentPage,
  } = useStore();

  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageWidth, setPageWidth] = useState<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setPageWidth(containerRef.current.clientWidth - 48); // Subtract padding
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Scroll to current page when it changes
  useEffect(() => {
    const pageElement = pageRefs.current.get(currentPage);
    if (pageElement) {
      pageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [currentPage]);

  // Pulse effect when evidence is selected
  useEffect(() => {
    if (selectedEvidenceIndex !== null && evidence[selectedEvidenceIndex]) {
      const page = evidence[selectedEvidenceIndex].page;
      setCurrentPage(page);
    }
  }, [selectedEvidenceIndex, evidence, setCurrentPage]);

  if (!pdfUrl) {
    return (
      <div className="h-full flex items-center justify-center bg-[hsl(var(--pdf-area-bg))] dark:bg-black/10 backdrop-blur-sm">
        <div className="text-center">
          <p className="text-muted-foreground">No document loaded</p>
          <p className="text-sm text-muted-foreground/80 mt-1">Upload a PDF to get started</p>
        </div>
      </div>
    );
  }

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  return (
    <div ref={containerRef} className="h-full overflow-y-auto bg-[hsl(var(--pdf-area-bg))] dark:bg-black/10 backdrop-blur-sm p-6">
      <Document
        file={pdfUrl}
        onLoadSuccess={onDocumentLoadSuccess}
        loading={
          <div className="flex flex-col items-center justify-center py-20">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full"
            />
            <p className="mt-4 text-muted-foreground">Loading PDF...</p>
          </div>
        }
        error={
          <div className="flex items-center justify-center py-20">
            <p className="text-red-400">Failed to load PDF</p>
          </div>
        }
        className="flex flex-col items-center gap-6"
      >
        {numPages &&
          Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => (
            <div
              key={pageNum}
              ref={(el) => {
                if (el) pageRefs.current.set(pageNum, el);
              }}
              className="relative"
            >
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: pageNum * 0.05 }}
                className={`
                  relative inline-block shadow-2xl rounded-lg overflow-hidden
                  ${
                    pageNum === currentPage
                      ? 'ring-2 ring-blue-500/50 shadow-blue-500/20'
                      : ''
                  }
                `}
              >
                <Page
                  pageNumber={pageNum}
                  width={pageWidth * zoom}
                  rotate={rotation}
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  className="bg-white"
                >
                  {/* Highlight Overlay - as child of Page so it renders on top of canvas/text/annotations */}
                  {(() => {
                    const pageHighlights = highlights.filter((h) => h.page === pageNum);
                    return pageHighlights.length > 0 ? (
                      <HighlightOverlay
                        highlights={pageHighlights}
                        pageWidth={pageWidth * zoom}
                        isPulse={pageNum === currentPage && selectedEvidenceIndex !== null}
                      />
                    ) : null;
                  })()}
                </Page>

                {/* Page Number Badge */}
                <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/50 backdrop-blur text-white text-sm font-medium">
                  Page {pageNum}
                </div>
              </motion.div>
            </div>
          ))}
      </Document>
    </div>
  );
}

interface HighlightOverlayProps {
  highlights: Array<{ page: number; rects: [number, number, number, number][] }>;
  pageWidth: number;
  isPulse: boolean;
}

function HighlightOverlay({ highlights, pageWidth, isPulse }: HighlightOverlayProps) {
  // Use exact scale from react-pdf's page context (matches canvas/text layer)
  const pageContext = usePageContext();
  const scale = pageContext?.scale ?? pageWidth / 612;

  return (
    <div
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: 100 }}
    >
      {highlights.map((highlight, i) =>
        highlight.rects.map((rect, j) => {
          const screenRect = pdfToScreenCoords(rect, 792, scale);

          const w = Math.max(screenRect.width, 2);
          const h = Math.max(screenRect.height, 2);

          return (
            <div
              key={`${i}-${j}`}
              className="absolute rounded-sm"
              style={{
                left: screenRect.x,
                top: screenRect.y,
                width: w,
                height: h,
                backgroundColor: 'rgba(239, 68, 68, 0.75)',
                border: '2px solid rgb(185, 28, 28)',
                boxSizing: 'border-box',
                zIndex: 101,
              }}
            />
          );
        })
      )}
    </div>
  );
}
