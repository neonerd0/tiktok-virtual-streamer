#!/usr/bin/env python3
"""
TikTok Live Overlay Launcher

This script launches the Qt overlay application for monitoring TikTok Live streams.
The overlay will stay always on top and display real-time stream information.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from minimal_overlay import main

if __name__ == "__main__":
    print("🎥 Starting TikTok Live Minimal Overlay...")
    print("📋 Features:")
    print("   • Minimal always-on-top overlay")
    print("   • Single HTML-formatted text display")
    print("   • Streamer mode toggle")
    print("   • Customizable text colors & font sizes")
    print("   • VIP fan highlighting")
    print("   • Background opacity control")
    print("   • Draggable & resizable window")
    print()
    print("🎮 Controls:")
    print("   • Toggle 'Streamer Mode' to hide/show settings")
    print("   • Enter TikTok username and click 'Connect'")
    print("   • Drag center area to move window")
    print("   • Drag edges/corners to resize window")
    print("   • Click 'Settings' for customization")
    print("   • Click 'Clear' to clear display")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Overlay closed by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")
