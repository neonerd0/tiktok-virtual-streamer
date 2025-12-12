from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QTextCharFormat, QColor
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
from tts_manager import TextToSpeechManager


class MessageType(Enum):
    DEFAULT = "default"
    ALERT = "alert"
    WARNING = "warning"


@dataclass
class MessageConfig:
    """Configuration for message formatting"""
    color: str
    font_size: int
    is_bold: bool = False
    
    def to_char_format(self) -> QTextCharFormat:
        """Convert to QTextCharFormat"""
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(self.color))
        char_format.setFontPointSize(self.font_size)
        if self.is_bold:
            char_format.setFontWeight(QFont.Weight.Bold)
        return char_format


class LiveFeedWidget(QWidget):
    # Signal for opacity changes
    opacity_changed = pyqtSignal(float)
    
    def __init__(self, parent=None, tts_manager: Optional[TextToSpeechManager] = None):
        super().__init__(parent)
        self._message_configs = self._get_default_configs()
        self.tts_manager = tts_manager
        self.setup_ui()
    
    def _get_default_configs(self) -> Dict[MessageType, MessageConfig]:
        """Get default message configurations"""
        return {
            MessageType.DEFAULT: MessageConfig(color="#ffffff", font_size=10, is_bold=False),
            MessageType.ALERT: MessageConfig(color="#ff6b6b", font_size=12, is_bold=True),
            MessageType.WARNING: MessageConfig(color="#ffa500", font_size=11, is_bold=True)
        }
    
    def setup_ui(self):
        """Set up the user interface"""
        # Create vertical layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create scrollable text box
        self.text_feed = QTextEdit()
        self.text_feed.setReadOnly(True)
        
        # Set font for better readability
        font = QFont("Consolas", 10)
        self.text_feed.setFont(font)
        
        # # Set dark background for better contrast
        # self.text_feed.setStyleSheet("""
        #     QTextEdit {
        #         background-color: #2b2b2b;
        #         border: 1px solid #555;
        #         border-radius: 4px;
        #     }
        # """)
        
        # Set placeholder text
        self.text_feed.setPlaceholderText("Live feed will appear here...")
        
        # Add to layout
        layout.addWidget(self.text_feed)
        
        # Remove margins for cleaner look
        layout.setContentsMargins(0, 0, 0, 0)
    
    def add_message(self, message, message_type=MessageType.DEFAULT, say_outloud=False):
        """Add a message to the feed with specified type and formatting"""
        # Get current cursor
        cursor = self.text_feed.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Get configuration for message type
        config = self._message_configs.get(message_type, self._message_configs[MessageType.DEFAULT])
        char_format = config.to_char_format()
        
        # Insert the formatted message
        cursor.insertText(message + "\n", char_format)
        
        # Auto-scroll to bottom
        scrollbar = self.text_feed.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Use TTS if requested and available
        if say_outloud and self.tts_manager:
            self.tts_manager.speak(message)
    
    def clear_feed(self):
        """Clear all messages from the feed"""
        self.text_feed.clear()
    
    def get_all_text(self):
        """Get all text from the feed"""
        return self.text_feed.toPlainText()
    
    def set_font_size(self, size):
        """Set the font size of the feed"""
        font = self.text_feed.font()
        font.setPointSize(size)
        self.text_feed.setFont(font)
    
    def set_font_family(self, family):
        """Set the font family of the feed"""
        font = self.text_feed.font()
        font.setFamily(family)
        self.text_feed.setFont(font)
    
    def set_read_only(self, read_only):
        """Set whether the text box is read-only"""
        self.text_feed.setReadOnly(read_only)
    
    def set_config(self, message_type: MessageType, config: MessageConfig):
        """Set configuration for a specific message type"""
        self._message_configs[message_type] = config
    
    def get_config(self, message_type: MessageType) -> MessageConfig:
        """Get configuration for a specific message type"""
        return self._message_configs.get(message_type, self._message_configs[MessageType.DEFAULT])
    
    def get_all_configs(self) -> Dict[MessageType, MessageConfig]:
        """Get all message configurations"""
        return self._message_configs.copy()
    
    def reset_configs(self):
        """Reset to default configurations"""
        self._message_configs = self._get_default_configs()
    
    @pyqtSlot(float)
    def on_opacity_change(self, opacity):
        """Slot for opacity changes - changes widget background opacity but keeps text opaque"""
        # Convert opacity (0.0-1.0) to alpha value (0-255)
        alpha = int(opacity * 255)
        
        # Set background color with alpha for the widget
        self.setStyleSheet(f"""
            LiveFeedWidget {{
                background-color: rgba(40, 40, 40, {alpha});
                border-radius: 5px;
            }}
            QTextEdit {{
                background-color: rgba(30, 30, 30, {alpha});
                border: 1px solid rgba(80, 80, 80, {alpha});
                border-radius: 3px;
                selection-background-color: rgba(100, 150, 200, 180);
            }}
        """)
