import pygame
import threading
import time
from enum import Enum
from typing import Optional, List, Dict
from dataclasses import dataclass
from pathlib import Path
import os


class AudioPlaybackMode(Enum):
    """Defines how to handle audio when max sources is reached"""
    STOP_EARLIEST = "stop_earliest"  # Stop one of the earlier audio and immediately play it
    SKIP = "skip"  # Don't play it
    QUEUE = "queue"  # Queue it and wait for a sound to finish unless queue is full


@dataclass
class AudioSource:
    """Represents an active audio source"""
    file_path: str
    channel: pygame.mixer.Channel
    start_time: float
    
    def is_playing(self) -> bool:
        """Check if this audio source is still playing"""
        return self.channel.get_busy()
    
    def stop(self):
        """Stop this audio source"""
        self.channel.stop()


class AudioManager:
    """Manages audio playback with configurable limits and queue behavior"""
    
    def __init__(self, max_concurrent_sounds: int = 3, max_queue_size: int = 5, 
                 playback_mode: AudioPlaybackMode = AudioPlaybackMode.QUEUE):
        """
        Initialize the AudioManager
        
        Args:
            max_concurrent_sounds: Maximum number of sounds playing simultaneously
            max_queue_size: Maximum number of sounds in queue when using QUEUE mode
            playback_mode: How to handle audio when max sources is reached
        """
        self.max_concurrent_sounds = max_concurrent_sounds
        self.max_queue_size = max_queue_size
        self.playback_mode = playback_mode
        
        # Initialize pygame mixer
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        
        # Track active audio sources
        self.active_sources: List[AudioSource] = []
        self.audio_queue: List[str] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Background thread for queue processing
        self._queue_thread = None
        self._stop_queue_thread = False
        
        if self.playback_mode == AudioPlaybackMode.QUEUE:
            self._start_queue_processor()
    
    def _start_queue_processor(self):
        """Start the background thread for processing queued audio"""
        if self._queue_thread is None or not self._queue_thread.is_alive():
            self._stop_queue_thread = False
            self._queue_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._queue_thread.start()
    
    def _process_queue(self):
        """Background thread function to process queued audio"""
        while not self._stop_queue_thread:
            with self._lock:
                # Clean up finished audio sources
                self._cleanup_finished_sources()
                
                # Try to play queued audio if we have available slots
                if self.audio_queue and len(self.active_sources) < self.max_concurrent_sounds:
                    file_path = self.audio_queue.pop(0)
                    self._play_audio_immediate(file_path)
            
            time.sleep(0.1)  # Check every 100ms
    
    def _cleanup_finished_sources(self):
        """Remove finished audio sources from active list"""
        self.active_sources = [source for source in self.active_sources if source.is_playing()]
    
    def _play_audio_immediate(self, file_path: str) -> bool:
        """
        Play audio immediately without queue checks
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            True if audio started playing, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                print(f"Audio file not found: {file_path}")
                return False
            
            # Load and play the sound
            sound = pygame.mixer.Sound(file_path)
            channel = pygame.mixer.find_channel()
            
            if channel is None:
                # All channels are busy, force use of channel 0
                channel = pygame.mixer.Channel(0)
            
            channel.play(sound)
            
            # Track this audio source
            audio_source = AudioSource(
                file_path=file_path,
                channel=channel,
                start_time=time.time()
            )
            self.active_sources.append(audio_source)
            
            return True
            
        except Exception as e:
            print(f"Error playing audio {file_path}: {e}")
            return False
    
    def play_audio(self, file_path: str) -> bool:
        """
        Play an audio file according to the configured playback mode
        
        Args:
            file_path: Path to the audio file to play
            
        Returns:
            True if audio was played or queued successfully, False otherwise
        """
        if not file_path or not file_path.strip():
            return False
        
        with self._lock:
            # Clean up finished sources first
            self._cleanup_finished_sources()
            
            # If we have available slots, play immediately
            if len(self.active_sources) < self.max_concurrent_sounds:
                return self._play_audio_immediate(file_path)
            
            # Handle different playback modes when at capacity
            if self.playback_mode == AudioPlaybackMode.STOP_EARLIEST:
                # Stop the earliest (oldest) audio source
                if self.active_sources:
                    oldest_source = min(self.active_sources, key=lambda s: s.start_time)
                    oldest_source.stop()
                    self.active_sources.remove(oldest_source)
                
                return self._play_audio_immediate(file_path)
            
            elif self.playback_mode == AudioPlaybackMode.SKIP:
                # Don't play the audio
                print(f"Skipping audio {file_path} - max concurrent sounds reached")
                return False
            
            elif self.playback_mode == AudioPlaybackMode.QUEUE:
                # Add to queue if there's space
                if len(self.audio_queue) < self.max_queue_size:
                    self.audio_queue.append(file_path)
                    return True
                else:
                    print(f"Skipping audio {file_path} - queue is full")
                    return False
        
        return False
    
    def stop_all_audio(self):
        """Stop all currently playing audio and clear the queue"""
        with self._lock:
            # Stop all active audio sources
            for source in self.active_sources:
                source.stop()
            
            # Clear active sources and queue
            self.active_sources.clear()
            self.audio_queue.clear()
            
            print("All audio stopped and queue cleared")
    
    def get_status(self) -> Dict:
        """Get current status of the audio manager"""
        with self._lock:
            self._cleanup_finished_sources()
            return {
                'active_sounds': len(self.active_sources),
                'max_concurrent': self.max_concurrent_sounds,
                'queued_sounds': len(self.audio_queue),
                'max_queue_size': self.max_queue_size,
                'playback_mode': self.playback_mode.value,
                'active_files': [source.file_path for source in self.active_sources],
                'queued_files': self.audio_queue.copy()
            }
    
    def set_playback_mode(self, mode: AudioPlaybackMode):
        """Change the playback mode"""
        with self._lock:
            old_mode = self.playback_mode
            self.playback_mode = mode
            
            # Start queue processor if switching to QUEUE mode
            if mode == AudioPlaybackMode.QUEUE and old_mode != AudioPlaybackMode.QUEUE:
                self._start_queue_processor()
    
    def set_max_concurrent_sounds(self, max_sounds: int):
        """Change the maximum number of concurrent sounds"""
        with self._lock:
            self.max_concurrent_sounds = max(1, max_sounds)
    
    def set_max_queue_size(self, max_queue: int):
        """Change the maximum queue size"""
        with self._lock:
            self.max_queue_size = max(0, max_queue)
            
            # Trim queue if it's now too large
            if len(self.audio_queue) > self.max_queue_size:
                self.audio_queue = self.audio_queue[:self.max_queue_size]
    
    def shutdown(self):
        """Clean shutdown of the audio manager"""
        self._stop_queue_thread = True
        if self._queue_thread and self._queue_thread.is_alive():
            self._queue_thread.join(timeout=1.0)
        
        self.stop_all_audio()
        pygame.mixer.quit()
