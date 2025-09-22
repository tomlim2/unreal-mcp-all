#!/usr/bin/env python3
"""
Test NLP integration with video generation commands.
"""

import os
os.environ['UNREAL_PROJECT_PATH'] = 'E:\\CINEVStudio\\CINEVStudio'

from tools.ai.nlp import process_natural_language

def test_nlp_video_integration():
    # Test video generation through NLP
    user_input = "Create a video with gentle camera movement"

    print(f'Testing NLP input: "{user_input}"')

    try:
        result = process_natural_language(user_input)
        print('✅ NLP processing completed!')

        if isinstance(result, dict):
            print(f'Response keys: {list(result.keys())}')
            print(f'Explanation: {result.get("explanation", "N/A")}')

            commands = result.get("commands", [])
            print(f'Number of commands: {len(commands)}')

            for i, cmd in enumerate(commands):
                print(f'Command {i+1}: {cmd.get("type", "unknown")}')
                if cmd.get("type") == "generate_video_from_image":
                    print(f'  Prompt: {cmd.get("params", {}).get("prompt", "N/A")}')
                    print('  ✅ Video generation command detected!')
        else:
            print(f'Unexpected result type: {type(result)}')

    except Exception as e:
        print(f'❌ Exception during NLP processing: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_nlp_video_integration()