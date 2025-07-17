'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function ResultsPageContent() {
  // This hook lets you read query parameters from the URL
  const params = useSearchParams(); // browser only react hook 

  // Get the 'img' parameter from the URL, e.g., /results?img=/static/output_with_boxes_123456.jpg
  const imgUrl = params.get('img');

  return (
    <div style={{ textAlign: 'center', padding: '2rem' }}>
      <h1>Processed Image with Bounding Boxes</h1>
      {/* If imgUrl exists, show the image. Otherwise, show a message. */}
      {imgUrl ? (
        <img
          src={`http://localhost:5000${imgUrl}`}
          alt="Processed with bounding boxes"
          style={{ maxWidth: '90%', border: '2px solid #333', marginTop: '2rem' }}
        />
      ) : (
        <p>No image to display. Please upload a file first.</p>
      )}
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResultsPageContent />
    </Suspense>
  );
} 