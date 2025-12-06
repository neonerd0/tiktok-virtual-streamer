# Text-to-Speech (TTS) Manager Usage Guide

## Overview

The `TextToSpeechManager` class provides Edge TTS support with advanced queue management and playback control. It supports voice changing, queueing, and different playback modes.

## Installation

First, install the required dependency:

```bash
pip install edge-tts
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

## Basic Usage

### Import and Initialize

```python
from src.tts_manager import TextToSpeechManager, TTSPlaybackMode

# Create TTS manager with default settings
tts = TextToSpeechManager()

# Or with custom settings
tts = TextToSpeechManager(
    max_queue_size=10,
    playback_mode=TTSPlaybackMode.QUEUE
)
```

### Speaking Text

```python
# Basic speech
tts.speak("Hello, this is a test message!")

# Alternative method (same functionality)
tts.say("Hello, this is a test message!")

# Override current speech (interrupt and play immediately)
tts.speak("This will interrupt current speech!", override=True)
```

### Voice Management

```python
# Change voice
tts.set_voice("en-US-JennyNeural")  # Female voice
tts.set_voice("en-US-GuyNeural")    # Male voice
tts.set_voice("en-GB-SoniaNeural")  # British accent

# Get current voice
current_voice = tts.get_voice()
print(f"Current voice: {current_voice}")

# Get available voices (async function)
import asyncio
voices = await TextToSpeechManager.get_available_voices()
for voice in voices[:5]:  # Show first 5
    print(f"{voice['name']} - {voice['gender']} ({voice['locale']})")
```

### Queue Management

```python
# Set queue length
tts.set_queue_length(15)  # Allow up to 15 items in queue

# Get queue status
status = tts.get_status()
print(f"Queue length: {status['queue_length']}")
print(f"Is speaking: {status['is_speaking']}")
print(f"Queued texts: {status['queued_texts']}")

# Stop all and clear queue
tts.stop_all()
```

### Playback Modes

```python
# QUEUE mode (default) - queue messages when busy
tts.set_playback_mode(TTSPlaybackMode.QUEUE)

# OVERRIDE mode - always interrupt current speech
tts.set_playback_mode(TTSPlaybackMode.OVERRIDE)

# CUT mode - same as OVERRIDE (alias)
tts.set_playback_mode(TTSPlaybackMode.CUT)
```

## Integration with Main Application

The TTS manager is automatically integrated into the main application. You can use it through the MainWindow:

```python
# In your main application
window = MainWindow()

# Use TTS through the window
window.speak("Welcome to the stream!")
window.set_tts_voice("en-US-AriaNeural")

# Get TTS status
status = window.get_tts_status()
print(status)
```

## Available Voices

Some popular Edge TTS voices:

### English (US)
- `en-US-AriaNeural` - Female, natural
- `en-US-JennyNeural` - Female, assistant style
- `en-US-GuyNeural` - Male, natural
- `en-US-AndrewNeural` - Male, news style
- `en-US-EmmaNeural` - Female, chat style
- `en-US-BrianNeural` - Male, news style

### English (UK)
- `en-GB-SoniaNeural` - Female
- `en-GB-RyanNeural` - Male

### Other Languages
- `es-ES-ElviraNeural` - Spanish (Spain), Female
- `fr-FR-DeniseNeural` - French (France), Female
- `de-DE-KatjaNeural` - German, Female
- `ja-JP-NanamiNeural` - Japanese, Female

## Example: TikTok Event Integration

```python
# Example: Speak when someone follows
@self.client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    message = f"Thank you {event.user.nickname} for following!"
    self.speak(message)

# Example: Announce gifts with different voice
@self.client.on(GiftEvent)  
async def on_gift(event: GiftEvent):
    # Use excited voice for gifts
    self.set_tts_voice("en-US-JennyNeural")
    message = f"Wow! {event.user.nickname} sent {event.gift.name}!"
    self.speak(message, override=True)  # Interrupt other messages
```

## Error Handling

```python
try:
    # TTS operations
    success = tts.speak("Hello world!")
    if not success:
        print("Failed to queue TTS message")
        
    # Voice changing
    if not tts.set_voice("invalid-voice"):
        print("Failed to set voice")
        
except Exception as e:
    print(f"TTS error: {e}")
```

## Cleanup

Always properly shutdown the TTS manager:

```python
# Manual cleanup
tts.shutdown()

# The MainWindow automatically handles cleanup on close
```

## Testing

Run the test script to verify functionality:

```bash
python test_tts.py
```

This will test:
- Basic TTS functionality
- Voice changing
- Queue management
- Different playback modes

## Tips

1. **Voice Selection**: Test different voices to find ones that work well for your use case
2. **Queue Management**: Adjust queue size based on your needs (larger for busy streams)
3. **Playback Modes**: Use QUEUE for normal operation, OVERRIDE for important announcements
4. **Performance**: TTS generation happens asynchronously to avoid blocking the UI
5. **Temporary Files**: The manager automatically cleans up temporary audio files
