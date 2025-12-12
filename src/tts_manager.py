import asyncio
import threading
import time
import os
import io
import queue
from enum import Enum
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
from pathlib import Path
import pygame
import edge_tts


class TTSPlaybackMode(Enum):
    """Defines how to handle TTS when queue is full or audio is playing"""
    QUEUE = "queue"  # Queue the text and wait for current to finish
    OVERRIDE = "override"  # Stop current audio and play immediately
    CUT = "cut"  # Cut current audio and play immediately (alias for override)


@dataclass
class TTSQueueItem:
    """Represents a TTS item in the queue"""
    text: str
    voice: str
    timestamp: float


class TextToSpeechManager:
    """Manages text-to-speech functionality using Edge TTS with queue support"""
    
    def __init__(self, max_queue_size: int = 3, playback_mode: TTSPlaybackMode = TTSPlaybackMode.QUEUE):
        """
        Initialize the TextToSpeechManager
        
        Args:
            max_queue_size: Maximum number of TTS items in queue
            playback_mode: How to handle TTS when queue is full or audio is playing
        """
        self.max_queue_size = max_queue_size
        self.playback_mode = playback_mode
        self.current_voice = "en-US-AriaNeural"  # Default voice
        
        # Initialize pygame mixer for audio playback
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
        
        # Queue and state management (thread-safe)
        self.tts_queue = queue.Queue(maxsize=self.max_queue_size)
        self.current_channel: Optional[pygame.mixer.Channel] = None
        self.is_speaking = False
        
        # Background processing
        self._queue_thread = None
        self._stop_queue_thread = False
        self._start_queue_processor()
    
    def _start_queue_processor(self):
        """Start the background thread for processing TTS queue"""
        if self._queue_thread is None or not self._queue_thread.is_alive():
            self._stop_queue_thread = False
            self._queue_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._queue_thread.start()
    
    def _process_queue(self):
        """Background thread function to process TTS queue"""
        while not self._stop_queue_thread:
            try:
                # Check if we can process the next item (non-blocking)
                if not self.is_speaking or self.playback_mode in [TTSPlaybackMode.OVERRIDE, TTSPlaybackMode.CUT]:
                    # Get next item from queue (non-blocking)
                    tts_item = self.tts_queue.get_nowait()
                    
                    # If we're in override/cut mode and something is playing, stop it
                    if (self.is_speaking and 
                        self.playback_mode in [TTSPlaybackMode.OVERRIDE, TTSPlaybackMode.CUT]):
                        self._stop_current_audio()
                    
                    # Process the TTS item (no locks needed)
                    asyncio.run(self._generate_and_play_tts(tts_item))
                    
            except queue.Empty:
                # No items to process
                pass
            
            time.sleep(0.1)  # Check every 100ms
    
    async def _generate_and_play_tts(self, tts_item: TTSQueueItem):
        """Generate TTS audio and play it using in-memory streaming"""
        try:
            # Generate TTS audio using Edge TTS
            communicate = edge_tts.Communicate(tts_item.text, tts_item.voice)
            
            # Stream audio data directly to memory buffer
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            # Create pygame Sound from memory buffer
            audio_buffer = io.BytesIO(audio_data)
            sound = pygame.mixer.Sound(audio_buffer)
            
            # Play the audio directly
            self._play_audio_direct(sound)
            
        except Exception as e:
            print(f"Error generating TTS for text '{tts_item.text}': {e}")
    
    def _play_audio_direct(self, sound: pygame.mixer.Sound):
        """Play a pygame Sound object directly without locks"""
        try:
            # Stop current audio if playing
            if self.current_channel and self.current_channel.get_busy():
                self.current_channel.stop()
            
            # Find available channel or use channel 0
            channel = pygame.mixer.find_channel()
            if channel is None:
                channel = pygame.mixer.Channel(0)
            
            # Play the sound
            channel.play(sound)
            
            # Update state (atomic operations, no lock needed)
            self.current_channel = channel
            self.is_speaking = True
            
            # Start monitoring thread to detect when audio finishes
            threading.Thread(target=self._monitor_audio_completion, daemon=True).start()
            
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def _monitor_audio_completion(self):
        """Monitor when current audio finishes playing"""
        if self.current_channel:
            while self.current_channel.get_busy():
                time.sleep(0.1)
            
            # Update state (atomic operations, no lock needed)
            self.is_speaking = False
            self.current_channel = None
    
    def _stop_current_audio(self):
        """Stop currently playing audio"""
        if self.current_channel and self.current_channel.get_busy():
            self.current_channel.stop()
        self.is_speaking = False
    
    def _clear_queue(self):
        """Clear all items from the queue"""
        try:
            while True:
                self.tts_queue.get_nowait()
        except queue.Empty:
            pass
    
    def speak(self, text: str, override: bool = False) -> bool:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to convert to speech  
            override: If True, override current playback mode to use OVERRIDE
            
        Returns:
            True if text was queued/played successfully, False otherwise
        """
        if not text or not text.strip():
            return False
        
        # Determine effective playback mode
        effective_mode = TTSPlaybackMode.OVERRIDE if override else self.playback_mode
        
        # Create TTS queue item
        tts_item = TTSQueueItem(
            text=text.strip(),
            voice=self.current_voice,
            timestamp=time.time()
        )
        
        # Handle different playback modes
        if effective_mode in [TTSPlaybackMode.OVERRIDE, TTSPlaybackMode.CUT]:
            # Clear queue and stop current audio
            self._clear_queue()
            self._stop_current_audio()
            try:
                self.tts_queue.put_nowait(tts_item)
                return True
            except queue.Full:
                return False
        
        elif effective_mode == TTSPlaybackMode.QUEUE:
            # Add to queue if there's space
            try:
                self.tts_queue.put_nowait(tts_item)
                return True
            except queue.Full:
                print(f"TTS queue is full, skipping text: {text[:50]}...")
                return False
        
        return False
    
    def set_voice(self, voice: str) -> bool:
        """
        Change the TTS voice
        
        Args:
            voice: Voice identifier (e.g., "en-US-AriaNeural", "en-US-JennyNeural")
            
        Returns:
            True if voice was set successfully, False otherwise
        """
        try:
            # Validate voice by attempting to create a Communicate object
            test_communicate = edge_tts.Communicate("test", voice)
            
            self.current_voice = voice
            
            print(f"TTS voice changed to: {voice}")
            return True
            
        except Exception as e:
            print(f"Error setting voice to {voice}: {e}")
            return False
    
    def get_voice(self) -> str:
        """Get current TTS voice"""
        return self.current_voice
    
    def set_queue_length(self, max_queue_size: int):
        """
        Set maximum queue length
        
        Args:
            max_queue_size: Maximum number of items in TTS queue
        """
        self.max_queue_size = max(0, max_queue_size)
        # Note: Cannot trim queue.Queue dynamically, but new items will respect the limit
    
    def get_queue_length(self) -> int:
        """Get current queue length"""
        return self.tts_queue.qsize()
    
    def get_max_queue_length(self) -> int:
        """Get maximum queue length"""
        return self.max_queue_size
    
    def set_playback_mode(self, mode: TTSPlaybackMode):
        """
        Change the playback mode
        
        Args:
            mode: New playback mode
        """
        self.playback_mode = mode
        print(f"TTS playback mode changed to: {mode.value}")
    
    def get_playback_mode(self) -> TTSPlaybackMode:
        """Get current playback mode"""
        return self.playback_mode
    
    def stop_all(self):
        """Stop all TTS playback and clear queue"""
        # Stop current audio
        self._stop_current_audio()
        
        # Clear queue
        self._clear_queue()
        
        print("All TTS stopped and queue cleared")
    
    def get_status(self) -> Dict:
        """Get current status of the TTS manager"""
        return {
            'is_speaking': self.is_speaking,
            'current_voice': self.current_voice,
            'queue_length': self.tts_queue.qsize(),
            'max_queue_length': self.max_queue_size,
            'playback_mode': self.playback_mode.value,
            'queued_texts': []  # Cannot easily iterate queue.Queue without consuming items
        }
    
    @staticmethod
    async def get_available_voices() -> List[Dict[str, str]]:
        """
        Get list of available Edge TTS voices
        
        Returns:
            List of dictionaries with voice information
        """
        try:
            voices = await edge_tts.list_voices()
            return [
                {
                    'name': voice['Name'],
                    'short_name': voice['ShortName'], 
                    'gender': voice['Gender'],
                    'locale': voice['Locale'],
                    'language': voice['FriendlyName']
                }
                for voice in voices
            ]
        except Exception as e:
            print(f"Error getting available voices: {e}")
            return []
    
    def shutdown(self):
        """Clean shutdown of the TTS manager"""
        self._stop_queue_thread = True
        if self._queue_thread and self._queue_thread.is_alive():
            self._queue_thread.join(timeout=1.0)
        
        # Stop all audio and clear queue
        self.stop_all()


# Convenience function for quick TTS usage
_default_tts_manager = None

def get_default_tts_manager() -> TextToSpeechManager:
    """Get or create the default TTS manager instance"""
    global _default_tts_manager
    if _default_tts_manager is None:
        _default_tts_manager = TextToSpeechManager()
    return _default_tts_manager

def speak(text: str, override: bool = False) -> bool:
    """Convenience function to speak text using default TTS manager"""
    return get_default_tts_manager().speak(text, override)
