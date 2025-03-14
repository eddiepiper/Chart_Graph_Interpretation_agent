import requests
from bs4 import BeautifulSoup
import io
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class URLProcessor:
    def __init__(self):
        """Initialize the URL processor."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.allowed_schemes = {'http', 'https'}
        self.allowed_content_types = {'image/png', 'image/jpeg', 'image/jpg', 'image/gif'}
        self.max_redirects = 5

    async def extract_charts(self, url: str) -> List[Dict[str, Any]]:
        """
        Extract charts from a given URL.
        
        Args:
            url: URL of the webpage to analyze
            
        Returns:
            List of dictionaries containing chart data
        """
        try:
            # Fetch webpage content
            response = requests.get(url, headers=self.headers, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all images
            images = soup.find_all('img')
            
            # Extract and process potential chart images
            charts = []
            for img in images:
                src = img.get('src', '')
                if not src or src.startswith('data:'):  # Skip empty sources and data URLs
                    continue
                
                try:
                    # Validate and normalize the URL
                    image_url = self._normalize_url(url, src)
                    if not image_url:
                        continue
                    
                    # Download image with redirect handling
                    result = self._get_with_redirects(image_url)
                    if not result:
                        continue
                        
                    img_response, final_url = result
                    
                    # Check content type
                    content_type = img_response.headers.get('content-type', '').lower()
                    if content_type not in self.allowed_content_types:
                        continue
                    
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(img_response.content))
                    
                    # Basic check if image might be a chart
                    if self._is_potential_chart(image):
                        # Convert PIL Image to bytes
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                        
                        charts.append({
                            'image_data': img_byte_arr.getvalue(),
                            'url': final_url,
                            'alt_text': img.get('alt', ''),
                            'caption': self._find_caption(img)
                        })
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error downloading image {src}: {str(e)}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing image {src}: {str(e)}")
                    continue
            
            return charts
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            raise

    def _get_with_redirects(self, url: str, redirect_count: int = 0) -> Optional[Tuple[requests.Response, str]]:
        """
        Get URL content with manual redirect handling.
        
        Args:
            url: URL to fetch
            redirect_count: Current number of redirects (to prevent infinite loops)
            
        Returns:
            Tuple of (Response object, final URL) or None if max redirects exceeded or error occurred
        """
        try:
            if redirect_count >= self.max_redirects:
                logger.warning(f"Max redirects ({self.max_redirects}) exceeded for URL: {url}")
                return None
                
            response = requests.get(url, headers=self.headers, allow_redirects=False)
            
            # Handle redirects manually
            if response.status_code in (301, 302, 303, 307, 308):
                redirect_url = response.headers.get('Location')
                if redirect_url:
                    # Make redirect URL absolute if it's relative
                    if not redirect_url.startswith(('http://', 'https://')):
                        redirect_url = urljoin(url, redirect_url)
                    return self._get_with_redirects(redirect_url, redirect_count + 1)
            
            response.raise_for_status()
            return response, url
            
        except Exception as e:
            logger.warning(f"Error fetching URL {url}: {str(e)}")
            return None

    def _normalize_url(self, base_url: str, src: str) -> Optional[str]:
        """
        Normalize and validate image URL.
        
        Args:
            base_url: Base URL of the webpage
            src: Source URL from img tag
            
        Returns:
            Normalized URL or None if invalid
        """
        try:
            # Handle protocol-relative URLs
            if src.startswith('//'):
                src = f"https:{src}"
            
            # Make URL absolute if it's relative
            if not src.startswith(('http://', 'https://')):
                src = urljoin(base_url, src)
            
            # Parse and validate URL
            parsed = urlparse(src)
            if parsed.scheme not in self.allowed_schemes:
                return None
            
            # Check for spaces or other invalid characters
            if ' ' in src or not re.match(r'^https?://[^\s/$.?#].[^\s]*$', src):
                return None
                
            return src
        except Exception:
            return None

    def _is_potential_chart(self, image: Image.Image) -> bool:
        """
        Basic check if an image might be a chart.
        This is a simple implementation that can be enhanced with more sophisticated detection.
        """
        # Convert to grayscale
        gray = image.convert('L')
        
        # Get image statistics
        stats = gray.getextrema()
        
        # Check if image has good contrast (might be a chart)
        contrast = stats[1] - stats[0]
        
        # Basic size check (charts are usually not too small)
        width, height = image.size
        min_dimension = min(width, height)
        
        return contrast > 50 and min_dimension > 200

    def _find_caption(self, img_tag) -> str:
        """Find the caption associated with an image."""
        # Find the closest figure ancestor and its caption
        current_tag = img_tag
        while current_tag:
            if current_tag.name == 'figure':
                figcaption = current_tag.find('figcaption')
                if figcaption:
                    return figcaption.get_text(strip=True)
            current_tag = current_tag.parent
            
        # If no figure caption found, use alt text
        alt = img_tag.get('alt', '')
        if alt:
            return alt
        
        return "" 