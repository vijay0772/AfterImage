/**
 * PDF coordinate mapping utilities
 *
 * Backend returns rects as [x0, y0, x1, y1] in PDF points.
 * PyMuPDF uses top-left origin; PDF standard uses bottom-left.
 * We support both - try Y-flip if highlights appear inverted.
 */

export interface ScreenRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Convert backend rect [x0, y0, x1, y1] to screen coordinates
 * @param rect - [x0, y0, x1, y1] in PDF points
 * @param pageHeightPdf - PDF page height in points (792 for letter)
 * @param scale - pixels per PDF point (pageWidth / 612)
 * @returns Screen coordinates in pixels (top-left origin)
 */
export function pdfToScreenCoords(
  rect: [number, number, number, number],
  _pageHeightPdf: number,
  scale: number
): ScreenRect {
  const [x0, y0, x1, y1] = rect;
  const width = Math.abs(x1 - x0) * scale;
  const height = Math.abs(y1 - y0) * scale;
  // Backend (PyMuPDF + pdfplumber) uses top-left origin, y increases downward
  const x = Math.min(x0, x1) * scale;
  const y = Math.min(y0, y1) * scale;

  return { x, y, width, height };
}

/**
 * Legacy: Convert [x, y, width, height] format (for mock data)
 */
export function pdfRectToScreen(
  pdfRect: [number, number, number, number],
  pageHeight: number,
  scale: number
): ScreenRect {
  // Assume backend format [x0, y0, x1, y1]
  if (pdfRect[2] > pdfRect[0] && pdfRect[3] > pdfRect[1]) {
    return pdfToScreenCoords(pdfRect as [number, number, number, number], pageHeight, scale);
  }
  // Fallback: [x, y, width, height]
  return {
    x: pdfRect[0] * scale,
    y: (pageHeight - pdfRect[1] - pdfRect[3]) * scale,
    width: pdfRect[2] * scale,
    height: pdfRect[3] * scale,
  };
}

/**
 * Calculate the overall bounding box for multiple rects
 */
export function calculateBoundingBox(rects: ScreenRect[]): ScreenRect | null {
  if (rects.length === 0) return null;

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  for (const rect of rects) {
    minX = Math.min(minX, rect.x);
    minY = Math.min(minY, rect.y);
    maxX = Math.max(maxX, rect.x + rect.width);
    maxY = Math.max(maxY, rect.y + rect.height);
  }

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  };
}
