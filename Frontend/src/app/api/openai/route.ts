import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

// MCP Server URL - adjust if needed
const MCP_SERVER_URL = 'http://127.0.0.1:55557';

interface UnrealCommand {
  type: string;
  params: Record<string, any>;
}

export async function POST(request: NextRequest) {
  try {
    const { prompt, context } = await request.json();

    if (!prompt) {
      return NextResponse.json({ error: 'Prompt is required' }, { status: 400 });
    }

    // Enhanced system prompt for Unreal Engine commands
    const systemPrompt = `You are an AI assistant that translates natural language requests into Unreal Engine commands via MCP protocol.

Available Unreal MCP commands:
- get_time_of_day: Get current time from Ultra Dynamic Sky
- set_time_of_day: Set time (0-24 hours), params: {time_of_day: number, sky_name?: string}
- get_actors_in_level: List all actors in level
- create_actor: Create new actor, params: {name: string, type: string, location?: [x,y,z], rotation?: [x,y,z], scale?: [x,y,z]}
- delete_actor: Delete actor by name, params: {name: string}
- set_actor_transform: Move/rotate/scale actor, params: {name: string, location?: [x,y,z], rotation?: [x,y,z], scale?: [x,y,z]}
- get_actor_properties: Get actor properties, params: {name: string}

Context: ${context || 'User is working with Unreal Engine project'}

Return a JSON response with:
{
  "explanation": "What you understood from the request",
  "commands": [
    {
      "type": "command_name",
      "params": {...}
    }
  ],
  "expectedResult": "What the user should expect to see"
}

User request: ${prompt}`;

    // Get AI response
    const completion = await anthropic.messages.create({
      model: 'claude-3-haiku-20240307',
      max_tokens: 1024,
      temperature: 0.1,
      messages: [
        { role: 'user', content: `${systemPrompt}\n\nUser request: ${prompt}` }
      ],
    });

    const aiResponse = completion.content[0]?.text;
    if (!aiResponse) {
      throw new Error('No response from Anthropic');
    }

    // Parse AI response
    let parsedResponse;
    try {
      parsedResponse = JSON.parse(aiResponse);
    } catch (parseError) {
      // If AI didn't return JSON, wrap it
      parsedResponse = {
        explanation: aiResponse,
        commands: [],
        expectedResult: "Please rephrase your request more specifically."
      };
    }

    // Execute commands if any
    const results = [];
    if (parsedResponse.commands && Array.isArray(parsedResponse.commands)) {
      for (const command of parsedResponse.commands) {
        try {
          const result = await executeUnrealCommand(command);
          results.push({
            command: command.type,
            success: true,
            result
          });
        } catch (error) {
          results.push({
            command: command.type,
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      }
    }

    return NextResponse.json({
      ...parsedResponse,
      executionResults: results
    });

  } catch (error) {
    console.error('Anthropic API error:', error);
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
}

async function executeUnrealCommand(command: UnrealCommand) {
  try {
    // First try to connect to your Python MCP server
    // The Python server communicates via TCP socket with Unreal Engine
    
    // For HTTP-based communication with your Python server, you could:
    // 1. Modify your Python server to also accept HTTP requests
    // 2. Or use a separate HTTP wrapper around your MCP server
    
    // For now, we'll simulate the response format your Python server would return
    const simulatedResponse = {
      success: true,
      message: `Command ${command.type} executed`,
      params: command.params,
      timestamp: new Date().toISOString(),
      // Add typical response format from your Python MCP server
      result: command.type === 'get_actors_in_level' 
        ? { actors: ['Ultra_Dynamic_Sky_C_0', 'PlayerStart', 'Cube_Actor'] }
        : command.type === 'set_time_of_day'
        ? { time_of_day: command.params.time_of_day, sky_name: command.params.sky_name || 'Ultra_Dynamic_Sky_C_0' }
        : { status: 'executed' }
    };

    return simulatedResponse;

    /* 
    TODO: Real implementation options:
    
    Option 1 - Direct HTTP to Python server (requires modifying Python server):
    const response = await fetch('http://localhost:8000/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(command),
    });
    
    Option 2 - TCP socket connection (more complex but matches your current setup):
    const net = require('net');
    const client = new net.Socket();
    // ... socket communication code
    
    Option 3 - Use MCP client libraries to connect to your stdio-based server
    */
    
  } catch (error) {
    throw new Error(`Failed to execute command: ${error}`);
  }
}