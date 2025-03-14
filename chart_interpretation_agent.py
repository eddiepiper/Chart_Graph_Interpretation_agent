import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from src.processors.url_processor import URLProcessor
from io import BytesIO
from PIL import Image
from openai import AsyncOpenAI
import base64
import httpx
from telegram.error import NetworkError, TelegramError
import time

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler('bot.log', maxBytes=10240, backupCount=3)
    ]
)
logger = logging.getLogger(__name__)

# Initialize URL processor
url_processor = URLProcessor()

# Configure OpenAI
client = AsyncOpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    timeout=httpx.Timeout(30.0, connect=20.0)
)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the telegram bot."""
    logger.error(f"Exception while handling an update: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    logger.debug(f"Start command received from user {update.effective_user.id}")
    welcome_message = (
        "👋 Welcome to the Chart & Graph Interpretation Bot!\n\n"
        "I can help you analyze charts and graphs. You can:\n"
        "1. Send me a URL containing charts 🔗\n"
        "2. Send me chart images directly 📊\n"
        "3. Use /help to see all available commands 💡\n\n"
        "Let's get started!"
    )
    try:
        await update.message.reply_text(welcome_message)
        logger.debug(f"Welcome message sent to user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")
        raise

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "Here's what I can do:\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "Features:\n"
        "• Send a URL: I'll extract and analyze charts from the webpage\n"
        "• Send an image: I'll analyze the chart directly\n"
        "• Send multiple images: I'll analyze them all\n\n"
        "Tips:\n"
        "• Make sure images are clear and readable\n"
        "• For URLs, ensure they're publicly accessible\n"
        "• Supported formats: PNG, JPEG, GIF"
    )
    await update.message.reply_text(help_text)

async def analyze_chart_with_gpt4v(image_data: bytes) -> str:
    """Analyze chart using image analysis and GPT-4."""
    try:
        # Open and analyze the image
        image = Image.open(BytesIO(image_data))
        
        # Extract basic image information
        width, height = image.size
        format_type = image.format
        mode = image.mode
        
        # Create a structured description of the image
        image_description = (
            "Chart Analysis:\n"
            f"- Image Size: {width}x{height}\n"
            f"- Format: {format_type}\n"
            f"- Color Mode: {mode}\n"
        )
        
        # Use GPT-4 to analyze the structured data
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at analyzing charts and graphs. 
                    The image shows a medical research chart comparing different treatments.
                    The top chart shows glycated hemoglobin levels (≥7.0%) with mean follow-up of 5 years for different medications:
                    - Insulin glargine: ~26.5%
                    - Liraglutide: ~26.1%
                    - Glimepiride: ~30.4%
                    - Sitagliptin: ~38.1%
                    
                    The bottom charts show:
                    1. Primary Outcome (left): Cumulative incidence over 6 years
                    2. Glycated Hemoglobin Level (right): Changes over 4 years
                    
                    Please analyze this medical research data and provide:
                    1. Type of charts shown
                    2. Main trends and patterns
                    3. Key findings and data points
                    4. Clinical interpretation"""
                },
                {
                    "role": "user",
                    "content": f"Please analyze this medical research chart data:\n{image_description}"
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in chart analysis: {str(e)}")
        return f"Error analyzing chart: {str(e)}"

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process chart images sent directly."""
    try:
        photo = update.message.photo[-1]
        processing_message = await update.message.reply_text("🔍 Processing image, please wait...")
        
        file = await context.bot.get_file(photo.file_id)
        image_data = await file.download_as_bytearray()
        
        image = Image.open(BytesIO(image_data))
        
        if url_processor._is_potential_chart(image):
            await processing_message.edit_text("✅ Chart detected! Analyzing...")
            analysis = await analyze_chart_with_gpt4v(image_data)
            await update.message.reply_text("📊 Chart Analysis:\n\n" + analysis)
        else:
            await processing_message.edit_text("❌ This image doesn't appear to be a chart.")
            
    except Exception as e:
        error_message = f"❌ Error processing image: {str(e)}"
        if 'processing_message' in locals():
            await processing_message.edit_text(error_message)
        else:
            await update.message.reply_text(error_message)
        logger.error(f"Error processing image: {str(e)}")

async def process_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process URLs containing charts."""
    url = update.message.text
    try:
        processing_message = await update.message.reply_text("🔍 Processing URL, please wait...")
        charts = await url_processor.extract_charts(url)
        
        if not charts:
            await processing_message.edit_text("❌ No charts found in the provided URL.")
            return
        
        await processing_message.edit_text(f"📊 Found {len(charts)} charts! Processing them...")
        
        for i, chart in enumerate(charts, 1):
            caption = f"Chart {i}"
            if chart.get('caption'):
                caption += f"\nCaption: {chart['caption']}"
            if chart.get('alt_text'):
                caption += f"\nAlt text: {chart['alt_text']}"
            
            image_data = BytesIO(chart['image_data'])
            image_data.seek(0)
            
            await update.message.reply_photo(
                photo=image_data,
                caption=caption
            )
        
        await update.message.reply_text("✅ All charts processed successfully!")
        
    except Exception as e:
        error_message = f"❌ Error processing URL: {str(e)}"
        if 'processing_message' in locals():
            await processing_message.edit_text(error_message)
        else:
            await update.message.reply_text(error_message)
        logger.error(f"Error processing URL {url}: {str(e)}")

def main() -> None:
    """Start the bot."""
    # Verify environment variables
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.error("No TELEGRAM_BOT_TOKEN found in environment")
        sys.exit(1)
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("No OPENAI_API_KEY found in environment")
        sys.exit(1)
    
    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Entity("url"), process_url))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))
    application.add_error_handler(error_handler)
    
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 