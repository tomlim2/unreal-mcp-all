import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import { platform } from 'os';

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
  try {
    const { path } = await request.json();

    if (!path) {
      return NextResponse.json(
        { error: 'Path is required' },
        { status: 400 }
      );
    }

    // Determine the command based on the platform
    const os = platform();
    let command: string;

    switch (os) {
      case 'win32':
        // Windows: Use explorer to open the folder
        command = `explorer "${path}"`;
        break;
      case 'darwin':
        // macOS: Use open command
        command = `open "${path}"`;
        break;
      case 'linux':
        // Linux: Use xdg-open
        command = `xdg-open "${path}"`;
        break;
      default:
        return NextResponse.json(
          { error: `Unsupported platform: ${os}` },
          { status: 500 }
        );
    }

    await execAsync(command);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error opening folder:', error);
    return NextResponse.json(
      { error: 'Failed to open folder' },
      { status: 500 }
    );
  }
}
