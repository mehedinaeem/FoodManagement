"""
OCR and Vision-Based Food Input Processor
Extracts food information from uploaded images using OCR or Vision API.
"""

import os
import re
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from uploads.models import Upload
from inventory.models import InventoryItem


class OCRProcessor:
    """
    Processes uploaded images to extract food information.
    """
    
    # Common food item patterns for extraction
    FOOD_PATTERNS = {
        'item_name': [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Capitalized words
            r'([A-Z]{2,})',  # All caps (brands)
        ],
        'quantity': [
            r'(\d+\.?\d*)\s*(kg|g|lb|oz|l|ml|pack|piece)',  # Quantity with unit
            r'(\d+)\s*x\s*(\d+)',  # Multiplier format
        ],
        'date': [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Date formats
            r'(EXP|EXPIRES?|USE BY|BEST BY)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4})',
        ],
        'price': [
            r'\$(\d+\.?\d*)',  # Dollar amounts
            r'(\d+\.?\d*)\s*USD',
        ],
    }
    
    def __init__(self, upload):
        self.upload = upload
        self.image_path = upload.image.path if upload.image else None
    
    def extract_food_data(self, use_google_vision=False):
        """
        Extract food data from image.
        Returns extracted data with confidence scores.
        """
        if not self.image_path or not os.path.exists(self.image_path):
            return {
                'success': False,
                'error': 'Image file not found'
            }
        
        # Try Google Vision API first if available
        if use_google_vision and self._has_google_vision_key():
            return self._extract_with_google_vision()
        
        # Fallback to Tesseract OCR
        try:
            return self._extract_with_tesseract()
        except Exception as e:
            return {
                'success': False,
                'error': f'OCR processing failed: {str(e)}',
                'fallback': 'Please enter information manually'
            }
    
    def _extract_with_tesseract(self):
        """Extract text using Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            # Read image
            image = Image.open(self.image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Parse extracted text
            extracted_data = self._parse_text(text)
            
            return {
                'success': True,
                'method': 'tesseract',
                'raw_text': text,
                'extracted_data': extracted_data,
                'confidence': self._calculate_confidence(extracted_data)
            }
        except ImportError:
            return {
                'success': False,
                'error': 'Tesseract OCR not installed. Install with: pip install pytesseract',
                'fallback': 'Please enter information manually'
            }
    
    def _extract_with_google_vision(self):
        """Extract text using Google Vision API."""
        try:
            from google.cloud import vision
            
            client = vision.ImageAnnotatorClient()
            
            with open(self.image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
            
            if response.error.message:
                return {
                    'success': False,
                    'error': response.error.message
                }
            
            # Extract text
            texts = response.text_annotations
            if texts:
                text = texts[0].description
                extracted_data = self._parse_text(text)
                
                return {
                    'success': True,
                    'method': 'google_vision',
                    'raw_text': text,
                    'extracted_data': extracted_data,
                    'confidence': self._calculate_confidence(extracted_data)
                }
            else:
                return {
                    'success': False,
                    'error': 'No text detected in image'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Google Vision API error: {str(e)}',
                'fallback': 'Falling back to manual entry'
            }
    
    def _parse_text(self, text):
        """Parse extracted text to find food information."""
        extracted = {
            'item_name': None,
            'quantity': None,
            'unit': None,
            'expiration_date': None,
            'price': None,
            'category': None,
        }
        
        # Extract item name (first capitalized word sequence)
        name_match = re.search(self.FOOD_PATTERNS['item_name'][0], text)
        if name_match:
            extracted['item_name'] = name_match.group(1)
        
        # Extract quantity and unit
        qty_match = re.search(self.FOOD_PATTERNS['quantity'][0], text, re.IGNORECASE)
        if qty_match:
            extracted['quantity'] = float(qty_match.group(1))
            extracted['unit'] = qty_match.group(2).lower()
        
        # Extract expiration date
        date_match = re.search(self.FOOD_PATTERNS['date'][1], text, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(2) if len(date_match.groups()) > 1 else date_match.group(1)
            extracted['expiration_date'] = self._parse_date(date_str)
        
        # Extract price
        price_match = re.search(self.FOOD_PATTERNS['price'][0], text)
        if price_match:
            extracted['price'] = float(price_match.group(1))
        
        # Infer category from item name
        if extracted['item_name']:
            extracted['category'] = self._infer_category(extracted['item_name'])
        
        return extracted
    
    def _parse_date(self, date_str):
        """Parse date string to date object."""
        try:
            # Try common formats
            formats = ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except:
                    continue
            return None
        except:
            return None
    
    def _infer_category(self, item_name):
        """Infer food category from item name."""
        item_lower = item_name.lower()
        
        category_keywords = {
            'vegetable': ['lettuce', 'tomato', 'carrot', 'broccoli', 'spinach', 'cucumber', 'pepper'],
            'fruit': ['apple', 'banana', 'orange', 'berry', 'grape', 'mango', 'peach'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
            'meat': ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb'],
            'grain': ['bread', 'rice', 'pasta', 'cereal', 'flour', 'oats'],
            'beverage': ['juice', 'soda', 'water', 'coffee', 'tea'],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in item_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def _calculate_confidence(self, extracted_data):
        """Calculate confidence score for extracted data."""
        confidence = 0
        total_fields = 6
        
        if extracted_data['item_name']:
            confidence += 20
        if extracted_data['quantity']:
            confidence += 20
        if extracted_data['unit']:
            confidence += 15
        if extracted_data['expiration_date']:
            confidence += 20
        if extracted_data['price']:
            confidence += 15
        if extracted_data['category']:
            confidence += 10
        
        return confidence
    
    def _has_google_vision_key(self):
        """Check if Google Vision API key is available."""
        api_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or \
                  getattr(settings, 'GOOGLE_VISION_API_KEY', None)
        return api_key is not None
    
    def create_inventory_item_from_extraction(self, extracted_data, confirm=True):
        """
        Create inventory item from extracted data.
        If confirm=True, returns data for user confirmation.
        """
        if confirm:
            return {
                'item_name': extracted_data.get('item_name', ''),
                'quantity': extracted_data.get('quantity', 1),
                'unit': extracted_data.get('unit', 'piece'),
                'category': extracted_data.get('category', 'other'),
                'expiration_date': extracted_data.get('expiration_date'),
                'purchase_date': timezone.now().date(),
            }
        else:
            # Create item directly
            item = InventoryItem.objects.create(
                user=self.upload.user,
                item_name=extracted_data.get('item_name', 'Unknown Item'),
                quantity=extracted_data.get('quantity', 1),
                unit=extracted_data.get('unit', 'piece'),
                category=extracted_data.get('category', 'other'),
                purchase_date=timezone.now().date(),
                expiration_date=extracted_data.get('expiration_date'),
            )
            item.update_status()
            
            # Associate upload with inventory item
            self.upload.associated_inventory = item
            self.upload.save()
            
            return item

