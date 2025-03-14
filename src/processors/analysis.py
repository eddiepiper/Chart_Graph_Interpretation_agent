import logging
from typing import Dict, Any
import openai
import os
import base64
from PIL import Image
import io

logger = logging.getLogger(__name__)

class AnalysisEngine:
    def __init__(self):
        """Initialize the analysis engine."""
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    async def generate_insights(self, data: Dict[str, Any]) -> str:
        """
        Generate insights from chart data using OpenAI.
        
        Args:
            data: Dictionary containing chart data and analysis
            
        Returns:
            String containing generated insights
        """
        try:
            # Prepare the prompt based on chart type and data
            prompt = self._prepare_prompt(data)
            
            # Prepare the image if available
            image_content = None
            if 'image' in data and isinstance(data['image'], Image.Image):
                # Convert PIL Image to base64
                buffered = io.BytesIO()
                data['image'].save(buffered, format="PNG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                image_content = f"data:image/png;base64,{image_base64}"

            # Prepare messages for the API
            messages = [
                {
                    "role": "system",
                    "content": "You are a medical data analysis expert specializing in interpreting medical charts and graphs. Provide clear, concise, and accurate interpretations of the data presented."
                }
            ]

            # Add the image and prompt as user message
            if image_content:
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": image_content
                        }
                    ]
                })
            else:
                messages.append({
                    "role": "user",
                    "content": prompt
                })
            
            # Generate insights using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract and format the insights
            insights = response.choices[0].message.content
            
            # Add statistical significance information if available
            if data.get('statistical_data'):
                insights += self._format_statistical_data(data['statistical_data'])
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return "Sorry, I encountered an error while analyzing the data. Please try again."

    def _prepare_prompt(self, data: Dict[str, Any]) -> str:
        """Prepare the prompt for OpenAI based on the data."""
        chart_type = data.get('chart_type', 'unknown')
        text_data = data.get('text_data', [])
        numerical_data = data.get('numerical_data', {})
        
        prompt = f"Please analyze this {chart_type} chart. "
        
        # Add extracted text information
        if text_data:
            prompt += "\n\nExtracted text:\n"
            for item in text_data:
                prompt += f"- {item['text']} (confidence: {item['confidence']})\n"
        
        # Add numerical data information
        if numerical_data:
            prompt += f"\n\nNumerical data type: {numerical_data.get('type', 'unknown')}"
        
        prompt += "\n\nPlease provide:\n1. A clear interpretation of the main findings\n2. Any notable trends or patterns\n3. Clinical implications if applicable"
        
        return prompt

    def _format_statistical_data(self, stats: Dict[str, Any]) -> str:
        """Format statistical data into a readable string."""
        formatted = "\n\nStatistical Information:"
        
        if stats.get('p_value'):
            formatted += f"\n- P-value: {stats['p_value']}"
        
        if stats.get('confidence_interval'):
            formatted += f"\n- Confidence Interval: {stats['confidence_interval']}"
        
        if stats.get('hazard_ratio'):
            formatted += f"\n- Hazard Ratio: {stats['hazard_ratio']}"
        
        if stats.get('odds_ratio'):
            formatted += f"\n- Odds Ratio: {stats['odds_ratio']}"
        
        return formatted 