import asyncio
import threading
import time
import tempfile
import os
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
    temp_file: Optional[str] = None


class TextToSpeechManager:
    """Manages text-to-speech functionality using Edge TTS with queue support"""
    
    def __init__(self, max_queue_size: int = 10, playback_mode: TTSPlaybackMode = TTSPlaybackMode.QUEUE):
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
        
        # Queue and state management
        self.tts_queue: List[TTSQueueItem] = []
        self.current_channel: Optional[pygame.mixer.Channel] = None
        self.current_temp_file: Optional[str] = None
        self.is_speaking = False
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Background processing
        self._queue_thread = None
        self._stop_queue_thread = False
        self._start_queue_processor()
        
        # Temporary file cleanup tracking
        self._temp_files: List[str] = []
    
    def _start_queue_processor(self):
        """Start the background thread for processing TTS queue"""
        if self._queue_thread is None or not self._queue_thread.is_alive():
            self._stop_queue_thread = False
            self._queue_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._queue_thread.start()
    
    def _process_queue(self):
        """Background thread function to process TTS queue"""
        while not self._stop_queue_thread:
            with self._lock:
                # Check if we can process the next item
                if (self.tts_queue and 
                    (not self.is_speaking or self.playback_mode in [TTSPlaybackMode.OVERRIDE, TTSPlaybackMode.CUT])):
                    
                    # Get next item from queue
                    tts_item = self.tts_queue.pop(0)
                    
                    # If we're in override/cut mode and something is playing, stop it
                    if (self.is_speaking and 
                        self.playback_mode in [TTSPlaybackMode.OVERRIDE, TTSPlaybackMode.CUT]):
                        self._stop_current_audio()
                    
                    # Process the TTS item
                    asyncio.run(self._generate_and_play_tts(tts_item))
            
            time.sleep(0.1)  # Check every 100ms
    
    async def _generate_and_play_tts(self, tts_item: TTSQueueItem):
        """Generate TTS audio and play it"""
        try:
            # Generate TTS audio using Edge TTS
            communicate = edge_tts.Communicate(tts_item.text, tts_item.voice)
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_filename = temp_file.name
                tts_item.temp_file = temp_filename
                self._temp_files.append(temp_filename)
            
            # Save audio to temporary file
            await communicate.save(temp_filename)
            
            # Play the audio
            self._play_audio_file(temp_filename)
            
        except Exception as e:
            print(f"Error generating TTS for text '{tts_item.text}': {e}")
    
    def _play_audio_file(self, file_path: str):
        """Play an audio file using pygame"""
        try:
            with self._lock:
                # Load and play the sound
                sound = pygame.mixer.Sound(file_path)
                
                # Stop current audio if playing
                if self.current_channel and self.current_channel.get_busy():
                    self.current_channel.stop()
                
                # Find available channel or use channel 0
                channel = pygame.mixer.find_channel()
                if channel is None:
                    channel = pygame.mixer.Channel(0)
                
                # Play the sound
                channel.play(sound)
                
                # Update state
                self.current_channel = channel
                self.current_temp_file = file_path
                self.is_speaking = True
                
                # Start monitoring thread to detect when audio finishes
                threading.Thread(target=self._monitor_audio_completion, daemon=True).start()
                
        except Exception as e:
            print(f"Error playing audio file {file_path}: {e}")
    
    def _monitor_audio_completion(self):
        """Monitor when current audio finishes playing"""
        if self.current_channel:
            while self.current_channel.get_busy():
                time.sleep(0.1)
            
            with self._lock:
                self.is_speaking = False
                
                # Clean up temporary file
                if self.current_temp_file and os.path.exists(self.current_temp_file):
                    try:
                        os.unlink(self.current_temp_file)
                        if self.current_temp_file in self._temp_files:
                            self._temp_files.remove(self.current_temp_file)
                    except Exception as e:
                        print(f"Error cleaning up temp file {self.current_temp_file}: {e}")
                
                self.current_temp_file = None
                self.current_channel = None
    
    def _stop_current_audio(self):
        """Stop currently playing audio"""
        if self.current_channel and self.current_channel.get_busy():
            self.current_channel.stop()
        self.is_speaking = False
    
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
        
        with self._lock:
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
                self.tts_queue.clear()
                self._stop_current_audio()
                self.tts_queue.append(tts_item)
                return True
            
            elif effective_mode == TTSPlaybackMode.QUEUE:
                # Add to queue if there's space
                if len(self.tts_queue) < self.max_queue_size:
                    self.tts_queue.append(tts_item)
                    return True
                else:
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
            
            with self._lock:
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
        with self._lock:
            self.max_queue_size = max(0, max_queue_size)
            
            # Trim queue if it's now too large
            if len(self.tts_queue) > self.max_queue_size:
                removed_items = self.tts_queue[self.max_queue_size:]
                self.tts_queue = self.tts_queue[:self.max_queue_size]
                print(f"Trimmed {len(removed_items)} items from TTS queue")
    
    def get_queue_length(self) -> int:
        """Get current queue length"""
        return len(self.tts_queue)
    
    def get_max_queue_length(self) -> int:
        """Get maximum queue length"""
        return self.max_queue_size
    
    def set_playback_mode(self, mode: TTSPlaybackMode):
        """
        Change the playback mode
        
        Args:
            mode: New playback mode
        """
        with self._lock:
            self.playback_mode = mode
            print(f"TTS playback mode changed to: {mode.value}")
    
    def get_playback_mode(self) -> TTSPlaybackMode:
        """Get current playback mode"""
        return self.playback_mode
    
    def stop_all(self):
        """Stop all TTS playback and clear queue"""
        with self._lock:
            # Stop current audio
            self._stop_current_audio()
            
            # Clear queue
            self.tts_queue.clear()
            
            print("All TTS stopped and queue cleared")
    
    def get_status(self) -> Dict:
        """Get current status of the TTS manager"""
        with self._lock:
            return {
                'is_speaking': self.is_speaking,
                'current_voice': self.current_voice,
                'queue_length': len(self.tts_queue),
                'max_queue_length': self.max_queue_size,
                'playback_mode': self.playback_mode.value,
                'queued_texts': [item.text[:50] + "..." if len(item.text) > 50 else item.text 
                               for item in self.tts_queue]
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
        
        # Clean up temporary files
        with self._lock:
            for temp_file in self._temp_files.copy():
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                    self._temp_files.remove(temp_file)
                except Exception as e:
                    print(f"Error cleaning up temp file {temp_file}: {e}")


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

def say(text: str, override: bool = False) -> bool:
    """Convenience function to say text using default TTS manager"""
    return get_default_tts_manager().say(text, override)
