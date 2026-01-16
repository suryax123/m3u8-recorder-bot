# 🎥 M3U8 Stream Recorder Bot

A powerful Telegram bot for recording live M3U8 streams with scheduling capabilities. Built with Python, Telethon, and FFmpeg.

## ✨ Features

- 🎬 **M3U8 Stream Recording** - Record live streams with robust error handling
- ⏰ **Scheduling** - Schedule recordings with start/end times
- 📤 **Auto Upload** - Automatically uploads recordings to Telegram
- ⏹️ **Cancellation** - Cancel active or scheduled recordings anytime
- 📊 **Progress Tracking** - Real-time upload progress with status updates
- 🔄 **Resilient** - Automatic reconnection and retry mechanisms
- 📺 **Quality Control** - 480p output @ 800kbps for optimal file sizes
- 💾 **Efficient Storage** - Temporary MKV recording, converted to MP4 with fast-start

## 🛠️ Technology Stack

- **Python 3.11+**
- **Telethon** - Async Telegram client library
- **FFmpeg** - Stream recording and conversion
- **asyncio** - Asynchronous task management
- **Docker** - Containerized deployment

## 📋 Prerequisites

- Python 3.11 or higher
- FFmpeg installed on your system
- Telegram API credentials (API_ID, API_HASH)
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

## 🚀 Quick Start

### Method 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/suryax123/m3u8-recorder-bot.git
   cd m3u8-recorder-bot
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

3. **Start the bot**
   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

### Method 2: Manual Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/suryax123/m3u8-recorder-bot.git
   cd m3u8-recorder-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg**
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

5. **Configure environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

6. **Run the bot**
   ```bash
   python bot.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram API Credentials (from https://my.telegram.org/apps)
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_from_botfather

# Optional: Custom recording path
RECORDING_PATH=./recordings
```

### Getting Telegram Credentials

1. **API_ID & API_HASH**
   - Visit https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Copy the `api_id` and `api_hash`

2. **BOT_TOKEN**
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow the prompts
   - Copy the bot token provided

## 📱 Usage

### Starting the Bot

1. Open Telegram and find your bot
2. Send `/start` or `/menu`
3. Use the interactive buttons to create a recording

### Recording a Stream

1. **Click "🎬 New Recording"**
2. **Enter Stream URL** (M3U8, YouTube, or direct stream)
3. **Enter Start Time** (Format: HH:MM, 24-hour)
4. **Enter End Time** (Format: HH:MM, 24-hour)
5. **Confirm** - The bot will schedule and record automatically

### Commands

- `/start` - Start the bot and show main menu
- `/menu` - Show main menu
- `/cancel` - Cancel active recording or scheduled job

### Interactive Buttons

- **🎬 New Recording** - Create a new recording
- **⏹ Cancel Job** - Cancel active/scheduled recording
- **ℹ️ Status** - Check recording status

## 📁 Project Structure

```
m3u8-recorder-bot/
├── bot.py              # Main bot logic with event handlers
├── config.py           # Configuration and Telegram client initialization
├── utils.py            # Recording utilities and FFmpeg handling
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
├── Dockerfile          # Docker container configuration
├── docker-compose.yml  # Docker Compose setup
└── README.md           # This file
```

### File Descriptions

#### `bot.py`
Main application file containing:
- Event handlers for bot commands
- Recording state management
- Scheduling logic
- User interaction flow

#### `config.py`
Configuration module with:
- Environment variable loading
- Telegram client initialization
- Directory setup

#### `utils.py`
Utility functions for:
- Async stream recording with FFmpeg
- File conversion (MKV to MP4)
- Cleanup operations
- Cancellation handling

## 🎯 Features Explained

### Scheduling System
- **Smart Date Handling** - Automatically handles next-day recordings
- **Duration Validation** - Maximum 12-hour recordings
- **Delayed Start** - Schedule recordings in advance

### Recording Process
1. **Stream Capture** - FFmpeg records to temporary MKV file
2. **Progress Monitoring** - Real-time status updates
3. **Conversion** - MKV converted to MP4 with fast-start
4. **Upload** - File uploaded to Telegram with progress bar
5. **Cleanup** - Temporary files automatically removed

### Error Handling
- Stream connection failures
- Network interruptions
- Invalid URLs
- Timeout protection
- Graceful cancellation

## 🔧 Troubleshooting

### Bot Not Starting
```bash
# Check logs
docker-compose logs -f

# Verify credentials
cat .env
```

### Recording Fails
- Verify FFmpeg is installed: `ffmpeg -version`
- Check stream URL is accessible
- Ensure sufficient disk space
- Check file permissions in `RECORDING_PATH`

### Upload Fails
- Check Telegram API limits (2GB file size)
- Verify bot has send_files permission
- Check network connectivity

## 🐛 Development

### Running in Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run with debug output
python bot.py
```

### Testing Stream Recording

```python
# Test utils module independently
from utils import record_stream_async

# Test recording
await record_stream_async(
    "https://example.com/stream.m3u8",
    duration_minutes=1,
    filename="test_recording",
    cancel_event=None
)
```

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 💡 Tips

- Use M3U8 playlist URLs for best results
- Schedule recordings at least 1 minute in advance
- Keep recording duration under 6 hours for stability
- Monitor disk space in `RECORDING_PATH`
- Use Docker for production deployments

## 📧 Support

If you encounter any issues:
1. Check the troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Open an issue on GitHub

## ⚠️ Disclaimer

This bot is for personal use only. Ensure you have the right to record and distribute any content. Respect copyright laws and streaming service terms of service.

---

Made with ❤️ by [suryax123](https://github.com/suryax123)