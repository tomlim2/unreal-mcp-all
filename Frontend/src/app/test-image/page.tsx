'use client';

import { useState } from 'react';

export default function TestImagePage() {
  const [imageStatus, setImageStatus] = useState('loading');
  const [errorDetails, setErrorDetails] = useState<any>(null);
  
  const imageUrl = '/api/screenshot/155e75cd-aaf2-4154-bce2-37f2399e65ac';
  
  return (
    <div style={{ padding: '20px', backgroundColor: '#1a1a1a', color: 'white', minHeight: '100vh' }}>
      <h1>Image Loading Test</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Status: {imageStatus}</h3>
        <p>Image URL: {imageUrl}</p>
        {errorDetails && (
          <div>
            <h4>Error Details:</h4>
            <pre style={{ background: '#333', padding: '10px', fontSize: '12px' }}>
              {JSON.stringify(errorDetails, null, 2)}
            </pre>
          </div>
        )}
      </div>
      
      <div style={{ border: '2px solid red', padding: '10px', display: 'inline-block' }}>
        <img 
          src={imageUrl}
          alt="Test Screenshot"
          style={{ maxWidth: '400px', display: 'block' }}
          onLoad={() => {
            console.log('✅ Image loaded successfully');
            setImageStatus('loaded');
          }}
          onError={(e) => {
            console.error('❌ Image failed to load');
            console.error('Error event:', e);
            setImageStatus('failed');
            setErrorDetails({
              type: e.type,
              target: e.target ? {
                src: (e.target as HTMLImageElement).src,
                complete: (e.target as HTMLImageElement).complete,
                naturalWidth: (e.target as HTMLImageElement).naturalWidth,
                naturalHeight: (e.target as HTMLImageElement).naturalHeight,
              } : null,
              timestamp: new Date().toISOString()
            });
          }}
        />
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <button 
          onClick={() => {
            setImageStatus('loading');
            setErrorDetails(null);
            // Force reload by adding timestamp
            const img = document.querySelector('img') as HTMLImageElement;
            if (img) {
              img.src = imageUrl + '?t=' + Date.now();
            }
          }}
          style={{ padding: '10px 20px', backgroundColor: '#333', color: 'white', border: '1px solid #666' }}
        >
          Reload Image
        </button>
        
        <button 
          onClick={() => {
            // Test the API endpoint directly
            fetch(imageUrl)
              .then(res => {
                console.log('API Response Status:', res.status);
                console.log('API Response Headers:', Object.fromEntries(res.headers));
                return res.blob();
              })
              .then(blob => {
                console.log('API Response Blob:', blob);
                setImageStatus('api-tested: ' + blob.type + ', ' + blob.size + ' bytes');
              })
              .catch(err => {
                console.error('API Test Error:', err);
                setImageStatus('api-failed: ' + err.message);
              });
          }}
          style={{ padding: '10px 20px', backgroundColor: '#333', color: 'white', border: '1px solid #666', marginLeft: '10px' }}
        >
          Test API Directly
        </button>
      </div>
    </div>
  );
}