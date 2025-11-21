"""
OCR and Vision-Based Food Input Processor
Extracts food information from uploaded images using OCR or Vision API.
Enhanced with better extraction patterns and automatic inventory addition.
"""

import os
import re
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from uploads.models import Upload
from inventory.models import InventoryItem, FoodItem


class OCRProcessor:
    """
    Advanced OCR processor for extracting food information from images.
    """
    
    # Enhanced food item patterns for extraction
    FOOD_PATTERNS = {
        'item_name': [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Capitalized words
            r'\b([A-Z]{2,})\b',  # All caps (brands)
            r'([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)',  # Mixed case
        ],
        'quantity': [
            r'(\d+\.?\d*)\s*(kg|g|lb|oz|l|ml|pack|piece|pcs|pkg|box|bottle|can)',  # Quantity with unit
            r'(\d+)\s*x\s*(\d+)',  # Multiplier format
            r'(\d+)\s*(\w+)',  # Generic number + word
        ],
        'date': [
            r'(EXP|EXPIRES?|USE BY|BEST BY|SELL BY)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Expiration labels
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Date formats
            r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',  # Text dates
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # ISO format
        ],
        'price': [
            r'\$(\d+\.?\d*)',  # Dollar amounts
            r'(\d+\.?\d*)\s*USD',
            r'PRICE\s*:?\s*\$?(\d+\.?\d*)',
        ],
        'barcode': [
            r'\b(\d{8,13})\b',  # Barcode numbers
        ],
    }
    
    # Common food keywords for better category inference
    FOOD_KEYWORDS = {
        'vegetable': ['lettuce', 'tomato', 'carrot', 'broccoli', 'spinach', 'cucumber', 'pepper', 
                     'onion', 'potato', 'celery', 'cabbage', 'cauliflower', 'corn', 'peas'],
        'fruit': ['apple', 'banana', 'orange', 'berry', 'grape', 'mango', 'peach', 'pear', 
                 'strawberry', 'blueberry', 'watermelon', 'pineapple', 'kiwi'],
        'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour cream', 'cottage cheese'],
        'meat': ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'sausage', 'bacon', 'ham'],
        'grain': ['bread', 'rice', 'pasta', 'cereal', 'flour', 'oats', 'wheat', 'quinoa', 'barley'],
        'beverage': ['juice', 'soda', 'water', 'coffee', 'tea', 'milk', 'drink'],
        'snack': ['chips', 'crackers', 'cookies', 'nuts', 'chocolate', 'candy'],
    }
    
    def __init__(self, upload):
        self.upload = upload
        self.image_path = upload.image.path if upload.image and hasattr(upload.image, 'path') else None
    
    def extract_food_data(self, use_google_vision=False):
        """
        Extract food data from image.
        Returns extracted data with confidence scores and extraction details.
        """
        if not self.image_path or not os.path.exists(self.image_path):
            return {
                'success': False,
                'error': 'Image file not found',
                'confidence': 0
            }
        
        # Try Google Vision API first if available
        if use_google_vision and self._has_google_vision_key():
            result = self._extract_with_google_vision()
            if result.get('success'):
                return result
        
        # Fallback to Tesseract OCR
        return self._extract_with_tesseract()
    
    def _extract_with_tesseract(self):
        """Extract text using Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            # Read image
            image = Image.open(self.image_path)
            
            # Preprocess image for better OCR (optional)
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text with different configurations
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            # If no text, try different PSM mode
            if not text.strip():
                text = pytesseract.image_to_string(image, config='--psm 3')
            
            # Parse extracted text
            extracted_data = self._parse_text(text)
            confidence = self._calculate_confidence(extracted_data)
            
            # Determine if extraction is partial
            is_partial = confidence < 70
            
            return {
                'success': True,
                'method': 'tesseract',
                'raw_text': text,
                'extracted_data': extracted_data,
                'confidence': confidence,
                'is_partial': is_partial,
                'missing_fields': self._get_missing_fields(extracted_data)
            }
        except ImportError:
            return {
                'success': False,
                'error': 'Tesseract OCR not installed. Install with: pip install pytesseract',
                'fallback': 'Please enter information manually',
                'confidence': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'OCR processing failed: {str(e)}',
                'fallback': 'Please enter information manually',
                'confidence': 0
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
                    'error': response.error.message,
                    'confidence': 0
                }
            
            # Extract text
            texts = response.text_annotations
            if texts:
                text = texts[0].description
                extracted_data = self._parse_text(text)
                confidence = self._calculate_confidence(extracted_data)
                is_partial = confidence < 70
                
                return {
                    'success': True,
                    'method': 'google_vision',
                    'raw_text': text,
                    'extracted_data': extracted_data,
                    'confidence': confidence,
                    'is_partial': is_partial,
                    'missing_fields': self._get_missing_fields(extracted_data)
                }
            else:
                return {
                    'success': False,
                    'error': 'No text detected in image',
                    'confidence': 0
                }
        except ImportError:
            return {
                'success': False,
                'error': 'Google Vision API not available',
                'confidence': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Google Vision API error: {str(e)}',
                'fallback': 'Falling back to Tesseract OCR',
                'confidence': 0
            }
    
    def _parse_text(self, text):
        """Parse extracted text to find food information with enhanced patterns."""
        extracted = {
            'item_name': None,
            'quantity': None,
            'unit': None,
            'expiration_date': None,
            'price': None,
            'category': None,
            'barcode': None,
        }
        
        text_upper = text.upper()
        text_lower = text.lower()
        
        # Extract item name (improved pattern matching)
        # Try to find product names (usually at the beginning or after common labels)
        name_patterns = [
            r'PRODUCT\s*:?\s*([A-Z][A-Za-z\s]+)',
            r'ITEM\s*:?\s*([A-Z][A-Za-z\s]+)',
            r'^([A-Z][A-Za-z\s]{3,})',  # Start of text
            r'\n([A-Z][A-Za-z\s]{3,})\n',  # On its own line
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # Filter out common non-food words
                if not any(word in name.upper() for word in ['EXP', 'DATE', 'PRICE', 'QUANTITY', 'WEIGHT']):
                    extracted['item_name'] = name
                    break
        
        # If no name found, try first capitalized sequence
        if not extracted['item_name']:
            name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,3})\b', text)
            if name_match:
                extracted['item_name'] = name_match.group(1)
        
        # Extract quantity and unit (enhanced)
        qty_patterns = [
            r'(\d+\.?\d*)\s*(kg|g|lb|oz|l|ml|pack|piece|pcs|pkg|box|bottle|can|ct)',
            r'NET\s*WT\s*:?\s*(\d+\.?\d*)\s*(kg|g|lb|oz)',
            r'WEIGHT\s*:?\s*(\d+\.?\d*)\s*(kg|g|lb|oz)',
            r'(\d+)\s*x\s*(\d+)',  # Multiplier
        ]
        
        for pattern in qty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['quantity'] = float(match.group(1))
                if len(match.groups()) > 1:
                    extracted['unit'] = match.group(2).lower()
                break
        
        # Extract expiration date (enhanced patterns)
        date_patterns = [
            r'(EXP|EXPIRES?|USE BY|BEST BY|SELL BY)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(2) if len(match.groups()) > 1 else match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    extracted['expiration_date'] = parsed_date
                    break
        
        # Extract price
        price_match = re.search(r'\$(\d+\.?\d*)', text)
        if price_match:
            extracted['price'] = float(price_match.group(1))
        
        # Extract barcode
        barcode_match = re.search(r'\b(\d{8,13})\b', text)
        if barcode_match:
            extracted['barcode'] = barcode_match.group(1)
        
        # Infer category from item name (enhanced)
        if extracted['item_name']:
            extracted['category'] = self._infer_category(extracted['item_name'])
        
        return extracted
    
    def _parse_date(self, date_str):
        """Parse date string to date object with multiple formats."""
        if not date_str:
            return None
        
        # Clean the date string
        date_str = date_str.strip()
        
        # Try common formats
        formats = [
            '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d',
            '%m/%d/%y', '%d/%m/%y', '%y/%m/%d',
            '%d %b %Y', '%d %B %Y', '%b %d, %Y', '%B %d, %Y',
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                # Validate reasonable date (not too far in past or future)
                today = timezone.now().date()
                if today - timedelta(days=365*2) <= parsed <= today + timedelta(days=365*2):
                    return parsed
            except:
                continue
        
        return None
    
    def _infer_category(self, item_name):
        """Infer food category from item name with enhanced keyword matching."""
        if not item_name:
            return 'other'
        
        item_lower = item_name.lower()
        
        # Check against food keywords
        for category, keywords in self.FOOD_KEYWORDS.items():
            for keyword in keywords:
                if keyword in item_lower:
                    return category
        
        # Try to match against food database
        food_item = FoodItem.objects.filter(name__icontains=item_name[:10]).first()
        if food_item:
            return food_item.category
        
        return 'other'
    
    def _calculate_confidence(self, extracted_data):
        """Calculate confidence score for extracted data."""
        confidence = 0
        max_score = 100
        
        # Item name (required, 30 points)
        if extracted_data['item_name']:
            confidence += 30
            # Bonus if it matches food database
            if FoodItem.objects.filter(name__icontains=extracted_data['item_name'][:10]).exists():
                confidence += 5
        
        # Quantity (important, 25 points)
        if extracted_data['quantity']:
            confidence += 25
        
        # Unit (important, 15 points)
        if extracted_data['unit']:
            confidence += 15
        
        # Expiration date (nice to have, 20 points)
        if extracted_data['expiration_date']:
            confidence += 20
        
        # Category (helpful, 10 points)
        if extracted_data['category']:
            confidence += 10
        
        # Price (optional, 5 points)
        if extracted_data['price']:
            confidence += 5
        
        return min(confidence, max_score)
    
    def _get_missing_fields(self, extracted_data):
        """Get list of missing important fields."""
        missing = []
        
        if not extracted_data.get('item_name'):
            missing.append('item_name')
        if not extracted_data.get('quantity'):
            missing.append('quantity')
        if not extracted_data.get('unit'):
            missing.append('unit')
        if not extracted_data.get('expiration_date'):
            missing.append('expiration_date')
        
        return missing
    
    def _has_google_vision_key(self):
        """Check if Google Vision API key is available."""
        api_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or \
                  getattr(settings, 'GOOGLE_VISION_API_KEY', None)
        return api_key is not None
    
    def create_inventory_item(self, user, item_data, auto_add=False):
        """
        Create inventory item from extracted data.
        
        Args:
            user: User object
            item_data: Dictionary with item data
            auto_add: If True and confidence is high, add automatically
        
        Returns:
            Dictionary with status and item/info
        """
        # Check if we should auto-add (high confidence and all required fields)
        required_fields = ['item_name', 'quantity', 'unit']
        has_required = all(item_data.get(field) for field in required_fields)
        
        if auto_add and has_required:
            # Auto-add to inventory
            item = InventoryItem.objects.create(
                user=user,
                item_name=item_data.get('item_name', 'Unknown Item'),
                quantity=Decimal(str(item_data.get('quantity', 1))),
                unit=item_data.get('unit', 'piece'),
                category=item_data.get('category', 'other'),
                purchase_date=timezone.now().date(),
                expiration_date=item_data.get('expiration_date'),
            )
            item.update_status()
            
            # Associate upload with inventory item
            self.upload.associated_inventory = item
            self.upload.save()
            
            return {
                'success': True,
                'auto_added': True,
                'item': item,
                'message': 'Item automatically added to inventory'
            }
        else:
            # Return data for user confirmation
            return {
                'success': True,
                'auto_added': False,
                'item_data': item_data,
                'message': 'Please review and confirm the extracted information'
            }
