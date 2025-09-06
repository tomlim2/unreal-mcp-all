import { NextRequest, NextResponse } from 'next/server';

// Python MCP HTTP Bridge URL
const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

export async function GET(request: NextRequest) {
  try {
    // Forward request to Python MCP server to get session list
    const response = await fetch(`${MCP_HTTP_BRIDGE_URL}/sessions`, {
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
    
    // Return the session list from Python MCP server
    return NextResponse.json(result);

  } catch (error) {
    console.error('Sessions API error:', error);
    
    // Return empty list if Python server is unavailable
    return NextResponse.json({
      sessions: [],
      error: `Python MCP server unavailable: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    // Parse the request body
    const body = await request.json();
    const { session_name } = body;
    
    if (!session_name) {
      return NextResponse.json({
        error: 'session_name is required'
      }, { status: 400 });
    }
    
    // Forward request to Python MCP server with create_session action - bypasses NLP
    const response = await fetch(`${MCP_HTTP_BRIDGE_URL}`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        action: 'create_session',
        session_name: session_name
      }),
    });

    if (!response.ok) {
      throw new Error(`Python MCP server error: ${response.status}`);
    }

    const result = await response.json();
    
    // Return the session creation result from Python MCP server
    return NextResponse.json(result);

  } catch (error) {
    console.error('Session creation API error:', error);
    
    // Return error if Python server is unavailable
    return NextResponse.json({
      success: false,
      error: `Python MCP server unavailable: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }, { status: 500 });
  }
}