#!/usr/bin/env python3
"""
Setup script for the Exam Notification Bot
"""

import os
import sys

def setup_environment():
    """Set up the environment for the bot"""
    print("🔧 Setting up Exam Notification Bot...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        with open('env.example', 'r') as example:
            content = example.read()
        with open('.env', 'w') as env_file:
            env_file.write(content)
        print("✅ .env file created! Please edit it with your bot token.")
    else:
        print("✅ .env file already exists")
    
    # Check if database exists
    if not os.path.exists('exams.db'):
        print("🗄️ Database will be created on first run")
    else:
        print("✅ Database already exists")
    
    print("\n🚀 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your Telegram bot token")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the bot: python bot.py")

if __name__ == "__main__":
    setup_environment()
