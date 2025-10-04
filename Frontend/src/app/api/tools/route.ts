import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // In production, this would fetch from the Python backend
    // For now, return mock data that matches the plugin system
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080';

    try {
      const response = await fetch(`${backendUrl}/tools`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        cache: 'no-store'
      });

      if (response.ok) {
        const data = await response.json();
        return NextResponse.json(data);
      }
    } catch (fetchError) {
      console.warn('Failed to fetch from backend, using fallback data:', fetchError);
    }

    // Fallback to default tools if backend is unavailable
    const tools = [
      {
        tool_id: 'unreal_engine',
        display_name: 'Unreal Engine',
        version: '5.5.4',
        description: 'Real-time 3D creation for games, film, and virtual production',
        icon: '🎮',
        status: 'available',
        capabilities: [
          'mesh_3d_creation',
          'mesh_3d_editing',
          'scene_management',
          'rendering',
          'lighting_control',
          'camera_control',
          'animation',
          'geospatial'
        ]
      },
      {
        tool_id: 'nano_banana',
        display_name: 'Nano Banana',
        version: '1.0.0',
        description: 'AI-powered image generation, editing, and style transfer',
        icon: '🍌',
        status: 'available',
        capabilities: [
          'image_generation',
          'image_editing',
          'image_style_transfer'
        ]
      }
    ];

    return NextResponse.json({ tools, source: 'fallback' });
  } catch (error) {
    console.error('Error in /api/tools:', error);
    return NextResponse.json(
      { error: 'Failed to fetch tools', tools: [] },
      { status: 500 }
    );
  }
}
