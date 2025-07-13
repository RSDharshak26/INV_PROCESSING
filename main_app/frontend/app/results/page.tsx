'use client';

import { useSearchParams } from 'next/navigation';//Pulls in the Next.js hook for reading query parameters.

//render when results page ( filename ) is accessed 
export default function ResultsPage() {
  // This hook lets you read query parameters from the URL
  const params = useSearchParams(); // browser only react hook 

  // Get the 'img' and 'text' parameters from the URL
  const imgUrl = params.get('img');
  const extractedText = params.get('text');

  // Getting the desired 

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>Invoice Processing Results</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Left side - Processed Image */}
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Processed Image with Bounding Boxes</h2>
          {imgUrl ? (
            <img
              src={`http://localhost:5000${imgUrl}`}
              alt="Processed with bounding boxes"
              style={{ 
                maxWidth: '100%', 
                border: '2px solid #333', 
                borderRadius: '8px',
                boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
              }}
            />
          ) : (
            <p>No image to display. Please upload a file first.</p>
          )}
        </div>

        {/* Right side - Extracted Text */}
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Extracted Text</h2>
          {extractedText ? (
            <div style={{
              border: '2px solid #333',
              borderRadius: '8px',
              padding: '1rem',
              backgroundColor: '#f9f9f9',
              maxHeight: '500px',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              fontSize: '14px',
              lineHeight: '1.5'
            }}>
              {extractedText}
            </div>
          ) : (
            <p>No text extracted. Please try uploading a different file.</p>
          )}
        </div>
      </div>
    </div>
  );
} 