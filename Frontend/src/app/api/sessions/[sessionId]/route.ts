import { NextRequest, NextResponse } from 'next/server';

// Python MCP HTTP Bridge URL
const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  try {
    const { sessionId } = await params;
    
    if (!sessionId) {
      return NextResponse.json({
        success: false,
        error: 'Session ID is required'
      }, { status: 400 });
    }
    
    // Forward delete request to Python MCP server
    const response = await fetch(`${MCP_HTTP_BRIDGE_URL}`, {
      method: 'DELETE',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        action: 'delete_session'
      }),
    });

    if (!response.ok) {
      throw new Error(`Python MCP server error: ${response.status}`);
    }

    const result = await response.json();
    
    // Return the session deletion result from Python MCP server
    return NextResponse.json(result);

  } catch (error) {
    console.error('Session deletion API error:', error);
    
    // Return error if Python server is unavailable
    return NextResponse.json({
      success: false,
      error: `Python MCP server unavailable: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }, { status: 500 });
  }
}