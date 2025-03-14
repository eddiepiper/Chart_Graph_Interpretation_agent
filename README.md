# Chart & Graph Interpretation Bot

A Telegram bot that analyzes charts and graphs using advanced image processing and GPT-4. The bot can extract charts from URLs and analyze images sent directly to it.

## Features

- 📊 Analyze charts and graphs sent as images
- 🔗 Extract and analyze charts from web pages via URL
- 📈 Support for multiple chart types (bar charts, line graphs, etc.)
- 🤖 Powered by GPT-4 for intelligent analysis
- 📝 Detailed analysis including:
  - Chart type identification
  - Main trends and patterns
  - Key data points
  - Overall interpretation

## Prerequisites

- Python 3.9+
- Telegram Bot Token
- OpenAI API Key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Chart-Graph-Interpretation-Agent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
LOG_LEVEL=INFO
```

## Usage

1. Start the bot:
```bash
python telegram_bot.py
```

2. In Telegram, search for your bot and start a conversation

3. Available commands:
- `/start` - Initialize the bot
- `/help` - Show help message

4. Features:
- Send an image of a chart directly to the bot for analysis
- Send a URL containing charts for extraction and analysis
- Receive detailed analysis of charts including type, trends, and interpretation

## Project Structure

```
.
├── src/
│   └── processors/
│       └── url_processor.py    # URL processing and chart extraction
├── tests/
│   └── test_url_processor.py  # Unit tests
├── telegram_bot.py            # Main bot implementation
├── requirements.txt           # Project dependencies
└── .env                      # Environment variables
```

## Development

- The bot uses asynchronous programming for efficient handling of requests
- Implements error handling and logging
- Supports multiple image formats (PNG, JPEG, GIF)
- Includes test suite for URL processing functionality

## Error Handling

The bot includes comprehensive error handling for:
- Network connectivity issues
- Invalid URLs or images
- API rate limits
- Server errors

## Logging

Logs are stored in `bot.log` with rotation enabled:
- Maximum log file size: 10KB
- Keeps up to 3 backup files
- Debug level logging for development

## Security Notes

- Never commit your `.env` file
- Regularly rotate your API keys
- Use environment variables for sensitive data
- Monitor API usage and costs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 