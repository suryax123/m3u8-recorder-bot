# 🎥 M3U8 Stream Recorder Bot

A powerful Telegram bot for recording live streams (M3U8, HLS, and more) with scheduled recording capabilities. Built with Python, Telethon, and FFmpeg.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg?logo=telegram)

## ✨ Features

- 📹 **M3U8/HLS Stream Recording** - Record live streams with automatic reconnection
- ⏰ **Scheduled Recordings** - Set start and end times for automated recording
- 🔄 **Robust Stream Handling** - Automatic retry/reconnect for unstable streams
- 📤 **Direct Telegram Upload** - Recorded files uploaded directly to your chat
- ⚙️ **Quality Settings** - Optimized for 480p with low bandwidth (configurable)
- 🛑 **Cancellation Support** - Cancel active or scheduled recordings anytime
- 📊 **Status Tracking** - Check recording progress in real-time
- 💾 **Automatic Cleanup** - Removes temporary files after upload

## 📋 Requirements

- Python 3.9 or higher
- FFmpeg installed on your system
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Telegram API credentials (from [my.telegram.org](https://my.telegram.org))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/suryax123/m3u8-recorder-bot.git
cd m3u8-recorder-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
RECORDING_PATH=./recordings
```

### 5. Run the Bot

```bash
python bot.py
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Using Docker Only

```bash
# Build
docker build -t m3u8-recorder-bot .

# Run
docker run -d \
  --name m3u8-bot \
  -v $(pwd)/recordings:/app/recordings \
  --env-file .env \
  m3u8-recorder-bot
```

## 📖 Usage

### Bot Commands

- `/start` or `/menu` - Show main menu
- `/cancel` - Cancel active or scheduled recording

### Recording Workflow

1. **Start the bot** - Send `/start` to the bot
2. **New Recording** - Click "New Recording" button
3. **Enter Stream URL** - Send the M3U8/HLS stream URL
4. **Set Start Time** - Enter start time in `HH:MM` format (e.g., `14:30`)
5. **Set End Time** - Enter end time in `HH:MM` format (e.g., `15:30`)
6. **Confirm** - Review and confirm the recording schedule
7. **Wait** - Bot will start recording at the scheduled time
8. **Receive File** - Recorded video will be uploaded to your chat

### Example Stream URLs

```
# Direct M3U8
https://example.com/live/stream.m3u8

# HLS Stream
https://example.com/playlist.m3u8

# YouTube Live (requires youtube-dl/yt-dlp)
https://youtube.com/watch?v=xxxxx
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `API_ID` | Telegram API ID from my.telegram.org | ✅ Yes | - |
| `API_HASH` | Telegram API Hash from my.telegram.org | ✅ Yes | - |
| `BOT_TOKEN` | Bot token from @BotFather | ✅ Yes | - |
| `RECORDING_PATH` | Directory to store recordings | ❌ No | `./recordings` |

### Recording Settings

Edit `utils.py` to customize FFmpeg settings:

- **Video Quality**: Change `-crf`, `-maxrate`, `-bufsize`
- **Resolution**: Modify `-vf scale=-2:480` (currently 480p)
- **Audio Bitrate**: Adjust `-b:a 96k`
- **Reconnection**: Tweak `-reconnect_delay_max`

## 🛠️ Advanced Configuration

### Multi-User Support

Current implementation supports one recording per user. To enable multiple simultaneous recordings:

```python
# In bot.py, modify active_recordings to use unique keys
active_recordings: Dict[str, ActiveRecording] = {}

# Use unique key: f"{chat_id}_{timestamp}"
```

### Custom Video Profiles

Create quality presets in `utils.py`:

```python
QUALITY_PRESETS = {
    "low": {"crf": 28, "maxrate": "800k", "scale": "480"},
    "medium": {"crf": 23, "maxrate": "1500k", "scale": "720"},
    "high": {"crf": 20, "maxrate": "3000k", "scale": "1080"}
}
```

## 📁 Project Structure

```
m3u8-recorder-bot/
├── bot.py              # Main bot logic and event handlers
├── config.py           # Configuration and Telegram client
├── utils.py            # Stream recording utilities
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
├── Dockerfile          # Docker container definition
├── docker-compose.yml  # Docker Compose configuration
├── README.md           # This file
└── recordings/         # Recorded files (auto-created)
```

## 🐛 Troubleshooting

### "Recording failed. Stream may be unavailable"

- Verify the stream URL is accessible
- Check if the stream requires authentication
- Test the URL with: `ffmpeg -i "URL" -t 10 test.mp4`

### "Connection failed"

- Verify API credentials in `.env`
- Check internet connection
- Ensure Telegram isn't blocking your IP

### FFmpeg Errors

- Ensure FFmpeg is installed: `ffmpeg -version`
- Check FFmpeg has permissions to write to `RECORDING_PATH`
- Review error logs in bot console

### Upload Failed

- Telegram file size limit is 2GB (4GB for Premium)
- For large files, reduce recording duration or quality
- Consider using external upload services

## 🔒 Security Notes

- **Never commit `.env`** - Contains sensitive credentials
- **Restrict bot access** - Use Telegram privacy settings
- **Secure recording path** - Ensure directory has appropriate permissions
- **Monitor disk space** - Recordings can be large

## 📝 Limitations

- One active recording per user
- Maximum recording duration: 12 hours
- Telegram upload limit: 2GB (or 4GB with Premium)
- Requires constant internet connection
- FFmpeg must be available in PATH

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram client library
- [FFmpeg](https://ffmpeg.org/) - Video processing
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment management

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/suryax123/m3u8-recorder-bot/issues)
- **Telegram**: [@suryax123](https://t.me/suryax123)

## 🗺️ Roadmap

- [ ] Multi-recording support per user
- [ ] Quality selection menu
- [ ] Automatic stream discovery
- [ ] Database for recording history
- [ ] Admin panel for monitoring
- [ ] Webhook support for CI/CD integration
- [ ] Custom watermark support
- [ ] Subtitle/caption support
- [ ] Cloud storage integration (S3, GCS)

---

**Made with ❤️ for the streaming community**
