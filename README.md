# Chart & Graph Interpretation Agent

An AI-powered agent that analyzes charts and graphs using advanced image processing and GPT-4. The agent can extract charts from URLs and analyze images sent directly through a Telegram interface.

## Features

- 📊 Analyze charts and graphs sent as images
- 🔗 Extract and analyze charts from web pages via URL
- 📈 Support for multiple chart types:
  - Bar charts
  - Line graphs
  - Scatter plots
  - Area charts
  - Pie charts
- 🤖 Powered by GPT-4 for intelligent analysis
- 📝 Detailed analysis including:
  - Chart type identification
  - Main trends and patterns
  - Key data points
  - Overall interpretation

## Prerequisites

- Python 3.9+
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- OpenAI API Key with GPT-4 access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/eddiepiper/Chart_Graph_Interpretation_agent.git
cd Chart_Graph_Interpretation_agent
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

1. Start the agent:
```bash
python chart_interpretation_agent.py
```

2. In Telegram, search for your bot and start a conversation

3. Available commands:
- `/start` - Initialize the agent
- `/help` - Show help message

4. Features:
- Send an image of a chart directly to the agent for analysis
- Send a URL containing charts for extraction and analysis
- Receive detailed analysis including chart type, trends, and interpretation

## Project Structure

```
.
├── src/
│   └── processors/
│       ├── __init__.py
│       ├── url_processor.py     # URL processing and chart extraction
│       ├── image_processor.py   # Image analysis and chart detection
│       └── analysis.py         # Chart analysis logic
├── tests/
│   ├── test_url_processor.py   # URL processor tests
│   ├── test_image_processor.py # Image processor tests
│   └── test_analysis.py       # Analysis tests
├── chart_interpretation_agent.py # Main agent implementation
├── requirements.txt            # Project dependencies
└── .env                       # Environment variables
```

## Development

The agent uses:
- Asynchronous programming for efficient request handling
- Comprehensive error handling and logging
- Multiple image format support (PNG, JPEG, GIF)
- Test suite for all major components
- Docker support for containerized deployment

## Error Handling

Comprehensive error handling for:
- Network connectivity issues
- Invalid URLs or images
- API rate limits and timeouts
- Server errors
- Image processing failures

## Logging

Logs are stored in `bot.log` with rotation enabled:
- Maximum log file size: 10KB
- Keeps up to 3 backup files
- Debug level logging for development

## Deployment Options

1. Local Deployment:
```bash
python chart_interpretation_agent.py
```

2. Docker Deployment:
```bash
docker build -t chart-agent .
docker run -d --env-file .env chart-agent
```

3. Linux Server (systemd):
```bash
sudo cp deployment/chart-bot.service /etc/systemd/system/
sudo systemctl enable chart-bot
sudo systemctl start chart-bot
```

## Security Notes

- Never commit your `.env` file
- Regularly rotate your API keys
- Use environment variables for sensitive data
- Monitor API usage and costs
- Keep dependencies updated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 