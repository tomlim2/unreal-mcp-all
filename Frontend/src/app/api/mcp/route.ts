import { NextRequest, NextResponse } from 'next/server';

// Python MCP HTTP Bridge URL
const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

export async function POST(request: NextRequest) {
  try {
    const { prompt, context } = await request.json();

    if (!prompt) {
      return NextResponse.json({ error: 'Prompt is required' }, { status: 400 });
    }

    // Forward request to Python MCP server with natural language processing
    const response = await fetch(MCP_HTTP_BRIDGE_URL, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        prompt,
        context: context || 'User is working with Unreal Engine project'
      }),
    });

    if (!response.ok) {
      throw new Error(`Python MCP server error: ${response.status}`);
    }

    const result = await response.json();
    
    // Return the result from Python MCP server directly
    return NextResponse.json(result);

  } catch (error) {
    console.error('MCP Bridge error:', error);
    
    // Fallback response if Python server is unavailable
    return NextResponse.json({
      error: `Python MCP server unavailable: ${error instanceof Error ? error.message : 'Unknown error'}`,
      explanation: "Could not connect to Python MCP server. Make sure it's running on port 8080.",
      commands: [],
      executionResults: [],
      fallback: true
    }, { status: 500 });
  }
}