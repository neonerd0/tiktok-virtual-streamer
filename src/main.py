from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, JoinEvent, RoomUserSeqEvent, FollowEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLineEdit, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from widgets import LiveConnectWidget, LiveFeedWidget, MessageType, MessageConfig, SettingsWidget
from event_config import TikTokEventSettings
from audio_manager import AudioManager, AudioPlaybackMode
from tts_manager import TextToSpeechManager, TTSPlaybackMode
import sys
import asyncio
import qasync


class DraggableMainWindow(QMainWindow):
    """A draggable settings window that can be moved around"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = None
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._offset = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self._offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.pos() - self._offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging"""
        self._offset = None
        super().mouseReleaseEvent(event)


class MainWindow(DraggableMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TikTok Live Overlay")
        self.client = None
        self.client_unique_id = ""
        self.event_settings = TikTokEventSettings()
        self.translucent_background_enabled = False  # Track translucent background state
        
        # Initialize audio manager
        self.audio_manager = AudioManager(
            max_concurrent_sounds=3,
            max_queue_size=5,
            playback_mode=AudioPlaybackMode.QUEUE
        )
        
        # Initialize TTS manager
        self.tts_manager = TextToSpeechManager(
            max_queue_size=10,
            playback_mode=TTSPlaybackMode.QUEUE
        )
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        self.__layout = QVBoxLayout()
        central_widget.setLayout(self.__layout)

        # Add the LiveConnectWidget with 5 retries
        self.live_connect_widget = LiveConnectWidget("@", max_retries=5)
        self.__layout.addWidget(self.live_connect_widget)
        
        # Add the LiveFeedWidget
        self.live_feed_widget = LiveFeedWidget()
        self.__layout.addWidget(self.live_feed_widget)
        
        # Create separate settings window (initially hidden)
        self.settings_window = None
        
        # Connect the widget's signals
        self.live_connect_widget.connection_toggled.connect(self.on_connection_toggled)
        self.live_connect_widget.retry_attempt.connect(self.on_retry_attempt)
        self.live_connect_widget.settings_toggled.connect(self.on_settings_toggled)
        self.live_connect_widget.streamer_mode_toggled.connect(self.on_streamer_mode_toggled)
        self.live_connect_widget.opacity_changed.connect(self.live_connect_widget.on_opacity_change)
        self.live_feed_widget.opacity_changed.connect(self.live_feed_widget.on_opacity_change)
        
        # Initialize settings widget with current configurations
        self.setup_settings_widget()
        self.toggle_translucent_background(True)
    
    def play_event_audio(self, config):
        """Helper method to play audio for an event if configured"""
        if config and config.chime_audio_file:
            success = self.audio_manager.play_audio(config.chime_audio_file)
            if not success:
                print(f"Failed to play audio: {config.chime_audio_file}")

    def on_connection_toggled(self, should_connect):
        """Handle connection toggle from the widget"""
        if should_connect:
            asyncio.create_task(self.start_client())
        else:
            asyncio.create_task(self.stop_client())
    
    def on_retry_attempt(self, current_attempt, max_retries):
        """Handle retry attempt notifications"""
        print(f"Retry attempt {current_attempt}/{max_retries} - waiting for exponential backoff...")
    
    def on_settings_toggled(self, show_settings):
        """Handle settings window toggle"""
        if show_settings:
            if self.settings_window is None:
                self.create_settings_window()
            self.settings_window.show()
            self.settings_window.raise_()  # Bring to front
            self.settings_window.activateWindow()  # Give focus
        else:
            if self.settings_window is not None:
                self.settings_window.hide()
    
    def on_streamer_mode_toggled(self, streamer_mode_on):
        """Handle streamer mode toggle - controls translucent background"""
        self.toggle_translucent_background(streamer_mode_on)
    
    def create_settings_window(self):
        """Create the settings window"""
        # Create draggable settings window
        self.settings_window = DraggableMainWindow(self)
        self.settings_window.setWindowTitle("TikTok Live Settings")
        self.settings_window.resize(500, 700)  # Resizable settings window
        
        # Create settings widget and set as central widget
        settings_widget = SettingsWidget()
        self.settings_window.setCentralWidget(settings_widget)
        
        # Initialize with current configurations
        self.setup_settings_widget(settings_widget)
        
        # Handle window close event to update button state
        def on_settings_close(event):
            # Reset the settings button state when window is closed
            self.live_connect_widget._LiveConnectWidget__settings_visible = False
            self.live_connect_widget.settings_button.setStyleSheet("")
            event.accept()
            
        self.settings_window.closeEvent = on_settings_close
    
    def setup_settings_widget(self, settings_widget=None):
        """Initialize settings widget with current configurations"""
        if settings_widget is None:
            return  # No widget to setup yet
            
        # Set current event settings
        settings_widget.set_event_settings(self.event_settings)
        
        # Get current message configs from live feed widget
        message_configs = self.live_feed_widget.get_all_configs()
        settings_widget.set_message_configs(message_configs)
        
        # Connect settings widget signals
        settings_widget.event_settings_changed.connect(self.on_event_settings_changed)
        settings_widget.message_config_changed.connect(self.on_message_config_changed)
        settings_widget.opacity_changed.connect(self.on_opacity_changed)
    
    def on_event_settings_changed(self, event_name, config):
        """Handle event settings changes from settings widget"""
        # Settings are already updated in self.event_settings
        # Add feedback message
        status = "enabled" if config.enabled else "disabled"
        message = f"🔄 Event '{event_name}' {status}"
        self.live_feed_widget.add_message(message, MessageType.WARNING)
    
    def on_message_config_changed(self, message_type, config):
        """Handle message config changes from settings widget"""
        # Update live feed widget configuration
        self.live_feed_widget.set_config(message_type, config)
        
        # Add feedback message
        message = f"🎨 Updated {message_type.value} message appearance"
        self.live_feed_widget.add_message(message, MessageType.WARNING)
    
    def on_opacity_changed(self, opacity):
        """Handle opacity changes from settings widget"""
        # Emit opacity change signals to other widgets so they can handle it
        self.live_connect_widget.opacity_changed.emit(opacity)
        self.live_feed_widget.opacity_changed.emit(opacity)
    
    async def start_client(self):
        """Start the TikTok Live client"""
        username = self.live_connect_widget.get_username()
        if not username:
            print("Please enter a username")
            self.live_connect_widget.set_connection_state(LiveConnectWidget.STATE_DISCONNECTED)
            return
        
        try:
            self.client = TikTokLiveClient(unique_id=username)
            self.client_unique_id = username
            
            # Set up event handlers based on configuration
            self.setup_event_handlers()
            
            # Start the client using the current event loop
            print(f"Attempting to connect to @{username}...")
            await self.client.start()
            
        except Exception as e:
            error_message = f"❌ Error connecting to TikTok Live: {e}"
            print(error_message)
            self.live_feed_widget.add_message(error_message, MessageType.WARNING)
            self.live_connect_widget.connection_failed()
    
    async def stop_client(self):
        """Stop the TikTok Live client"""
        if self.client:
            try:
                # TikTokLiveClient uses disconnect() method, not stop()
                await self.client.disconnect()
                message = "🔌 Disconnected from TikTok Live"
                print(message)
                self.live_feed_widget.add_message(message, MessageType.WARNING)
            except Exception as e:
                error_message = f"❌ Error disconnecting: {e}"
                print(error_message)
                self.live_feed_widget.add_message(error_message, MessageType.WARNING)
            finally:
                self.client = None
        
        # Ensure widget is in disconnected state
        self.live_connect_widget.set_connection_state(LiveConnectWidget.STATE_DISCONNECTED)
    
    def setup_event_handlers(self):
        """Set up TikTok Live event handlers based on configuration"""
        if not self.client:
            return
        
        # Set up all handlers - they read settings dynamically
        self._setup_connect_handler()
        self._setup_comment_handler()
        self._setup_gift_handler()
        self._setup_join_handler()
        self._setup_viewer_count_handler()
        self._setup_follow_handler()
    
    def _setup_connect_handler(self):
        """Set up connection event handler"""
        @self.client.on(ConnectEvent)
        async def on_connect_success(event: ConnectEvent):
            if not self.event_settings.is_enabled('connect'):
                return
            
            config = self.event_settings.get_config('connect')
            message = config.message_template.format(
                unique_id=event.unique_id,
                room_id=self.client.room_id
            )
            print(message)
            self.live_feed_widget.add_message(message, config.message_type)
            
            # Play audio if configured
            self.play_event_audio(config)
            
            self.live_connect_widget.connection_succeeded()
    
    def _setup_comment_handler(self):
        """Set up comment event handler"""
        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            if not self.event_settings.is_enabled('comments'):
                return
            
            config = self.event_settings.get_config('comments')
            message = config.message_template.format(
                nickname=event.user.nickname,
                comment=event.comment
            )
            self.live_feed_widget.add_message(message, config.message_type)
            
            # Play audio if configured
            self.play_event_audio(config)
    
    def _setup_gift_handler(self):
        """Set up gift event handler"""
        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            if not self.event_settings.is_enabled('gifts'):
                return
            
            config = self.event_settings.get_config('gifts')
            
            if event.gift.streakable and not event.streaking:
                count = event.repeat_count
            elif not event.gift.streakable:
                count = 1
            else:
                return  # Skip streak updates
            
            message = config.message_template.format(
                nickname=event.user.nickname,
                count=count,
                gift_name=event.gift.name
            )
            self.live_feed_widget.add_message(message, config.message_type)
            
            # Play audio if configured
            self.play_event_audio(config)
    
    def _setup_join_handler(self):
        """Set up join event handler"""
        @self.client.on(JoinEvent)
        async def on_join(event: JoinEvent):
            if not self.event_settings.is_enabled('joins'):
                return
            
            config = self.event_settings.get_config('joins')
            message = config.message_template.format(
                nickname=event.user.nickname
            )
            self.live_feed_widget.add_message(message, config.message_type)
            
            # Play audio if configured
            self.play_event_audio(config)
    
    def _setup_viewer_count_handler(self):
        """Set up viewer count event handler"""
        @self.client.on(RoomUserSeqEvent)
        async def on_viewer_count_update(event: RoomUserSeqEvent):
            if not self.event_settings.is_enabled('viewer_count'):
                return
            
            config = self.event_settings.get_config('viewer_count')
            message = config.message_template.format(
                count=event.m_total
            )
            self.live_feed_widget.add_message(message, config.message_type)
            
            # Play audio if configured
            self.play_event_audio(config)
    
    def _setup_follow_handler(self):
        """Set up follow event handler"""
        @self.client.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            if not self.event_settings.is_enabled('follows'):
                return
            
            config = self.event_settings.get_config('follows')
            message = config.message_template.format(
                nickname=event.user.nickname
            )
            self.live_feed_widget.add_message(message, config.message_type)
            
            # Play audio if configured
            self.play_event_audio(config)
    
    def toggle_event(self, event_name: str, enabled: bool = None):
        """Toggle an event on or off, or set to specific state"""
        if enabled is None:
            # Toggle current state
            current_state = self.event_settings.is_enabled(event_name)
            enabled = not current_state
        
        self.event_settings.enable_event(event_name, enabled)
        
        # Add feedback message
        status = "enabled" if enabled else "disabled"
        message = f"🔄 Event '{event_name}' {status}"
        self.live_feed_widget.add_message(message, MessageType.WARNING)
    
    def toggle_comments(self, enabled: bool = None):
        """Toggle comment events"""
        self.toggle_event('comments', enabled)
    
    def toggle_gifts(self, enabled: bool = None):
        """Toggle gift events"""
        self.toggle_event('gifts', enabled)
    
    def toggle_joins(self, enabled: bool = None):
        """Toggle join events"""
        self.toggle_event('joins', enabled)
    
    def toggle_viewer_count(self, enabled: bool = None):
        """Toggle viewer count events"""
        self.toggle_event('viewer_count', enabled)
    
    def toggle_follows(self, enabled: bool = None):
        """Toggle follow events"""
        self.toggle_event('follows', enabled)
    
    def get_event_status(self) -> dict:
        """Get current status of all events"""
        return {
            'connect': self.event_settings.is_enabled('connect'),
            'comments': self.event_settings.is_enabled('comments'),
            'gifts': self.event_settings.is_enabled('gifts'),
            'joins': self.event_settings.is_enabled('joins'),
            'viewer_count': self.event_settings.is_enabled('viewer_count'),
            'follows': self.event_settings.is_enabled('follows')
        }
    
    # TTS convenience methods
    def speak(self, text: str, override: bool = False) -> bool:
        """Speak text using TTS manager"""
        return self.tts_manager.speak(text, override)
    
    def set_tts_voice(self, voice: str) -> bool:
        """Change TTS voice"""
        return self.tts_manager.set_voice(voice)
    
    def get_tts_voice(self) -> str:
        """Get current TTS voice"""
        return self.tts_manager.get_voice()
    
    def set_tts_queue_length(self, length: int):
        """Set TTS queue length"""
        self.tts_manager.set_queue_length(length)
    
    def get_tts_status(self) -> dict:
        """Get TTS manager status"""
        return self.tts_manager.get_status()
    
    def stop_all_tts(self):
        """Stop all TTS and clear queue"""
        self.tts_manager.stop_all()

    def closeEvent(self, event):
        """Handle window close event"""
        if self.client:
            asyncio.create_task(self.stop_client())
        
        # Shutdown audio manager
        if hasattr(self, 'audio_manager'):
            self.audio_manager.shutdown()
        
        # Shutdown TTS manager
        if hasattr(self, 'tts_manager'):
            self.tts_manager.shutdown()
        
        event.accept()

    def toggle_translucent_background(self, enabled=None):
        """Toggle translucent background attribute on/off"""
        if enabled is None:
            # Toggle current state
            enabled = not self.translucent_background_enabled
        
        self.translucent_background_enabled = enabled
        
        if enabled:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
        # Force window to update its appearance
        self.update()
        self.updateGeometry()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set up asyncio event loop integration with Qt
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = MainWindow()
    window.show()
    
    # Run the Qt app with asyncio integration
    with loop:
        sys.exit(loop.run_forever())