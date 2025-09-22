import { NextRequest, NextResponse } from 'next/server';

const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ filename: string }> }
) {
  try {
    const { filename } = await params;

    console.log(`Video API called for filename: ${filename}`);

    if (!filename) {
      return NextResponse.json({ error: 'Filename is required' }, { status: 400 });
    }

    // Validate filename is an MP4
    if (!filename.endsWith('.mp4')) {
      return NextResponse.json({ error: 'Only MP4 files are supported' }, { status: 400 });
    }

    // Fetch the video from the Python HTTP bridge
    const response = await fetch(`${MCP_HTTP_BRIDGE_URL}/api/video-file/${filename}`, {
      method: 'GET',
      headers: {
        'Accept': 'video/mp4',
      },
    });

    if (response.ok) {
      const videoBuffer = await response.arrayBuffer();

      return new NextResponse(videoBuffer, {
        status: 200,
        headers: {
          'Content-Type': 'video/mp4',
          'Cache-Control': 'public, max-age=3600',
          'Access-Control-Allow-Origin': '*',
          'Accept-Ranges': 'bytes', // Important for video seeking
        },
      });
    } else {
      console.error(`Failed to fetch video: ${response.status} ${response.statusText}`);
      return NextResponse.json({
        error: `Video not found: ${filename}`
      }, { status: 404 });
    }

  } catch (error) {
    console.error('Video proxy error:', error);

    return NextResponse.json({
      error: `Video proxy failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }, { status: 500 });
  }
}