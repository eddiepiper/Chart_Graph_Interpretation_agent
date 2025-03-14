import pytest
import pytest_asyncio
import asyncio
from src.processors.url_processor import URLProcessor
from unittest.mock import Mock, patch, PropertyMock
import requests
from PIL import Image, ImageDraw
import io
import numpy as np

class TestURLProcessor:
    @pytest_asyncio.fixture
    async def processor(self):
        """Fixture to create URLProcessor instance."""
        processor = URLProcessor()
        return processor

    @pytest.fixture
    def mock_html(self):
        """Fixture to provide mock HTML content."""
        return """
        <html>
            <body>
                <img src="chart1.png" alt="Patient survival rate">
                <figure>
                    <img src="chart2.png" width="600" height="400">
                    <figcaption>Statistical analysis of treatment outcomes</figcaption>
                </figure>
                <div>
                    <img src="logo.png" alt="Site logo">
                </div>
            </body>
        </html>
        """

    def create_test_image(self, width=100, height=100, color='white'):
        """Helper method to create a test image."""
        img = Image.new('RGB', (width, height), color=color)
        # Add some contrast to make it look like a chart
        draw = ImageDraw.Draw(img)
        draw.line([(10, 10), (90, 90)], fill='black', width=2)
        draw.text((10, 10), "Test", fill='black')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()

    @pytest.mark.asyncio
    async def test_initialization(self, processor):
        """Test if the URLProcessor initializes correctly."""
        assert processor is not None
        assert processor.headers is not None

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_basic(self, mock_get, processor, mock_html):
        """Test basic chart extraction from a webpage."""
        # Set up the initial response for the HTML
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        # Set up responses for image requests
        mock_image_response = Mock()
        mock_image_response.content = self.create_test_image(600, 400)
        mock_image_response.headers = {'content-type': 'image/png'}
        
        # Make get return different responses for HTML and image requests
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            return mock_image_response
        
        mock_get.side_effect = side_effect

        charts = await processor.extract_charts("http://example.com")
        assert isinstance(charts, list)
        assert len(charts) > 0
        assert all('url' in chart for chart in charts)
        assert all('image_data' in chart for chart in charts)

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_no_images(self, mock_get, processor):
        """Test chart extraction from a webpage with no images."""
        mock_response = Mock()
        mock_html = "<html><body>No images here</body></html>"
        mock_response.text = mock_html
        type(mock_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_get.return_value = mock_response

        charts = await processor.extract_charts("http://example.com")
        assert isinstance(charts, list)
        assert len(charts) == 0

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_invalid_url(self, mock_get, processor):
        """Test chart extraction with invalid URL."""
        mock_get.side_effect = requests.exceptions.RequestException("Invalid URL")
        
        with pytest.raises(Exception):
            await processor.extract_charts("invalid_url")

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_with_captions(self, mock_get, processor, mock_html):
        """Test chart extraction with figure captions."""
        # Set up the initial response for the HTML
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        # Set up responses for image requests
        mock_image_response = Mock()
        mock_image_response.content = self.create_test_image(600, 400)
        mock_image_response.headers = {'content-type': 'image/png'}
        
        # Make get return different responses for HTML and image requests
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            return mock_image_response
        
        mock_get.side_effect = side_effect

        charts = await processor.extract_charts("http://example.com")
        assert any('caption' in chart for chart in charts)
        assert any('Statistical analysis' in chart.get('caption', '') for chart in charts)

    @pytest.mark.asyncio
    async def test_is_potential_chart(self, processor):
        """Test chart detection logic."""
        # Create test images with some chart-like features
        def create_chart_like_image(width, height):
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            # Add some lines and text to make it look like a chart
            draw.line([(10, 10), (width-10, height-10)], fill='black', width=2)
            draw.text((10, 10), "Chart Title", fill='black')
            return img

        # Create test images
        chart_image = create_chart_like_image(800, 600)
        icon_image = create_chart_like_image(32, 32)
        banner_image = create_chart_like_image(1200, 100)

        # Test with chart-like dimensions and content
        assert processor._is_potential_chart(chart_image) is True

        # Test with small icon dimensions
        assert processor._is_potential_chart(icon_image) is False

        # Test with banner-like dimensions
        assert processor._is_potential_chart(banner_image) is False

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_error_handling(self, mock_get, processor):
        """Test error handling for various scenarios."""
        # Test timeout
        mock_get.side_effect = TimeoutError("Connection timeout")
        with pytest.raises(Exception):
            await processor.extract_charts("http://example.com")

        # Test invalid content type
        mock_response = Mock()
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_html = "<html><body>PDF content</body></html>"
        type(mock_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_get.side_effect = None
        mock_get.return_value = mock_response
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 0

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_image_filtering(self, mock_get, processor):
        """Test filtering of non-chart images."""
        mock_html = """
        <html>
            <body>
                <img src="logo.svg" width="50" height="50">
                <img src="banner.jpg" width="1200" height="200">
                <img src="chart.png" width="600" height="400" alt="Statistical data">
            </body>
        </html>
        """
        
        # Set up the initial response for the HTML
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        # Set up different responses for different image types
        def create_mock_image_response(width, height, is_chart=False, content_type='image/png'):
            response = Mock()
            img = Image.new('RGB', (width, height), color='white')
            if is_chart:
                draw = ImageDraw.Draw(img)
                draw.line([(10, 10), (width-10, height-10)], fill='black', width=2)
                draw.text((10, 10), "Chart Title", fill='black')
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            response.content = img_byte_arr.getvalue()
            response.headers = {'content-type': content_type}
            return response
        
        # Make get return different responses for different URLs
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            elif "logo.svg" in url:
                return create_mock_image_response(50, 50, content_type='image/svg+xml')
            elif "banner.jpg" in url:
                return create_mock_image_response(1200, 200, content_type='image/jpeg')
            elif "chart.png" in url:
                return create_mock_image_response(600, 400, is_chart=True)
            return Mock()
        
        mock_get.side_effect = side_effect

        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 1  # Only the chart image should be included
        assert "chart.png" in charts[0]['url']

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_with_svg(self, mock_get, processor):
        """Test handling of SVG images."""
        mock_html = """
        <html><body><img src="chart.svg" width="600" height="400"></body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        
        mock_svg_response = Mock()
        mock_svg_response.headers = {'content-type': 'image/svg+xml'}
        mock_svg_response.content = b'<svg>...</svg>'
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            return mock_svg_response
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 0  # SVG images should be skipped

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_with_data_url(self, mock_get, processor):
        """Test handling of data URLs in img src."""
        base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        mock_html = f"""
        <html><body><img src="{base64_image}" width="600" height="400"></body></html>
        """
        mock_response = Mock()
        mock_response.text = mock_html
        type(mock_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_get.return_value = mock_response
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 0  # Data URLs should be skipped for security

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_with_nested_figures(self, mock_get, processor):
        """Test handling of nested figure elements."""
        mock_html = """
        <html><body>
            <figure>
                <figure>
                    <img src="nested_chart.png" width="600" height="400">
                    <figcaption>Inner caption</figcaption>
                </figure>
                <figcaption>Outer caption</figcaption>
            </figure>
        </body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        mock_image_response = Mock()
        mock_image_response.content = self.create_test_image(600, 400)
        mock_image_response.headers = {'content-type': 'image/png'}
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            return mock_image_response
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 1
        assert charts[0]['caption'] == "Inner caption"  # Should use innermost caption

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_with_malformed_urls(self, mock_get, processor):
        """Test handling of malformed URLs in img src."""
        mock_html = """
        <html><body>
            <img src="http://invalid url with spaces.png">
            <img src="ftp://unsupported-protocol.com/chart.png">
            <img src="//protocol-relative.com/chart.png">
        </body></html>
        """
        mock_response = Mock()
        mock_response.text = mock_html
        type(mock_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_get.return_value = mock_response
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 0  # Malformed URLs should be skipped

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_with_redirects(self, mock_get, processor):
        """Test handling of redirected image URLs."""
        mock_html = """
        <html><body><img src="chart.png"></body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        # Mock a redirect response
        mock_redirect_response = Mock()
        mock_redirect_response.status_code = 302
        mock_redirect_response.headers = {'Location': 'http://example.com/new_chart.png'}
        
        # Mock the final image response
        mock_image_response = Mock()
        mock_image_response.content = self.create_test_image(600, 400)
        mock_image_response.headers = {'content-type': 'image/png'}
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            elif url == "http://example.com/chart.png":
                return mock_redirect_response
            elif url == "http://example.com/new_chart.png":
                return mock_image_response
            return Mock()
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 1
        assert "new_chart.png" in charts[0]['url']

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_extract_charts_rate_limiting(self, mock_get, processor):
        """Test handling of rate limiting responses."""
        mock_html = """
        <html><body>
            <img src="chart1.png">
            <img src="chart2.png">
            <img src="chart3.png">
        </body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        def create_mock_image_response():
            response = Mock()
            response.content = self.create_test_image(600, 400)
            response.headers = {'content-type': 'image/png'}
            return response
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            elif "chart1.png" in url:
                raise requests.exceptions.RequestException("Rate limited")
            else:
                return create_mock_image_response()
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 2  # Should still process other images when one fails 

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_concurrent_image_downloads(self, mock_get, processor):
        """Test handling of multiple concurrent image downloads."""
        mock_html = """
        <html><body>
            <img src="chart1.png">
            <img src="chart2.png">
            <img src="chart3.png">
            <img src="chart4.png">
            <img src="chart5.png">
        </body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        def create_mock_image_response(delay=0):
            response = Mock()
            response.content = self.create_test_image(600, 400)
            response.headers = {'content-type': 'image/png'}
            return response
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            return create_mock_image_response()
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 5
        assert all('image_data' in chart for chart in charts)

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_different_image_formats(self, mock_get, processor):
        """Test handling of different image formats and sizes."""
        mock_html = """
        <html><body>
            <img src="chart1.png">
            <img src="chart2.jpg">
            <img src="chart3.gif">
            <img src="chart4.bmp">
            <img src="chart5.webp">
        </body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        def create_mock_image_response(format_type='png'):
            response = Mock()
            response.content = self.create_test_image(600, 400)
            response.headers = {'content-type': f'image/{format_type}'}
            return response
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            elif "png" in url:
                return create_mock_image_response('png')
            elif "jpg" in url:
                return create_mock_image_response('jpeg')
            elif "gif" in url:
                return create_mock_image_response('gif')
            elif "bmp" in url:
                return create_mock_image_response('bmp')
            elif "webp" in url:
                return create_mock_image_response('webp')
            return Mock()
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 3  # Only PNG, JPEG, and GIF should be processed
        assert all('image_data' in chart for chart in charts)

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_large_image_handling(self, mock_get, processor):
        """Test handling of large images."""
        mock_html = """
        <html><body><img src="large_chart.png"></body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        # Create a large test image with complex content
        img = Image.new('RGB', (5000, 5000), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add complex content to prevent efficient compression
        for i in range(0, 5000, 10):
            for j in range(0, 5000, 10):
                # Draw random shapes and colors
                color = (i % 256, j % 256, (i + j) % 256)
                draw.rectangle([i, j, i+8, j+8], fill=color)
                draw.line([i, j, i+8, j+8], fill='black', width=2)
                if i % 100 == 0 and j % 100 == 0:
                    draw.text((i, j), f"Data{i},{j}", fill='black')
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', optimize=False)
        img_byte_arr.seek(0)
        large_image = img_byte_arr.getvalue()
        
        mock_image_response = Mock()
        mock_image_response.content = large_image
        mock_image_response.headers = {'content-type': 'image/png'}
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            return mock_image_response
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 1
        assert len(charts[0]['image_data']) > 1000000  # Should be able to handle large images

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_network_timeouts(self, mock_get, processor):
        """Test handling of network timeouts."""
        mock_html = """
        <html><body>
            <img src="timeout1.png">
            <img src="timeout2.png">
            <img src="working.png">
        </body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        def create_mock_image_response():
            response = Mock()
            response.content = self.create_test_image(600, 400)
            response.headers = {'content-type': 'image/png'}
            return response
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            elif "timeout" in url:
                raise requests.exceptions.Timeout("Request timed out")
            return create_mock_image_response()
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 1  # Should still process working images
        assert "working.png" in charts[0]['url']

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_invalid_image_data(self, mock_get, processor):
        """Test handling of invalid image data."""
        mock_html = """
        <html><body>
            <img src="corrupt.png">
            <img src="truncated.png">
            <img src="valid.png">
        </body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        valid_image = self.create_test_image(600, 400)
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            elif "corrupt.png" in url:
                response = Mock()
                response.content = b'Invalid image data'
                response.headers = {'content-type': 'image/png'}
                return response
            elif "truncated.png" in url:
                response = Mock()
                response.content = valid_image[:len(valid_image)//2]  # Truncate the image data
                response.headers = {'content-type': 'image/png'}
                return response
            else:
                response = Mock()
                response.content = valid_image
                response.headers = {'content-type': 'image/png'}
                return response
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 1  # Should only process the valid image
        assert "valid.png" in charts[0]['url']

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_complex_html_structure(self, mock_get, processor):
        """Test handling of complex HTML structures with nested elements."""
        mock_html = """
        <html><body>
            <div class="chart-container">
                <figure>
                    <div class="chart-wrapper">
                        <img src="nested_chart1.png" class="chart" data-type="line">
                    </div>
                    <figcaption>Nested Chart 1</figcaption>
                </figure>
            </div>
            <article>
                <section>
                    <div>
                        <img src="nested_chart2.png" alt="Deep nested chart">
                    </div>
                </section>
            </article>
            <div style="display: none">
                <img src="hidden_chart.png" alt="Hidden chart">
            </div>
        </body></html>
        """
        mock_html_response = Mock()
        mock_html_response.text = mock_html
        type(mock_html_response).content = PropertyMock(return_value=mock_html.encode('utf-8'))
        mock_html_response.headers = {'content-type': 'text/html'}
        
        def create_mock_image_response():
            response = Mock()
            response.content = self.create_test_image(600, 400)
            response.headers = {'content-type': 'image/png'}
            return response
        
        def side_effect(url, **kwargs):
            if url == "http://example.com":
                return mock_html_response
            return create_mock_image_response()
        
        mock_get.side_effect = side_effect
        
        charts = await processor.extract_charts("http://example.com")
        assert len(charts) == 3  # Should find all charts regardless of nesting
        assert any('Nested Chart 1' in chart['caption'] for chart in charts)
        assert any('Deep nested chart' in chart['alt_text'] for chart in charts) 