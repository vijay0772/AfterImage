const BASE_URL = import.meta.env?.VITE_API_BASE_URL || '';
const IS_MOCK = !BASE_URL;

// Mock data
const MOCK_ANSWER = {
  answer: "According to the document, the company's revenue grew by 45% year-over-year, reaching $12.3 million in Q4 2023. This growth was primarily driven by increased adoption of the enterprise tier and expansion into the European market.",
  evidence: [
    { page: 1, line_id: "p1_b0_l1", text: "Revenue increased 45% YoY to $12.3M in Q4 2023" },
    { page: 2, line_id: "p2_b0_l1", text: "Enterprise tier adoption drove 60% of new revenue" },
    { page: 3, line_id: "p3_b0_l1", text: "European market expansion contributed $4.2M in new ARR" },
  ],
  // rects in [x0,y0,x1,y1] top-left origin (matching PyMuPDF/pdfplumber)
  highlights: [
    { page: 1, rects: [[72, 122, 400, 140]] },
    { page: 2, rects: [[72, 122, 420, 140]] },
    { page: 3, rects: [[72, 122, 400, 140]] },
  ],
};

// Generate a sample PDF blob for mock mode
function generateMockPDF(): Blob {
  // This is a minimal valid PDF structure
  const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R 4 0 R 5 0 R]
/Count 3
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 6 0 R
>>
endobj
4 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 7 0 R
>>
endobj
5 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 8 0 R
>>
endobj
6 0 obj
<<
/Length 165
>>
stream
BT
/F1 24 Tf
72 720 Td
(Sample PDF Document - Page 1) Tj
0 -50 Td
/F1 12 Tf
(Revenue increased 45% YoY to $12.3M in Q4 2023) Tj
0 -30 Td
(This is mock evidence for demonstration.) Tj
ET
endstream
endobj
7 0 obj
<<
/Length 150
>>
stream
BT
/F1 24 Tf
72 720 Td
(Sample PDF Document - Page 2) Tj
0 -50 Td
/F1 12 Tf
(Enterprise tier adoption drove 60% of new revenue) Tj
0 -30 Td
(More mock content here.) Tj
ET
endstream
endobj
8 0 obj
<<
/Length 155
>>
stream
BT
/F 24 Tf
72 720 Td
(Sample PDF Document - Page 3) Tj
0 -50 Td
/F1 12 Tf
(European market expansion contributed $4.2M in new ARR) Tj
0 -30 Td
(Final page content.) Tj
ET
endstream
endobj
xref
0 9
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000125 00000 n 
0000000324 00000 n 
0000000523 00000 n 
0000000722 00000 n 
0000000937 00000 n 
0000001137 00000 n 
trailer
<<
/Size 9
/Root 1 0 R
>>
startxref
1342
%%EOF`;

  return new Blob([pdfContent], { type: 'application/pdf' });
}

export interface UploadResponse {
  doc_id: string;
  filename: string;
  page_count: number;
}

export interface AskResponse {
  answer: string;
  evidence: Array<{ page: number; line_id: string; text: string }>;
  highlights: Array<{ page: number; rects: [number, number, number, number][] }>;
}

async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function uploadDocument(
  file: File,
  options?: { force?: boolean }
): Promise<{ response: UploadResponse; pdfUrl: string }> {
  if (IS_MOCK) {
    await delay(1000); // Simulate upload time
    const mockPdf = generateMockPDF();
    return {
      response: {
        doc_id: 'mock-doc-' + Date.now(),
        filename: file.name,
        page_count: 3,
      },
      pdfUrl: URL.createObjectURL(mockPdf),
    };
  }

  const formData = new FormData();
  formData.append('file', file);

  const uploadUrl = options?.force ? `${BASE_URL}/documents?force=true` : `${BASE_URL}/documents`;
  const response = await fetch(uploadUrl, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(err || 'Upload failed');
  }

  const data: UploadResponse = await response.json();
  const pdfUrl = `${BASE_URL}/documents/${data.doc_id}/file`;

  return { response: data, pdfUrl };
}

export async function downloadHighlightedPdf(
  docId: string,
  highlights: Array<{ page: number; rects: [number, number, number, number][] }>
): Promise<Blob> {
  const response = await fetch(`${BASE_URL}/documents/${docId}/export-highlighted`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ highlights }),
  });
  if (!response.ok) throw new Error('Failed to export highlighted PDF');
  return response.blob();
}

export async function askQuestion(docId: string, question: string): Promise<AskResponse> {
  if (IS_MOCK) {
    await delay(1500); // Simulate processing time
    return MOCK_ANSWER;
  }

  const response = await fetch(`${BASE_URL}/documents/${docId}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(err || 'Failed to get answer');
  }

  return response.json();
}

export { IS_MOCK };