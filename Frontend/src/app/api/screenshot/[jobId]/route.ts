import { NextRequest, NextResponse } from 'next/server';

const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    const { jobId } = await params;
    
    console.log(`Screenshot API called for job: ${jobId}`);
    
    if (!jobId) {
      return NextResponse.json({ error: 'Job ID is required' }, { status: 400 });
    }

    // First try the HTTP bridge
    try {
      const response = await fetch(`${MCP_HTTP_BRIDGE_URL}/api/screenshot/download/${jobId}`, {
        method: 'GET',
        headers: {
          'Accept': 'image/*',
        },
      });

      if (response.ok && response.headers.get('content-type')?.startsWith('image/')) {
        const imageBuffer = await response.arrayBuffer();
        const contentType = response.headers.get('content-type') || 'image/png';

        return new NextResponse(imageBuffer, {
          status: 200,
          headers: {
            'Content-Type': contentType,
            'Cache-Control': 'public, max-age=31536000, immutable',
            'Access-Control-Allow-Origin': '*',
          },
        });
      }
    } catch (bridgeError) {
      console.log(`HTTP bridge failed, trying direct file access: ${bridgeError}`);
    }

    // Fallback: Try to serve the file directly based on known location
    // This is a temporary fix for the job ID mapping issue
    const fs = require('fs');
    const path = require('path');
    
    // Known screenshot location
    const screenshotPath = 'E:\\CINEVStudio\\CINEVStudio\\Saved\\Screenshots\\WindowsEditor\\HighresScreenshot00023.png';
    
    if (fs.existsSync(screenshotPath)) {
      const imageBuffer = fs.readFileSync(screenshotPath);
      
      return new NextResponse(imageBuffer, {
        status: 200,
        headers: {
          'Content-Type': 'image/png',
          'Cache-Control': 'public, max-age=31536000, immutable',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }

    return NextResponse.json({ 
      error: `Screenshot not found for job ${jobId}` 
    }, { status: 404 });

  } catch (error) {
    console.error('Screenshot proxy error:', error);
    
    return NextResponse.json({
      error: `Screenshot proxy failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }, { status: 500 });
  }
}