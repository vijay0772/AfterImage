import { create } from 'zustand';

export interface Evidence {
  page: number;
  line_id: string;
  text: string;
}

export interface Highlight {
  page: number;
  rects: [number, number, number, number][];
}

export interface Question {
  id: string;
  question: string;
  answer: string;
  timestamp: Date;
}

interface AppState {
  // Document
  docId: string | null;
  filename: string | null;
  pageCount: number;
  pdfUrl: string | null;
  uploadStatus: 'idle' | 'uploading' | 'success' | 'error';
  uploadError: string | null;

  // Question & Answer
  question: string;
  askStatus: 'idle' | 'loading' | 'success' | 'error';
  askError: string | null;
  answer: string | null;
  evidence: Evidence[];
  highlights: Highlight[];

  // Viewer
  currentPage: number;
  zoom: number;
  rotation: number;
  selectedEvidenceIndex: number | null;
  viewMode: 'continuous' | 'single';

  // History
  history: Question[];

  // Theme & Mode
  theme: 'dark' | 'light';
  isMockMode: boolean;

  // Actions
  setDocument: (docId: string, filename: string, pageCount: number, pdfUrl: string) => void;
  setUploadStatus: (status: 'idle' | 'uploading' | 'success' | 'error', error?: string) => void;
  setQuestion: (question: string) => void;
  setAskStatus: (status: 'idle' | 'loading' | 'success' | 'error', error?: string) => void;
  setAnswer: (answer: string, evidence: Evidence[], highlights: Highlight[]) => void;
  setCurrentPage: (page: number) => void;
  setZoom: (zoom: number) => void;
  setRotation: (rotation: number) => void;
  setSelectedEvidence: (index: number | null) => void;
  setViewMode: (mode: 'continuous' | 'single') => void;
  addToHistory: (question: string, answer: string) => void;
  restoreFromHistory: (id: string) => void;
  toggleTheme: () => void;
  reset: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  // Initial state
  docId: null,
  filename: null,
  pageCount: 0,
  pdfUrl: null,
  uploadStatus: 'idle',
  uploadError: null,

  question: '',
  askStatus: 'idle',
  askError: null,
  answer: null,
  evidence: [],
  highlights: [],

  currentPage: 1,
  zoom: 1.0,
  rotation: 0,
  selectedEvidenceIndex: null,
  viewMode: 'continuous',

  history: [],

  theme: 'dark',
  isMockMode: !import.meta.env?.VITE_API_BASE_URL || import.meta.env?.VITE_API_BASE_URL === '',

  // Actions
  setDocument: (docId, filename, pageCount, pdfUrl) =>
    set({ docId, filename, pageCount, pdfUrl, uploadStatus: 'success' }),

  setUploadStatus: (status, error) =>
    set({ uploadStatus: status, uploadError: error || null }),

  setQuestion: (question) => set({ question }),

  setAskStatus: (status, error) =>
    set({ askStatus: status, askError: error || null }),

  setAnswer: (answer, evidence, highlights) =>
    set({ answer, evidence, highlights, askStatus: 'success' }),

  setCurrentPage: (page) => set({ currentPage: page }),

  setZoom: (zoom) => set({ zoom }),

  setRotation: (rotation) => set({ rotation }),

  setSelectedEvidence: (index) => set({ selectedEvidenceIndex: index }),

  setViewMode: (mode) => set({ viewMode: mode }),

  addToHistory: (question, answer) =>
    set((state) => ({
      history: [
        {
          id: Date.now().toString(),
          question,
          answer,
          timestamp: new Date(),
        },
        ...state.history.slice(0, 4),
      ],
    })),

  restoreFromHistory: (id) => {
    const state = get();
    const item = state.history.find((h) => h.id === id);
    if (item) {
      set({ question: item.question, answer: item.answer });
    }
  },

  toggleTheme: () =>
    set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),

  reset: () =>
    set({
      docId: null,
      filename: null,
      pageCount: 0,
      pdfUrl: null,
      uploadStatus: 'idle',
      uploadError: null,
      question: '',
      askStatus: 'idle',
      askError: null,
      answer: null,
      evidence: [],
      highlights: [],
      currentPage: 1,
      zoom: 1.0,
      rotation: 0,
      selectedEvidenceIndex: null,
      history: [],
    }),
}));