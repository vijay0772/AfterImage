import { useRef, useState } from 'react';
import { motion } from 'motion/react';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import { useStore } from '../lib/store';
import { uploadDocument } from '../lib/api';
import { toast } from '../lib/toast';

export function UploadCard() {
  const { filename, pageCount, uploadStatus, setUploadStatus, setDocument, reset } = useStore();
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.type.includes('pdf')) {
      toast.error('Please upload a PDF file');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      toast.error('File size must be less than 50MB');
      return;
    }

    setUploadStatus('uploading');

    try {
      const { response, pdfUrl } = await uploadDocument(file);
      setDocument(response.doc_id, response.filename, response.page_count, pdfUrl);
      toast.success('PDF uploaded successfully');
    } catch (error) {
      setUploadStatus('error', 'Upload failed. Please try again.');
      toast.error('Upload failed');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleReplace = () => {
    reset();
    fileInputRef.current?.click();
  };

  if (uploadStatus === 'success' && filename) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 rounded-xl bg-card dark:bg-gradient-to-br dark:from-white/5 dark:to-white/[0.02] border-2 border-[hsl(var(--border))] dark:border-white/10 shadow-sm dark:shadow-none backdrop-blur-sm"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
              <File className="w-5 h-5 text-[hsl(var(--primary))]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-foreground truncate">{filename}</p>
              <p className="text-sm text-muted-foreground mt-1">{pageCount} pages</p>
            </div>
          </div>
          <button
            onClick={handleReplace}
            className="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
            aria-label="Replace PDF"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 rounded-xl bg-card dark:bg-gradient-to-br dark:from-white/5 dark:to-white/[0.02] border-2 border-[hsl(var(--border))] dark:border-white/10 shadow-sm dark:shadow-none backdrop-blur-sm"
    >
      <div
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        className={`
          relative border-2 border-dashed rounded-lg p-8 transition-all cursor-pointer
          ${
            isDragging
              ? 'border-[hsl(var(--primary))] bg-primary/5'
              : 'border-[hsl(var(--primary))]/40 hover:border-[hsl(var(--primary))]/70 hover:bg-muted/50'
          }
          ${uploadStatus === 'uploading' ? 'pointer-events-none opacity-50' : ''}
        `}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-4 text-center">
          <motion.div
            animate={uploadStatus === 'uploading' ? { rotate: 360 } : {}}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="p-4 rounded-full bg-primary/10 border border-primary/20"
          >
            <Upload className="w-8 h-8 text-[hsl(var(--primary))]" />
          </motion.div>

          {uploadStatus === 'uploading' ? (
            <div>
              <p className="font-medium text-foreground">Uploading PDF...</p>
              <p className="text-sm text-muted-foreground mt-1">Please wait</p>
            </div>
          ) : (
            <div>
              <p className="font-medium text-foreground">
                {isDragging ? 'Drop PDF here' : 'Upload PDF'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Drag and drop or click to browse
              </p>
            </div>
          )}
        </div>

        {uploadStatus === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-2 text-red-400 text-sm justify-center"
          >
            <AlertCircle className="w-4 h-4" />
            <span>Upload failed. Please try again.</span>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
