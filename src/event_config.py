from dataclasses import dataclass, field
from typing import Optional
from widgets.live_feed_widget import MessageType


@dataclass
class EventConfig:
    """Configuration for TikTok Live event handling"""
    enabled: bool = True
    message_type: MessageType = MessageType.DEFAULT
    message_template: Optional[str] = None  # Custom message format string
    chime_audio_file: Optional[str] = None  # Path to audio file to play when event occurs


@dataclass
class TikTokEventSettings:
    """Settings for all TikTok Live events"""
    
    # Connection events
    connect: EventConfig = field(default_factory=lambda: EventConfig(
        enabled=True, 
        message_type=MessageType.ALERT,
        message_template="✅ Connected to @{unique_id} (Room ID: {room_id})"
    ))
    
    # Chat events
    comments: EventConfig = field(default_factory=lambda: EventConfig(
        enabled=True,
        message_type=MessageType.DEFAULT,
        message_template="💬 {nickname}: {comment}"
    ))
    
    # Gift events
    gifts: EventConfig = field(default_factory=lambda: EventConfig(
        enabled=True,
        message_type=MessageType.ALERT,
        message_template="🎁 {nickname} sent {count}x {gift_name}",
        chime_audio_file="audio/thank_you_for_the_gift.mp3"
    ))
    
    # User join events
    joins: EventConfig = field(default_factory=lambda: EventConfig(
        enabled=True,
        message_type=MessageType.DEFAULT,
        message_template="👋 {nickname} joined the stream!",
        chime_audio_file="audio/chime-sound-7143.mp3"
    ))
    
    # Viewer count updates
    viewer_count: EventConfig = field(default_factory=lambda: EventConfig(
        enabled=False,
        message_type=MessageType.DEFAULT,
        message_template="👥 Viewers: {count}"
    ))
    
    # Follow events
    follows: EventConfig = field(default_factory=lambda: EventConfig(
        enabled=True,
        message_type=MessageType.ALERT,
        message_template="❤️ {nickname} followed the stream!",
        chime_audio_file="audio/thanks_for_the_follow.mp3"
    ))
    
    def is_enabled(self, event_name: str) -> bool:
        """Check if an event is enabled"""
        config = getattr(self, event_name, None)
        return config.enabled if config else False
    
    def get_config(self, event_name: str) -> Optional[EventConfig]:
        """Get configuration for a specific event"""
        return getattr(self, event_name, None)
    
    def enable_event(self, event_name: str, enabled: bool = True):
        """Enable or disable a specific event"""
        config = getattr(self, event_name, None)
        if config:
            config.enabled = enabled
    
    def set_message_type(self, event_name: str, message_type: MessageType):
        """Set message type for a specific event"""
        config = getattr(self, event_name, None)
        if config:
            config.message_type = message_type
    
    def set_message_template(self, event_name: str, template_string: str):
        """Set message template string for a specific event"""
        config = getattr(self, event_name, None)
        if config:
            config.message_template = template_string
    
    def set_chime_audio_file(self, event_name: str, audio_file_path: str):
        """Set chime audio file path for a specific event"""
        config = getattr(self, event_name, None)
        if config:
            config.chime_audio_file = audio_file_path
