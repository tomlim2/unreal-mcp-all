import { NextRequest, NextResponse } from 'next/server';

// Python MCP HTTP Bridge URL
const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

export async function GET(request: NextRequest) {
  try {
    // Forward request to Python MCP server to get session ID list
    const response = await fetch(`${MCP_HTTP_BRIDGE_URL}/session-ids`, {
      method: 'GET',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
    });

    if (!response.ok) {
      throw new Error(`Python MCP server error: ${response.status}`);
    }

    const result = await response.json();
    
    // Return the session ID list from Python MCP server
    return NextResponse.json(result);

  } catch (error) {
    console.error('Session IDs API error:', error);
    
    // Return empty list if Python server is unavailable
    return NextResponse.json({
      session_ids: [],
      error: `Python MCP server unavailable: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }, { status: 500 });
  }
}