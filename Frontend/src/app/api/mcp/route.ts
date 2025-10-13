import { NextRequest, NextResponse } from 'next/server';

// Python MCP HTTP Bridge URL
const MCP_HTTP_BRIDGE_PORT = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
const MCP_HTTP_BRIDGE_URL = `http://127.0.0.1:${MCP_HTTP_BRIDGE_PORT}`;

type McpRequestBody = {
  prompt: string;
  context?: string;
  llm_model?: string;
  session_id?: string;
  main_prompt?: string;
  reference_prompts?: string[];
  target_image_uid?: string;
  mainImageData?: unknown;
  referenceImageData?: unknown[];
};

export async function POST(request: NextRequest) {
  try {
    const {
      prompt,
      context,
      session_id,
      llm_model,
      target_image_uid,
      main_prompt,
      reference_prompts,
      mainImageData,
      referenceImageData
    } = await request.json();

    if (!prompt) {
      return NextResponse.json({ error: 'Prompt is required' }, { status: 400 });
    }

    // Prepare request body for Python MCP server
    const requestBody: McpRequestBody = {
      prompt,
      context: context || 'User is working with Unreal Engine project',
      llm_model,
      session_id
    };

    // Add enhanced prompt fields
    if (main_prompt) {
      requestBody.main_prompt = main_prompt;
    }

    if (reference_prompts && Array.isArray(reference_prompts) && reference_prompts.length > 0) {
      requestBody.reference_prompts = reference_prompts;
    }

    // UID-based system for existing screenshots (target image only)
    if (target_image_uid) {
      requestBody.target_image_uid = target_image_uid;
    }

    // User-uploaded images (in-memory processing, not stored)
    if (mainImageData) {
      requestBody.mainImageData = mainImageData;
      console.log('API Route: mainImageData present');
    }

    if (referenceImageData && Array.isArray(referenceImageData) && referenceImageData.length > 0) {
      requestBody.referenceImageData = referenceImageData;
      console.log('API Route: referenceImageData count:', referenceImageData.length);
    } else {
      console.log('API Route: NO referenceImageData', { referenceImageData });
    }

    // Forward request to Python MCP server with natural language processing
    const response = await fetch(MCP_HTTP_BRIDGE_URL, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(requestBody),
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