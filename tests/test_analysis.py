import pytest
import pytest_asyncio
import asyncio
from src.processors.analysis import AnalysisEngine
from unittest.mock import Mock, patch
import json
from PIL import Image
import io
import numpy as np

class TestAnalysisEngine:
    @pytest_asyncio.fixture
    async def engine(self):
        """Fixture to create AnalysisEngine instance."""
        engine = AnalysisEngine()
        return engine

    @pytest.fixture
    def sample_chart_data(self):
        """Fixture to provide sample chart data."""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        test_image = Image.open(img_byte_arr)

        return {
            'chart_type': 'line_graph',
            'image': test_image,
            'text_data': [
                {'text': 'Survival Rate', 'confidence': 0.95},
                {'text': '80%', 'confidence': 0.98},
                {'text': 'p < 0.001', 'confidence': 0.99}
            ],
            'numerical_data': {
                'type': 'numerical',
                'min': 0,
                'max': 100,
                'mean': 50,
                'count': 10
            },
            'statistical_data': {
                'p_value': 'p < 0.001',
                'confidence_interval': '95% CI: 0.75-0.85',
                'hazard_ratio': 'HR: 1.5',
                'odds_ratio': None
            }
        }

    @pytest.mark.asyncio
    async def test_initialization(self, engine):
        """Test if the AnalysisEngine initializes correctly."""
        assert engine is not None
        assert engine.openai_client is not None

    @pytest.mark.asyncio
    @patch('openai.OpenAI')
    async def test_generate_insights_basic(self, mock_openai, engine, sample_chart_data):
        """Test basic insight generation."""
        # Mock OpenAI response
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="Test insights"))]
        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        insights = await engine.generate_insights(sample_chart_data)
        assert isinstance(insights, str)
        assert len(insights) > 0

    @pytest.mark.asyncio
    @patch('openai.OpenAI')
    async def test_generate_insights_no_image(self, mock_openai, engine):
        """Test insight generation without image data."""
        data = {
            'chart_type': 'unknown',
            'text_data': [],
            'numerical_data': {'type': 'unknown'},
            'statistical_data': {}
        }

        insights = await engine.generate_insights(data)
        assert isinstance(insights, str)
        assert "error" in insights.lower() or "unable to analyze" in insights.lower()

    @pytest.mark.asyncio
    @patch('openai.OpenAI')
    async def test_generate_insights_with_statistics(self, mock_openai, engine, sample_chart_data):
        """Test insight generation with statistical data."""
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="Statistical analysis results"))]
        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        insights = await engine.generate_insights(sample_chart_data)
        assert isinstance(insights, str)
        assert len(insights) > 0

    @pytest.mark.asyncio
    async def test_prepare_prompt(self, engine, sample_chart_data):
        """Test prompt preparation."""
        prompt = engine._prepare_prompt(sample_chart_data)
        assert isinstance(prompt, str)
        assert 'line_graph' in prompt.lower()
        assert 'survival rate' in prompt.lower()
        assert 'p < 0.001' in prompt.lower()

    @pytest.mark.asyncio
    async def test_format_statistical_data(self, engine, sample_chart_data):
        """Test statistical data formatting."""
        formatted = engine._format_statistical_data(sample_chart_data['statistical_data'])
        assert isinstance(formatted, str)
        assert 'p < 0.001' in formatted
        assert '95% CI' in formatted
        assert 'HR: 1.5' in formatted

    @pytest.mark.asyncio
    @patch('openai.OpenAI')
    async def test_error_handling(self, mock_openai, engine, sample_chart_data):
        """Test error handling in insight generation."""
        # Test API error
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
        insights = await engine.generate_insights(sample_chart_data)
        assert "error" in insights.lower()

        # Test invalid data
        invalid_data = {}
        insights = await engine.generate_insights(invalid_data)
        assert "error" in insights.lower()

    @pytest.mark.asyncio
    @patch('openai.OpenAI')
    async def test_different_chart_types(self, mock_openai, engine, sample_chart_data):
        """Test insight generation for different chart types."""
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="Chart specific insights"))]
        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        chart_types = ['bar_chart', 'scatter_plot', 'kaplan_meier']
        for chart_type in chart_types:
            data = sample_chart_data.copy()
            data['chart_type'] = chart_type
            insights = await engine.generate_insights(data)
            assert isinstance(insights, str)
            assert len(insights) > 0

    @pytest.mark.asyncio
    @patch('openai.OpenAI')
    async def test_image_handling(self, mock_openai, engine):
        """Test handling of different image formats and sizes."""
        # Test with different image sizes
        sizes = [(100, 100), (800, 600), (1920, 1080)]
        for width, height in sizes:
            img = Image.new('RGB', (width, height), color='white')
            data = {
                'chart_type': 'line_graph',
                'image': img,
                'text_data': [],
                'numerical_data': {'type': 'numerical'},
                'statistical_data': {}
            }
            mock_completion = Mock()
            mock_completion.choices = [Mock(message=Mock(content="Image size test"))]
            mock_openai.return_value.chat.completions.create.return_value = mock_completion
            
            insights = await engine.generate_insights(data)
            assert isinstance(insights, str)
            assert len(insights) > 0 