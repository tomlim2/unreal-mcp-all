import { NextRequest, NextResponse } from 'next/server';

const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const { filename } = await params;
    
    console.log(`Screenshot API called for filename: ${filename}`);
    
    if (!filename) {
      return NextResponse.json({ error: 'Filename is required' }, { status: 400 });
    }

    // Validate filename is a PNG
    if (!filename.endsWith('.png')) {
      return NextResponse.json({ error: 'Only PNG files are supported' }, { status: 400 });
    }

    // Fetch the image from the Python HTTP bridge
    const response = await fetch(`${MCP_HTTP_BRIDGE_URL}/api/screenshot-file/${filename}`, {
      method: 'GET',
      headers: {
        'Accept': 'image/png',
      },
    });

    if (response.ok) {
      const imageBuffer = await response.arrayBuffer();
      
      return new NextResponse(imageBuffer, {
        status: 200,
        headers: {
          'Content-Type': 'image/png',
          'Cache-Control': 'public, max-age=3600',
          'Access-Control-Allow-Origin': '*',
        },
      });
    } else {
      console.error(`Failed to fetch screenshot: ${response.status} ${response.statusText}`);
      return NextResponse.json({ 
        error: `Screenshot not found: ${filename}` 
      }, { status: 404 });
    }

  } catch (error) {
    console.error('Screenshot proxy error:', error);
    
    return NextResponse.json({
      error: `Screenshot proxy failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }, { status: 500 });
  }
}