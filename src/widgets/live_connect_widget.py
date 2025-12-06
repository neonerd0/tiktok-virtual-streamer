from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QTimer
import time
import math


class LiveConnectWidget(QWidget):
    # Connection states
    STATE_DISCONNECTED = 0
    STATE_CONNECTING = 1
    STATE_CONNECTED = 2
    
    # Signal for opacity changes
    opacity_changed = pyqtSignal(float)
    
    # Signal for connection state changes
    connection_toggled = pyqtSignal(bool)  # True for connect, False for disconnect
    
    # Signal for retry attempts
    retry_attempt = pyqtSignal(int, int)  # current_attempt, max_retries
    
    # Signal for settings toggle
    settings_toggled = pyqtSignal(bool)  # True for show, False for hide
    
    # Signal for streamer mode toggle
    streamer_mode_toggled = pyqtSignal(bool)  # True for streamer mode on, False for off
    
    def __init__(self, title="@", parent=None, max_retries=3):
        super().__init__(parent)
        self.title = title
        self.connection_state = self.STATE_DISCONNECTED
        self.__retries = max_retries
        self.__current_retry = 0
        self.__retry_timer = QTimer()
        self.__retry_timer.setSingleShot(True)
        self.__retry_timer.timeout.connect(self.__on_retry_timeout)
        self.__settings_visible = False
        self.__streamer_mode = False
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Create horizontal layout
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # Create components
        self.title_label = QLabel(self.title)
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Enter username...")
        
        self.toggle_button = QPushButton("Connect")
        
        # Settings button
        self.settings_button = QPushButton("⚙️")
        self.settings_button.setMaximumWidth(40)
        self.settings_button.setToolTip("Toggle Settings Panel")
        
        # Streamer mode button
        self.streamer_button = QPushButton("📺")
        self.streamer_button.setMaximumWidth(40)
        self.streamer_button.setToolTip("Toggle Streamer Mode (Translucent Background)")
        
        # Add components to layout
        layout.addWidget(self.title_label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.streamer_button)
        
        # Set initial state
        self.update_ui_state()
    
    def setup_connections(self):
        """Set up signal/slot connections"""
        self.toggle_button.clicked.connect(self.toggle_connection)
        self.settings_button.clicked.connect(self.toggle_settings)
        self.streamer_button.clicked.connect(self.toggle_streamer_mode)
    
    def toggle_connection(self):
        """Toggle between connection states"""
        if self.connection_state == self.STATE_DISCONNECTED:
            self.set_connection_state(self.STATE_CONNECTING)
            self.connection_toggled.emit(True)
        elif self.connection_state == self.STATE_CONNECTING:
            self.set_connection_state(self.STATE_DISCONNECTED)
            self.__stop_retry_timer()
            self.connection_toggled.emit(False)
        elif self.connection_state == self.STATE_CONNECTED:
            self.set_connection_state(self.STATE_DISCONNECTED)
            self.connection_toggled.emit(False)
    
    def toggle_settings(self):
        """Toggle settings panel visibility"""
        self.__settings_visible = not self.__settings_visible
        self.settings_toggled.emit(self.__settings_visible)
    
    def toggle_streamer_mode(self):
        """Toggle streamer mode (translucent background)"""
        self.__streamer_mode = not self.__streamer_mode
        self.streamer_mode_toggled.emit(self.__streamer_mode)
        
        # Update button appearance and widget visibility
        if self.__streamer_mode:
            # Streamer mode ON - hide other widgets, show only streamer button
            self.title_label.hide()
            self.line_edit.hide()
            self.toggle_button.hide()
            self.settings_button.hide()
            self.streamer_button.show()
            
            self.streamer_button.setStyleSheet("QPushButton { background-color: #FF6B6B; }")
            self.streamer_button.setToolTip("Streamer Mode ON - Click to disable translucent background")
        else:
            # Streamer mode OFF - show all widgets
            self.title_label.show()
            self.line_edit.show()
            self.toggle_button.show()
            self.settings_button.show()
            self.streamer_button.show()
            
            self.streamer_button.setStyleSheet("")
            self.streamer_button.setToolTip("Streamer Mode OFF - Click to enable translucent background")
    
    def update_ui_state(self):
        """Update UI based on connection state"""
        if self.connection_state == self.STATE_DISCONNECTED:
            # Disconnected state
            self.toggle_button.setText("🔴")
            self.line_edit.setEnabled(True)
            # self.toggle_button.setStyleSheet("QPushButton { background-color: #44ff44; }")
        elif self.connection_state == self.STATE_CONNECTING:
            # Connecting state
            retry_text = f" (Retry {self.__current_retry}/{self.__retries})" if self.__current_retry > 0 else ""
            self.toggle_button.setText(f"Connecting{retry_text}")
            self.line_edit.setEnabled(False)
            # self.toggle_button.setStyleSheet("QPushButton { background-color: #ffaa44; }")
        elif self.connection_state == self.STATE_CONNECTED:
            # Connected state
            self.toggle_button.setText("🟢")
            self.line_edit.setEnabled(False)
            # self.toggle_button.setStyleSheet("QPushButton { background-color: #ff4444; }")
    
    def get_username(self):
        """Get the username from the line edit"""
        return self.line_edit.text().strip()
    
    def set_username(self, username):
        """Set the username in the line edit"""
        self.line_edit.setText(username)
    
    def set_connected_state(self, connected):
        """Programmatically set the connection state (legacy method)"""
        if connected:
            self.set_connection_state(self.STATE_CONNECTED)
        else:
            self.set_connection_state(self.STATE_DISCONNECTED)
    
    def set_connection_state(self, state):
        """Set the connection state using state constants"""
        if self.connection_state != state:
            self.connection_state = state
            if state == self.STATE_DISCONNECTED:
                self.__current_retry = 0
                self.__stop_retry_timer()
            self.update_ui_state()
    
    def start_retry_sequence(self):
        """Start the retry sequence with exponential backoff"""
        if self.__current_retry < self.__retries:
            self.__current_retry += 1
            self.set_connection_state(self.STATE_CONNECTING)
            
            # Calculate exponential backoff delay (base 2, starting at 1 second)
            delay_seconds = min(2 ** (self.__current_retry - 1), 30)  # Cap at 30 seconds
            
            self.retry_attempt.emit(self.__current_retry, self.__retries)
            self.__retry_timer.start(delay_seconds * 1000)  # Convert to milliseconds
            return True
        else:
            # Max retries reached, go to disconnected state
            self.set_connection_state(self.STATE_DISCONNECTED)
            return False
    
    def connection_failed(self):
        """Call this when a connection attempt fails"""
        if self.connection_state == self.STATE_CONNECTING:
            if not self.start_retry_sequence():
                # Max retries reached
                self.connection_toggled.emit(False)
    
    def connection_succeeded(self):
        """Call this when connection succeeds"""
        self.__current_retry = 0
        self.__stop_retry_timer()
        self.set_connection_state(self.STATE_CONNECTED)
    
    def __stop_retry_timer(self):
        """Stop the retry timer"""
        if self.__retry_timer.isActive():
            self.__retry_timer.stop()
    
    def __on_retry_timeout(self):
        """Handle retry timer timeout"""
        if self.connection_state == self.STATE_CONNECTING:
            # Emit signal to attempt reconnection
            self.connection_toggled.emit(True)
    
    def get_max_retries(self):
        """Get the maximum number of retries"""
        return self.__retries
    
    def set_max_retries(self, retries):
        """Set the maximum number of retries"""
        self.__retries = max(0, retries)
    
    def get_current_retry(self):
        """Get the current retry attempt number"""
        return self.__current_retry
    
    def is_connecting(self):
        """Check if widget is in connecting state"""
        return self.connection_state == self.STATE_CONNECTING
    
    def is_connected(self):
        """Check if widget is in connected state"""
        return self.connection_state == self.STATE_CONNECTED
    
    def is_disconnected(self):
        """Check if widget is in disconnected state"""
        return self.connection_state == self.STATE_DISCONNECTED
    
    @pyqtSlot(float)
    def on_opacity_change(self, opacity):
        """Slot for opacity changes - changes widget background opacity but keeps text opaque"""
        # Convert opacity (0.0-1.0) to alpha value (0-255)
        alpha = int(opacity * 255)
        
        # Set background color with alpha for the widget
        self.setStyleSheet(f"""
            LiveConnectWidget {{
                background-color: rgba(50, 50, 50, {alpha});
                border-radius: 5px;
            }}
            QLabel {{
                background-color: transparent;
                color: rgba(255, 255, 255, 255);
            }}
            QLineEdit {{
                background-color: rgba(70, 70, 70, {alpha});
                color: rgba(255, 255, 255, 255);
                border: 1px solid rgba(100, 100, 100, {alpha});
                border-radius: 3px;
                padding: 2px;
            }}
            QPushButton {{
                background-color: rgba(80, 80, 80, {alpha});
                color: rgba(255, 255, 255, 255);
                border: 1px solid rgba(120, 120, 120, {alpha});
                border-radius: 3px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: rgba(100, 100, 100, {alpha});
            }}
        """)
    
    def set_title(self, title):
        """Change the widget title"""
        self.title = title
        self.title_label.setText(title)
