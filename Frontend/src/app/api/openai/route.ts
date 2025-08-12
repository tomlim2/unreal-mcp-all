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
- get_ultra_dynamic_sky: Get Ultra Dynamic Sky actor info and current time of day
- get_time_of_day: Get current time from Ultra Dynamic Sky
- set_time_of_day: Set time in HHMM format (0000-2359), params: {time_of_day: number, sky_name?: string}
- get_actors_in_level: List all actors in level
- create_actor: Create new actor, params: {name: string, type: string, location?: [x,y,z], rotation?: [x,y,z], scale?: [x,y,z]}
- delete_actor: Delete actor by name, params: {name: string}
- set_actor_transform: Move/rotate/scale actor, params: {name: string, location?: [x,y,z], rotation?: [x,y,z], scale?: [x,y,z]}
- get_actor_properties: Get actor properties, params: {name: string}

IMPORTANT - Time Format Conversion Rules:
When user requests time changes, convert natural language to HHMM format:
- "sunrise" or "6 AM" → time_of_day: 600
- "sunset" or "6 PM" → time_of_day: 1800
- "1 PM" → time_of_day: 1300
- "23:30" → time_of_day: 2330
- "12:30 AM" → time_of_day: 30
- "noon" → time_of_day: 1200
- "midnight" → time_of_day: 0

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
    // Call the real Python MCP server via HTTP bridge
    const response = await fetch('http://127.0.0.1:8080', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(command),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result;
    
  } catch (error) {
    // Fallback to simulated response if HTTP bridge is not available
    console.warn(`MCP HTTP Bridge not available: ${error}. Using fallback simulation.`);
    
    const simulatedResponse = {
      status: "error",
      error: `HTTP Bridge unavailable: ${error}`,
      fallback: true,
      timestamp: new Date().toISOString(),
      // Add typical response format from your Python MCP server
      result: command.type === 'get_actors_in_level' 
        ? { actors: ['Ultra_Dynamic_Sky_C_0', 'PlayerStart', 'Cube_Actor'] }
        : command.type === 'set_time_of_day'
        ? { time_of_day: command.params.time_of_day, sky_name: command.params.sky_name || 'Ultra_Dynamic_Sky_C_0' }
        : { status: 'executed' }
    };

    return simulatedResponse;
  }
}