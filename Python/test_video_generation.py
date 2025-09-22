#!/usr/bin/env python3
"""
Test script for video generation handler.
Uses small test image to minimize API costs.
"""

import os
os.environ['UNREAL_PROJECT_PATH'] = 'E:\\CINEVStudio\\CINEVStudio'

from tools.ai.command_handlers.video_generation.video_handler import VideoGenerationHandler

def test_video_generation():
    handler = VideoGenerationHandler()

    # Test actual video generation with very small, simple parameters
    test_params = {
        'prompt': 'gentle zoom in',  # Very simple prompt to minimize processing
        'aspect_ratio': '16:9',
        'resolution': '720p'  # Lowest resolution to minimize cost
    }

    print('Starting video generation test with small image...')
    print('Parameters:', test_params)

    try:
        # This will actually call Veo-3 API with our small test image
        result = handler._generate_video_from_latest_screenshot(test_params)
        print('✅ Video generation completed!')
        print('Result keys:', list(result.keys()) if isinstance(result, dict) else 'Not a dict')

        if isinstance(result, dict) and 'video_uid' in result:
            print(f'Video UID: {result["video_uid"]}')
            print(f'Filename: {result.get("filename", "N/A")}')
            print(f'Cost: ${result.get("cost", 0):.2f}')
            print(f'Processing time: {result.get("processing_time_seconds", 0):.1f}s')
            print(f'Video path: {result.get("video_path", "N/A")}')
        elif isinstance(result, dict) and 'error' in result:
            print(f'❌ Error: {result["error"]}')
        else:
            print(f'Unexpected result: {result}')

    except Exception as e:
        print(f'❌ Exception during video generation: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_video_generation()