# Telegram Spam Filter Bot

AI-powered Telegram bot that automatically detects and removes financial spam using Google Gemini API.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API keys

- **Telegram Bot Token**: Message [@BotFather](https://t.me/botfather) → `/newbot`
- **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 3. Configure environment

Create `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_key
```

### 4. Add bot to channel

1. Add bot to your Telegram channel
2. Promote to admin with "Delete messages" permission
3. For groups: disable Privacy Mode via @BotFather (`/setprivacy`)

## Usage

```bash
python bot.py
```

The bot monitors channel posts and automatically deletes spam with >80% confidence.

## Configuration

Adjust spam detection threshold in `bot.py`:

```python
return result.get('is_spam', False) and result.get('confidence', 0) > 80
```

## Troubleshooting

**Bot can't delete messages**: Make sure bot is admin with delete permission

**Bot not seeing messages**:
- Channels: bot must be admin
- Groups: disable Privacy Mode via @BotFather

**API errors**: Verify keys in `.env` and check [API quota](https://aistudio.google.com/)

## License

MIT
