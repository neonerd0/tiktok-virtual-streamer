from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QCheckBox, QLineEdit, QLabel, QSlider, QSpinBox,
                             QColorDialog, QPushButton, QComboBox, QScrollArea, QFileDialog)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt6.QtGui import QColor
from typing import Dict, Optional
from event_config import TikTokEventSettings, EventConfig
from .live_feed_widget import MessageType, MessageConfig


class SettingsWidget(QWidget):
    # Signals
    opacity_changed = pyqtSignal(float)
    event_settings_changed = pyqtSignal(str, EventConfig)  # event_name, config
    message_config_changed = pyqtSignal(MessageType, MessageConfig)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_settings: Optional[TikTokEventSettings] = None
        self.message_configs: Dict[MessageType, MessageConfig] = {}
        
        # Track UI elements for updates
        self.event_checkboxes: Dict[str, QCheckBox] = {}
        self.event_templates: Dict[str, QLineEdit] = {}
        self.event_message_types: Dict[str, QComboBox] = {}
        self.event_audio_files: Dict[str, QLineEdit] = {}
        self.event_audio_buttons: Dict[str, QPushButton] = {}
        
        self.message_color_buttons: Dict[MessageType, QPushButton] = {}
        self.message_font_sizes: Dict[MessageType, QSpinBox] = {}
        self.message_bold_checkboxes: Dict[MessageType, QCheckBox] = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the settings widget UI"""
        # Main layout with scroll area
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Create scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Opacity settings
        opacity_group = self.create_opacity_group()
        scroll_layout.addWidget(opacity_group)
        
        # Event settings
        event_group = self.create_event_settings_group()
        scroll_layout.addWidget(event_group)
        
        # Message config settings
        message_group = self.create_message_config_group()
        scroll_layout.addWidget(message_group)
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
    
    def create_opacity_group(self) -> QGroupBox:
        """Create opacity control group"""
        group = QGroupBox("Opacity Settings")
        layout = QVBoxLayout()
        
        # Opacity slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)  # Default to fully opaque
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        
        self.opacity_label = QLabel("100%")
        self.opacity_label.setMinimumWidth(40)
        
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        
        layout.addLayout(opacity_layout)
        group.setLayout(layout)
        return group
    
    def create_event_settings_group(self) -> QGroupBox:
        """Create event settings control group"""
        group = QGroupBox("Event Settings")
        layout = QVBoxLayout()
        
        # Event types to configure
        event_types = ['connect', 'comments', 'gifts', 'joins', 'viewer_count', 'follows']
        
        for event_name in event_types:
            event_layout = self.create_event_control(event_name)
            layout.addLayout(event_layout)
        
        group.setLayout(layout)
        return group
    
    def create_event_control(self, event_name: str) -> QVBoxLayout:
        """Create controls for a single event type"""
        layout = QVBoxLayout()
        
        # Event header with checkbox
        header_layout = QHBoxLayout()
        
        # Enable/disable checkbox
        checkbox = QCheckBox(f"Enable {event_name.replace('_', ' ').title()}")
        checkbox.setChecked(True)  # Default enabled
        checkbox.stateChanged.connect(lambda state, name=event_name: self.on_event_enabled_changed(name, state))
        self.event_checkboxes[event_name] = checkbox
        header_layout.addWidget(checkbox)
        
        layout.addLayout(header_layout)
        
        # Message template
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        
        template_edit = QLineEdit()
        template_edit.setPlaceholderText(f"Message template for {event_name}")
        template_edit.textChanged.connect(lambda text, name=event_name: self.on_template_changed(name, text))
        self.event_templates[event_name] = template_edit
        template_layout.addWidget(template_edit)
        
        layout.addLayout(template_layout)
        
        # Message type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Message Type:"))
        
        type_combo = QComboBox()
        type_combo.addItems([msg_type.value for msg_type in MessageType])
        type_combo.currentTextChanged.connect(lambda text, name=event_name: self.on_message_type_changed(name, text))
        self.event_message_types[event_name] = type_combo
        type_layout.addWidget(type_combo)
        
        layout.addLayout(type_layout)
        
        # Audio file selection
        audio_layout = QHBoxLayout()
        audio_layout.addWidget(QLabel("Audio Chime:"))
        
        audio_file_edit = QLineEdit()
        audio_file_edit.setPlaceholderText("Path to audio file (optional)")
        audio_file_edit.textChanged.connect(lambda text, name=event_name: self.on_audio_file_changed(name, text))
        self.event_audio_files[event_name] = audio_file_edit
        audio_layout.addWidget(audio_file_edit)
        
        audio_browse_button = QPushButton("Browse...")
        audio_browse_button.clicked.connect(lambda checked, name=event_name: self.on_browse_audio_file(name))
        self.event_audio_buttons[event_name] = audio_browse_button
        audio_layout.addWidget(audio_browse_button)
        
        layout.addLayout(audio_layout)
        
        # Add separator
        layout.addWidget(QLabel(""))  # Spacer
        
        return layout
    
    def create_message_config_group(self) -> QGroupBox:
        """Create message configuration control group"""
        group = QGroupBox("Message Appearance")
        layout = QVBoxLayout()
        
        for msg_type in MessageType:
            msg_layout = self.create_message_config_control(msg_type)
            layout.addLayout(msg_layout)
        
        group.setLayout(layout)
        return group
    
    def create_message_config_control(self, msg_type: MessageType) -> QVBoxLayout:
        """Create controls for a single message type configuration"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"{msg_type.value.title()} Messages")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)
        
        # Color selection
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        color_button = QPushButton("Choose Color")
        color_button.clicked.connect(lambda checked, mt=msg_type: self.on_color_button_clicked(mt))
        self.message_color_buttons[msg_type] = color_button
        color_layout.addWidget(color_button)
        
        layout.addLayout(color_layout)
        
        # Font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Font Size:"))
        
        size_spinbox = QSpinBox()
        size_spinbox.setMinimum(8)
        size_spinbox.setMaximum(24)
        size_spinbox.setValue(10)  # Default size
        size_spinbox.valueChanged.connect(lambda value, mt=msg_type: self.on_font_size_changed(mt, value))
        self.message_font_sizes[msg_type] = size_spinbox
        size_layout.addWidget(size_spinbox)
        
        layout.addLayout(size_layout)
        
        # Bold checkbox
        bold_checkbox = QCheckBox("Bold")
        bold_checkbox.stateChanged.connect(lambda state, mt=msg_type: self.on_bold_changed(mt, state))
        self.message_bold_checkboxes[msg_type] = bold_checkbox
        layout.addWidget(bold_checkbox)
        
        # Add separator
        layout.addWidget(QLabel(""))  # Spacer
        
        return layout
    
    @pyqtSlot(int)
    def on_opacity_changed(self, value: int):
        """Handle opacity slider changes"""
        opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.opacity_changed.emit(opacity)
    
    @pyqtSlot(int)
    def on_event_enabled_changed(self, event_name: str, state: int):
        """Handle event enable/disable changes"""
        enabled = state == Qt.CheckState.Checked.value
        if self.event_settings:
            self.event_settings.enable_event(event_name, enabled)
            config = self.event_settings.get_config(event_name)
            if config:
                self.event_settings_changed.emit(event_name, config)
    
    @pyqtSlot(str)
    def on_template_changed(self, event_name: str, text: str):
        """Handle message template changes"""
        if self.event_settings:
            self.event_settings.set_message_template(event_name, text)
            config = self.event_settings.get_config(event_name)
            if config:
                self.event_settings_changed.emit(event_name, config)
    
    @pyqtSlot(str)
    def on_message_type_changed(self, event_name: str, type_text: str):
        """Handle message type changes"""
        if self.event_settings:
            msg_type = MessageType(type_text)
            self.event_settings.set_message_type(event_name, msg_type)
            config = self.event_settings.get_config(event_name)
            if config:
                self.event_settings_changed.emit(event_name, config)
    
    @pyqtSlot(str)
    def on_audio_file_changed(self, event_name: str, file_path: str):
        """Handle audio file path changes"""
        if self.event_settings:
            self.event_settings.set_chime_audio_file(event_name, file_path if file_path.strip() else None)
            config = self.event_settings.get_config(event_name)
            if config:
                self.event_settings_changed.emit(event_name, config)
    
    def on_browse_audio_file(self, event_name: str):
        """Handle browse button clicks for audio file selection"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            f"Select Audio File for {event_name.replace('_', ' ').title()}",
            "audio/",  # Start in audio directory
            "Audio Files (*.mp3 *.wav *.ogg *.m4a *.flac);;All Files (*)"
        )
        
        if file_path:
            # Update the line edit with the selected file
            if event_name in self.event_audio_files:
                self.event_audio_files[event_name].setText(file_path)
    
    def on_color_button_clicked(self, msg_type: MessageType):
        """Handle color button clicks"""
        color = QColorDialog.getColor()
        if color.isValid():
            # Update button color
            button = self.message_color_buttons[msg_type]
            button.setStyleSheet(f"background-color: {color.name()};")
            
            # Update message config
            self.update_message_config(msg_type)
    
    @pyqtSlot(int)
    def on_font_size_changed(self, msg_type: MessageType, size: int):
        """Handle font size changes"""
        self.update_message_config(msg_type)
    
    @pyqtSlot(int)
    def on_bold_changed(self, msg_type: MessageType, state: int):
        """Handle bold checkbox changes"""
        self.update_message_config(msg_type)
    
    def update_message_config(self, msg_type: MessageType):
        """Update and emit message config changes"""
        # Get current values from UI
        color_button = self.message_color_buttons[msg_type]
        color = color_button.palette().button().color().name()
        
        font_size = self.message_font_sizes[msg_type].value()
        is_bold = self.message_bold_checkboxes[msg_type].isChecked()
        
        # Create new config
        config = MessageConfig(color=color, font_size=font_size, is_bold=is_bold)
        self.message_configs[msg_type] = config
        
        # Emit change signal
        self.message_config_changed.emit(msg_type, config)
    
    def set_event_settings(self, settings: TikTokEventSettings):
        """Set the event settings to configure"""
        self.event_settings = settings
        self.update_ui_from_settings()
    
    def set_message_configs(self, configs: Dict[MessageType, MessageConfig]):
        """Set the message configs to configure"""
        self.message_configs = configs.copy()
        self.update_ui_from_message_configs()
    
    def update_ui_from_settings(self):
        """Update UI controls from current event settings"""
        if not self.event_settings:
            return
        
        event_types = ['connect', 'comments', 'gifts', 'joins', 'viewer_count', 'follows']
        
        for event_name in event_types:
            config = self.event_settings.get_config(event_name)
            if config:
                # Update checkbox
                if event_name in self.event_checkboxes:
                    self.event_checkboxes[event_name].setChecked(config.enabled)
                
                # Update template
                if event_name in self.event_templates and config.message_template:
                    self.event_templates[event_name].setText(config.message_template)
                
                # Update message type
                if event_name in self.event_message_types:
                    self.event_message_types[event_name].setCurrentText(config.message_type.value)
                
                # Update audio file
                if event_name in self.event_audio_files and config.chime_audio_file:
                    self.event_audio_files[event_name].setText(config.chime_audio_file)
    
    def update_ui_from_message_configs(self):
        """Update UI controls from current message configs"""
        for msg_type, config in self.message_configs.items():
            # Update color button
            if msg_type in self.message_color_buttons:
                button = self.message_color_buttons[msg_type]
                button.setStyleSheet(f"background-color: {config.color};")
            
            # Update font size
            if msg_type in self.message_font_sizes:
                self.message_font_sizes[msg_type].setValue(config.font_size)
            
            # Update bold checkbox
            if msg_type in self.message_bold_checkboxes:
                self.message_bold_checkboxes[msg_type].setChecked(config.is_bold)
    
    def get_opacity(self) -> float:
        """Get current opacity value"""
        return self.opacity_slider.value() / 100.0
    
    def set_opacity(self, opacity: float):
        """Set opacity value"""
        value = int(opacity * 100)
        self.opacity_slider.setValue(value)
