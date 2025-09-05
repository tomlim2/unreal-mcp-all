import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const jobId = url.searchParams.get('jobId') || '155e75cd-aaf2-4154-bce2-37f2399e65ac';
    
    // Test the screenshot endpoint
    const screenshotUrl = `http://localhost:3000/api/screenshot/${jobId}`;
    
    console.log(`Testing screenshot URL: ${screenshotUrl}`);
    
    const response = await fetch(screenshotUrl);
    
    const responseInfo = {
      url: screenshotUrl,
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      contentType: response.headers.get('content-type'),
      contentLength: response.headers.get('content-length'),
    };
    
    console.log('Screenshot response info:', responseInfo);
    
    return NextResponse.json({
      message: 'Screenshot endpoint debug info',
      ...responseInfo,
      isImage: response.headers.get('content-type')?.startsWith('image/'),
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Debug error:', error);
    return NextResponse.json({
      error: `Debug failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      timestamp: new Date().toISOString()
    }, { status: 500 });
  }
}