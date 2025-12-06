#!/usr/bin/env python3
"""
Test script for TextToSpeechManager functionality
"""

import asyncio
import time
from src.tts_manager import TextToSpeechManager, TTSPlaybackMode


async def test_basic_tts():
    """Test basic TTS functionality"""
    print("=== Testing Basic TTS Functionality ===")
    
    # Create TTS manager
    tts = TextToSpeechManager(max_queue_size=5, playback_mode=TTSPlaybackMode.QUEUE)
    
    try:
        # Test basic speech
        print("Testing basic speech...")
        success = tts.speak("Hello, this is a test of the text to speech system.")
        print(f"Speak result: {success}")
        
        # Wait a bit for audio to start
        await asyncio.sleep(1)
        
        # Check status
        status = tts.get_status()
        print(f"TTS Status: {status}")
        
        # Test queue functionality
        print("\nTesting queue functionality...")
        tts.say("This is the first message in the queue.")
        tts.say("This is the second message.")
        tts.say("And this is the third message.")
        
        # Check status again
        status = tts.get_status()
        print(f"TTS Status after queuing: {status}")
        
        # Wait for all to complete
        print("Waiting for TTS to complete...")
        while tts.get_status()['is_speaking'] or tts.get_status()['queue_length'] > 0:
            await asyncio.sleep(0.5)
            print(f"Queue length: {tts.get_status()['queue_length']}, Speaking: {tts.get_status()['is_speaking']}")
        
        print("All TTS completed!")
        
    finally:
        # Clean shutdown
        tts.shutdown()


async def test_voice_changing():
    """Test voice changing functionality"""
    print("\n=== Testing Voice Changes ===")
    
    tts = TextToSpeechManager()
    
    try:
        # Get available voices
        print("Getting available voices...")
        voices = await TextToSpeechManager.get_available_voices()
        
        # Show first few English voices
        english_voices = [v for v in voices if 'en-' in v['locale']][:5]
        print(f"Found {len(voices)} total voices, showing first 5 English voices:")
        for voice in english_voices:
            print(f"  - {voice['name']} ({voice['gender']}, {voice['locale']})")
        
        if english_voices:
            # Test different voices
            for i, voice in enumerate(english_voices[:3]):  # Test first 3 voices
                print(f"\nTesting voice: {voice['name']}")
                tts.set_voice(voice['name'])
                tts.say(f"Hello, this is voice number {i+1}, {voice['name']}")
                
                # Wait for completion
                while tts.get_status()['is_speaking']:
                    await asyncio.sleep(0.5)
        
    finally:
        tts.shutdown()


async def test_playback_modes():
    """Test different playback modes"""
    print("\n=== Testing Playback Modes ===")
    
    # Test QUEUE mode
    print("Testing QUEUE mode...")
    tts = TextToSpeechManager(playback_mode=TTSPlaybackMode.QUEUE)
    
    try:
        tts.say("First message in queue mode")
        tts.say("Second message in queue mode")
        tts.say("Third message in queue mode")
        
        # Wait a bit, then test override
        await asyncio.sleep(2)
        print("Testing override functionality...")
        tts.say("This should interrupt and override!", override=True)
        
        # Wait for completion
        while tts.get_status()['is_speaking'] or tts.get_status()['queue_length'] > 0:
            await asyncio.sleep(0.5)
        
        print("QUEUE mode test completed!")
        
    finally:
        tts.shutdown()
    
    # Test OVERRIDE mode
    print("\nTesting OVERRIDE mode...")
    tts = TextToSpeechManager(playback_mode=TTSPlaybackMode.OVERRIDE)
    
    try:
        tts.say("This is the first message that should be interrupted")
        await asyncio.sleep(1)
        tts.say("This message should immediately interrupt the first one")
        
        # Wait for completion
        while tts.get_status()['is_speaking']:
            await asyncio.sleep(0.5)
        
        print("OVERRIDE mode test completed!")
        
    finally:
        tts.shutdown()


async def main():
    """Run all tests"""
    print("Starting TTS Manager Tests...")
    print("Make sure you have edge-tts installed: pip install edge-tts")
    print("=" * 50)
    
    try:
        await test_basic_tts()
        await test_voice_changing()
        await test_playback_modes()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
