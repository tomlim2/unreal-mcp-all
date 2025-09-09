import { NextRequest, NextResponse } from 'next/server';

// Python MCP HTTP Bridge URL
const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

export async function GET(request: NextRequest) {
  try {
    // Forward request to Python MCP server to get API key status
    const response = await fetch(`${MCP_HTTP_BRIDGE_URL}/api/keys/status`, {
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
    
    // Return the API key status from Python MCP server
    return NextResponse.json(result);

  } catch (error) {
    console.error('API key status API error:', error);
    
    // Return safe defaults if Python server is unavailable
    return NextResponse.json({
      google_available: false,
      anthropic_available: false,
      error: `Python MCP server unavailable: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }, { status: 500 });
  }
}