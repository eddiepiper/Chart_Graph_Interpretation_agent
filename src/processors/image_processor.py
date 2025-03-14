import os
import cv2
import numpy as np
from PIL import Image
import io
import easyocr
import logging
from typing import Dict, List, Tuple, Any
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class ImageProcessingError(Exception):
    """Base exception for image processing errors."""
    pass

class InvalidImageError(ImageProcessingError):
    """Exception raised when the image is invalid or corrupted."""
    pass

class ChartDetectionError(ImageProcessingError):
    """Exception raised when chart detection fails."""
    pass

class OCRError(ImageProcessingError):
    """Exception raised when text extraction fails."""
    pass

class ImageProcessor:
    def __init__(self):
        """Initialize the image processor with EasyOCR."""
        try:
            self.reader = easyocr.Reader(['en'])
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {str(e)}")
            raise ImageProcessingError("Failed to initialize image processor")
        
    async def process_image(self, file) -> Dict[str, Any]:
        """
        Process an image file to extract charts and text.
        
        Args:
            file: Telegram file object
            
        Returns:
            Dict containing processed data including:
            - chart_type: detected type of chart
            - text_data: extracted text
            - numerical_data: extracted numerical values
            - statistical_data: extracted statistical information
        """
        try:
            # Download and convert image to numpy array
            image_data = await file.download_as_bytearray()
            if not image_data:
                raise InvalidImageError("Failed to download image data")

            # Validate image data
            if len(image_data) < 100:  # Basic size check
                raise InvalidImageError("Image data is too small")

            try:
                image = self._bytes_to_cv2(image_data)
            except Exception as e:
                raise InvalidImageError(f"Failed to convert image: {str(e)}")

            # Validate image dimensions
            if image.shape[0] < 10 or image.shape[1] < 10:
                raise InvalidImageError("Image dimensions are too small")

            # Detect chart type with error handling
            try:
                chart_type = self._detect_chart_type(image)
            except Exception as e:
                logger.error(f"Chart detection failed: {str(e)}")
                chart_type = 'unknown'

            # Extract text with error handling
            try:
                text_data = self._extract_text(image)
            except Exception as e:
                logger.error(f"Text extraction failed: {str(e)}")
                raise OCRError("Failed to extract text from image")

            # Extract numerical data
            try:
                numerical_data = self._extract_numerical_data(text_data)
            except Exception as e:
                logger.error(f"Numerical data extraction failed: {str(e)}")
                numerical_data = {'type': 'unknown', 'error': str(e)}

            # Extract statistical information
            try:
                statistical_data = self._extract_statistical_info(text_data)
            except Exception as e:
                logger.error(f"Statistical data extraction failed: {str(e)}")
                statistical_data = {}

            return {
                'chart_type': chart_type,
                'text_data': text_data,
                'numerical_data': numerical_data,
                'statistical_data': statistical_data
            }
            
        except InvalidImageError as e:
            logger.error(f"Invalid image error: {str(e)}")
            raise
        except OCRError as e:
            logger.error(f"OCR error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in image processing: {str(e)}")
            raise ImageProcessingError(f"Failed to process image: {str(e)}")

    def _bytes_to_cv2(self, image_data: bytes) -> np.ndarray:
        """Convert bytes to CV2 image with validation."""
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise InvalidImageError("Failed to decode image")
            return img
        except Exception as e:
            raise InvalidImageError(f"Failed to convert image bytes: {str(e)}")

    def _detect_chart_type(self, image: np.ndarray) -> str:
        """
        Detect the type of chart in the image.
        
        Args:
            image: CV2 image array
            
        Returns:
            String indicating chart type (e.g., 'kaplan_meier', 'bar_chart', etc.)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        
        if lines is None:
            return 'unknown'
        
        # Analyze line patterns to determine chart type
        horizontal_lines = 0
        vertical_lines = 0
        diagonal_lines = 0
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
            
            if angle < 10 or angle > 170:  # Horizontal
                horizontal_lines += 1
            elif 80 < angle < 100:  # Vertical
                vertical_lines += 1
            else:  # Diagonal
                diagonal_lines += 1
        
        # Determine chart type based on line patterns
        if diagonal_lines > (horizontal_lines + vertical_lines) * 0.5:
            return 'kaplan_meier'  # Survival curves often have diagonal lines
        elif horizontal_lines > vertical_lines * 2:
            return 'bar_chart'
        elif abs(horizontal_lines - vertical_lines) < 5:
            return 'scatter_plot'
        else:
            return 'line_graph'

    def _extract_text(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract text from the image using OCR.
        
        Args:
            image: CV2 image array
            
        Returns:
            List of dictionaries containing text and their positions
        """
        results = self.reader.readtext(image)
        if not results or not results[0]:
            return []
        
        extracted_text = []
        for detection in results:
            bbox, text, confidence = detection
            extracted_text.append({
                'text': text,
                'confidence': confidence,
                'bbox': bbox
            })
        
        return extracted_text

    def _extract_numerical_data(self, text_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract numerical information from detected text.
        
        Args:
            text_data: List of dictionaries containing detected text and metadata
            
        Returns:
            Dictionary containing processed numerical data
        """
        try:
            numbers = []
            for item in text_data:
                text = item['text']
                # Try to convert text to float
                try:
                    num = float(text.replace(',', ''))
                    numbers.append(num)
                except ValueError:
                    continue
            
            if not numbers:
                return {'type': 'unknown'}
            
            return {
                'type': 'numerical',
                'min': min(numbers),
                'max': max(numbers),
                'mean': sum(numbers) / len(numbers),
                'count': len(numbers)
            }
            
        except Exception as e:
            logger.error(f"Error extracting numerical data: {str(e)}")
            return {'type': 'unknown'}

    def _extract_statistical_info(self, text_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract statistical information from text data.
        
        Args:
            text_data: List of dictionaries containing text and positions
            
        Returns:
            Dictionary containing statistical information
        """
        stats = {
            'p_value': None,
            'confidence_interval': None,
            'hazard_ratio': None,
            'odds_ratio': None
        }
        
        for item in text_data:
            text = item['text'].lower()
            
            # Extract p-value
            if 'p' in text and ('=' in text or '<' in text or '>' in text):
                stats['p_value'] = text
            
            # Extract confidence interval
            if 'ci' in text or 'confidence interval' in text:
                stats['confidence_interval'] = text
            
            # Extract hazard ratio
            if 'hr' in text or 'hazard ratio' in text:
                stats['hazard_ratio'] = text
            
            # Extract odds ratio
            if 'or' in text or 'odds ratio' in text:
                stats['odds_ratio'] = text
        
        return stats

    def _extract_survival_data(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract data specific to Kaplan-Meier survival curves."""
        # Implementation for survival curve data extraction
        return {'type': 'survival_data'}

    def _extract_bar_data(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract data specific to bar charts."""
        # Implementation for bar chart data extraction
        return {'type': 'bar_data'}

    def _extract_scatter_data(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract data specific to scatter plots."""
        # Implementation for scatter plot data extraction
        return {'type': 'scatter_data'}

    def _extract_line_data(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract data specific to line graphs."""
        # Implementation for line graph data extraction
        return {'type': 'line_data'} 