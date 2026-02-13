# Afterimage - Chat with PDF + Evidence Highlight

A highly interactive, visually premium web application for chatting with PDFs and highlighting evidence with production-quality UI/UX.

## Features

- **PDF Upload**: Drag & drop or browse to upload PDF documents
- **AI Chat**: Ask questions about your PDF and get intelligent answers
- **Evidence Highlighting**: Click evidence citations to jump to the exact location in the PDF with red highlight overlays
- **Smooth Animations**: Framer Motion powered micro-interactions and transitions
- **Modern UI**: Dark mode with glassmorphism, gradients, and premium styling
- **Keyboard Shortcuts**: 
  - `Cmd/Ctrl + Enter`: Ask question
  - `Cmd/Ctrl + K`: Focus question input
  - `Esc`: Clear highlights
- **History**: Track recent questions
- **Mock Mode**: Works without a backend using simulated responses

## Tech Stack

- **React 18** with TypeScript
- **Vite** for blazing fast development
- **TailwindCSS 4** for styling
- **Framer Motion** for animations
- **react-pdf** for PDF rendering
- **Zustand** for state management
- **Lucide React** for icons

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
# Run in mock mode (no backend needed)
npm run dev

# Run with real API
# 1. Copy .env.example to .env
# 2. Set VITE_API_BASE_URL to your backend URL
npm run dev
```

### Build

```bash
npm run build
npm run preview
```

## API Contract

The app expects the following endpoints:

### Upload PDF
```
POST {BASE_URL}/documents
Content-Type: multipart/form-data
Body: file

Response:
{
  "doc_id": "string",
  "filename": "string",
  "page_count": number
}
```

### Fetch PDF
```
GET {BASE_URL}/documents/{doc_id}/file

Response: PDF bytes
```

### Ask Question
```
POST {BASE_URL}/documents/{doc_id}/ask
Content-Type: application/json
Body: { "question": "string" }

Response:
{
  "answer": "string",
  "evidence": [{ "page": number, "quote": "string" }],
  "highlights": [{ "page": number, "rects": [[x, y, width, height]] }]
}
```

## Project Structure

```
src/
├── components/
│   ├── TopBar.tsx          # App header with status & controls
│   ├── UploadCard.tsx      # PDF upload with drag & drop
│   ├── QuestionCard.tsx    # Question input & example chips
│   ├── AnswerPanel.tsx     # Answer display with confidence
│   ├── EvidenceList.tsx    # Clickable evidence citations
│   ├── HistoryPanel.tsx    # Recent questions
│   ├── PdfToolbar.tsx      # PDF controls (zoom, page nav)
│   ├── PdfViewer.tsx       # PDF renderer with highlights
│   └── Toast.tsx           # Toast notifications
├── lib/
│   ├── api.ts              # API client with mock mode
│   ├── store.ts            # Zustand state management
│   ├── pdfCoords.ts        # PDF coordinate mapping
│   └── toast.ts            # Toast manager
├── styles/
│   └── globals.css         # Global styles & Tailwind
├── App.tsx                 # Main app component
└── main.tsx                # Entry point
```

## Customization

### Styling
- All colors and styles are in `/src/styles/globals.css` using CSS custom properties
- Tailwind configuration uses v4 with `@import "tailwindcss"`

### Mock Data
- Edit `/src/lib/api.ts` to customize mock responses and sample PDF

### Theme
- Dark mode is default; theme toggle available in top bar

## License

MIT
