import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from src.processors.image_processor import ImageProcessor
from src.processors.url_processor import URLProcessor
from src.processors.analysis import AnalysisEngine

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('LOG_LEVEL', 'INFO')
)
logger = logging.getLogger(__name__)

class MedicalChartBot:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.url_processor = URLProcessor()
        self.analysis_engine = AnalysisEngine()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a welcome message when the command /start is issued."""
        welcome_message = (
            "👋 Welcome to the Medical Chart & Graph Interpretation Bot!\n\n"
            "I can help you analyze medical charts, graphs, and tables. Here's what I can do:\n\n"
            "🔹 Analyze uploaded images of medical charts\n"
            "🔹 Extract and analyze charts from research article URLs\n"
            "🔹 Provide technical medical insights\n\n"
            "Use /help to see all available commands."
        )
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a help message when the command /help is issued."""
        help_message = (
            "📚 Available Commands:\n\n"
            "🔸 /start - Start the bot\n"
            "🔸 /help - Show this help message\n"
            "🔸 /upload_graph - Upload a medical chart/graph for analysis\n"
            "🔸 /analyze_url <article_link> - Analyze charts from a research article\n\n"
            "To analyze a chart:\n"
            "1. Use /upload_graph\n"
            "2. Send your image\n"
            "3. Wait for the analysis results"
        )
        await update.message.reply_text(help_message)

    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process uploaded images."""
        try:
            # Get the largest available photo
            photo = update.message.photo[-1]
            
            # Notify user that processing has started
            processing_message = await update.message.reply_text(
                "🔄 Processing your medical chart... This may take a moment."
            )

            # Get the file and analyze it
            file = await context.bot.get_file(photo.file_id)
            analysis_result = await self.image_processor.process_image(file)
            
            # Generate insights using the analysis engine
            insights = await self.analysis_engine.generate_insights(analysis_result)
            
            # Format and send the response
            await processing_message.edit_text(insights)

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error while processing your image. "
                "Please try again or contact support if the issue persists."
            )

    async def analyze_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze charts from a provided URL."""
        try:
            # Get the URL from the command
            if not context.args:
                await update.message.reply_text(
                    "❌ Please provide a URL to analyze.\n"
                    "Example: /analyze_url https://example.com/article"
                )
                return

            url = context.args[0]
            
            # Notify user that processing has started
            processing_message = await update.message.reply_text(
                "🔄 Analyzing the article... This may take a moment."
            )

            # Process the URL and get charts
            charts = await self.url_processor.extract_charts(url)
            
            if not charts:
                await processing_message.edit_text(
                    "❌ No charts or graphs found in the provided URL."
                )
                return

            # Analyze each chart and compile results
            results = []
            for chart in charts:
                analysis = await self.analysis_engine.generate_insights(chart)
                results.append(analysis)

            # Format and send the combined analysis
            combined_analysis = "\n\n".join(results)
            await processing_message.edit_text(combined_analysis)

        except Exception as e:
            logger.error(f"Error processing URL: {str(e)}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error while analyzing the URL. "
                "Please make sure the URL is accessible and try again."
            )

def main():
    """Start the bot."""
    try:
        # Create the bot instance
        logger.info("Creating bot instance...")
        bot = MedicalChartBot()
        
        # Create the Application and pass it your bot's token
        logger.info("Initializing Telegram application...")
        application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

        # Add command handlers
        logger.info("Setting up command handlers...")
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("help", bot.help))
        application.add_handler(CommandHandler("analyze_url", bot.analyze_url))
        
        # Add message handlers
        logger.info("Setting up message handlers...")
        application.add_handler(MessageHandler(filters.PHOTO, bot.handle_image))

        # Start the Bot
        logger.info("Starting bot polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise

if __name__ == '__main__':
    main() 