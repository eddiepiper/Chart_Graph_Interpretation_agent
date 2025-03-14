import pytest
import pytest_asyncio
import asyncio
import os
from PIL import Image
import io
import numpy as np
from src.processors.image_processor import ImageProcessor, InvalidImageError, OCRError, ImageProcessingError
import matplotlib.pyplot as plt

@pytest.mark.asyncio
class TestImageProcessor:
    @pytest_asyncio.fixture
    async def processor(self):
        """Fixture to create ImageProcessor instance."""
        processor = ImageProcessor()
        return processor
        
    def create_test_image(self, width=100, height=100, color='white'):
        """Helper method to create a test image."""
        img = Image.new('RGB', (width, height), color=color)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()
        
    def create_chart_image(self):
        """Helper method to create a simple line chart for testing."""
        plt.figure(figsize=(8, 6))
        plt.plot([1, 2, 3, 4], [1, 4, 2, 3])
        plt.title("Test Chart")
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")
        
        img_byte_arr = io.BytesIO()
        plt.savefig(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        plt.close()
        return img_byte_arr.getvalue()

    @pytest.mark.asyncio
    async def test_initialization(self, processor):
        """Test if the ImageProcessor initializes correctly."""
        assert processor is not None
        assert processor.reader is not None

    @pytest.mark.asyncio
    async def test_bytes_to_cv2(self, processor):
        """Test conversion from bytes to CV2 image."""
        test_image = self.create_test_image()
        cv2_image = processor._bytes_to_cv2(test_image)
        assert cv2_image is not None
        assert cv2_image.shape[2] == 3  # RGB channels

    @pytest.mark.asyncio
    async def test_detect_chart_type(self, processor):
        """Test chart type detection."""
        chart_image = self.create_chart_image()
        cv2_image = processor._bytes_to_cv2(chart_image)
        chart_type = processor._detect_chart_type(cv2_image)
        assert chart_type in ['line_graph', 'bar_chart', 'scatter_plot', 'kaplan_meier', 'unknown']

    @pytest.mark.asyncio
    async def test_extract_text(self, processor):
        """Test text extraction from chart."""
        chart_image = self.create_chart_image()
        cv2_image = processor._bytes_to_cv2(chart_image)
        text_data = processor._extract_text(cv2_image)
        assert isinstance(text_data, list)
        assert all('text' in item and 'confidence' in item for item in text_data)

    @pytest.mark.asyncio
    async def test_extract_numerical_data(self, processor):
        """Test numerical data extraction."""
        test_data = [
            {'text': '10.5', 'confidence': 0.9, 'bbox': [[0, 0], [10, 0], [10, 10], [0, 10]]},
            {'text': '20.7', 'confidence': 0.85, 'bbox': [[20, 0], [30, 0], [30, 10], [20, 10]]},
            {'text': 'not a number', 'confidence': 0.95, 'bbox': [[40, 0], [50, 0], [50, 10], [40, 10]]}
        ]
        result = processor._extract_numerical_data(test_data)
        assert isinstance(result, dict)
        assert 'type' in result
        assert result['min'] <= result['max']

    @pytest.mark.asyncio
    async def test_error_handling(self, processor):
        """Test error handling with invalid inputs."""
        # Test with empty image
        empty_image = self.create_test_image(10, 10, 'black')
        cv2_image = processor._bytes_to_cv2(empty_image)
        text_data = processor._extract_text(cv2_image)
        assert len(text_data) == 0

    @pytest.mark.asyncio
    async def test_process_image(self, processor):
        """Test the complete image processing pipeline."""
        class MockFile:
            async def download_as_bytearray(self):
                return bytearray(TestImageProcessor.create_chart_image(self))

        result = await processor.process_image(MockFile())
        assert isinstance(result, dict)
        assert 'chart_type' in result
        assert 'text_data' in result
        assert 'numerical_data' in result

    @pytest.mark.asyncio
    async def test_invalid_image_data(self, processor):
        """Test handling of invalid image data."""
        class MockInvalidFile:
            async def download_as_bytearray(self):
                return bytearray(b"invalid data")

        with pytest.raises(InvalidImageError):
            await processor.process_image(MockInvalidFile())

    @pytest.mark.asyncio
    async def test_empty_image(self, processor):
        """Test handling of empty image."""
        class MockEmptyFile:
            async def download_as_bytearray(self):
                return bytearray()

        with pytest.raises(InvalidImageError):
            await processor.process_image(MockEmptyFile())

    @pytest.mark.asyncio
    async def test_very_small_image(self, processor):
        """Test handling of very small images."""
        tiny_image = self.create_test_image(5, 5)
        class MockTinyFile:
            async def download_as_bytearray(self):
                return bytearray(tiny_image)

        with pytest.raises(InvalidImageError):
            await processor.process_image(MockTinyFile())

    @pytest.mark.asyncio
    async def test_corrupted_image(self, processor):
        """Test handling of corrupted image data."""
        valid_image = self.create_test_image()
        corrupted_image = valid_image[:-100]  # Remove last 100 bytes
        class MockCorruptedFile:
            async def download_as_bytearray(self):
                return bytearray(corrupted_image)

        with pytest.raises(InvalidImageError):
            await processor.process_image(MockCorruptedFile()) 