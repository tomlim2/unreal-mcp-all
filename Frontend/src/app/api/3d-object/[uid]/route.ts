import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { uid: string } }
) {
  try {
    const { uid } = params;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080';

    // Proxy request to Python backend
    const response = await fetch(`${backendUrl}/3d-object/${uid}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/octet-stream',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: '3D object not found' },
        { status: 404 }
      );
    }

    // Get the file data
    const buffer = await response.arrayBuffer();

    // Determine content type based on UID prefix or response headers
    let contentType = response.headers.get('content-type') || 'application/octet-stream';

    if (uid.startsWith('fbx_')) {
      contentType = 'application/octet-stream';
    } else if (uid.startsWith('obj_')) {
      contentType = 'text/plain';
    } else if (uid.includes('gltf')) {
      contentType = 'model/gltf+json';
    } else if (uid.includes('glb')) {
      contentType = 'model/gltf-binary';
    }

    // Return the file
    return new NextResponse(buffer, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `attachment; filename="${uid}"`,
        'Cache-Control': 'public, max-age=31536000',
      },
    });
  } catch (error) {
    console.error('Error fetching 3D object:', error);
    return NextResponse.json(
      { error: 'Failed to fetch 3D object' },
      { status: 500 }
    );
  }
}
