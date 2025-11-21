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

# Try to import pytesseract at module level
try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None
    Image = None


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
        # Check if pytesseract is available
        if not PYTESSERACT_AVAILABLE:
            return {
                'success': False,
                'error': 'pytesseract Python package not installed',
                'error_detail': 'Install with: pip install pytesseract',
                'fallback': 'Please enter information manually',
                'confidence': 0
            }
        
        # Check if Tesseract binary is installed on the system
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            # Tesseract binary not found - this is the most common issue
            # pytesseract raises TesseractNotFoundError when binary is missing
            error_type = type(e).__name__
            error_msg = str(e).lower()
            
            if 'tesseractnotfound' in error_type.lower() or 'tesseract' in error_msg or 'not installed' in error_msg or 'path' in error_msg or 'not found' in error_msg:
                return {
                    'success': False,
                    'error': 'Tesseract OCR engine not installed on system',
                    'error_detail': self._get_tesseract_install_instructions(),
                    'fallback': 'Please enter information manually',
                    'confidence': 0
                }
            else:
                # Some other error
                return {
                    'success': False,
                    'error': f'Tesseract OCR error: {str(e)}',
                    'error_detail': self._get_tesseract_install_instructions(),
                    'fallback': 'Please enter information manually',
                    'confidence': 0
                }
        
        try:
            
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
        except Exception as e:
            error_msg = str(e)
            # Provide helpful error messages
            if 'tesseract' in error_msg.lower() or 'not found' in error_msg.lower():
                return {
                    'success': False,
                    'error': 'Tesseract OCR engine not found',
                    'error_detail': self._get_tesseract_install_instructions(),
                    'fallback': 'Please enter information manually',
                    'confidence': 0
                }
            return {
                'success': False,
                'error': f'OCR processing failed: {error_msg}',
                'fallback': 'Please enter information manually',
                'confidence': 0
            }
    
    def _get_tesseract_install_instructions(self):
        """Get installation instructions for Tesseract OCR based on OS."""
        import platform
        os_type = platform.system().lower()
        
        if os_type == 'linux':
            return (
                "Install Tesseract OCR on Linux:\n"
                "  Ubuntu/Debian: sudo apt-get install tesseract-ocr\n"
                "  Fedora: sudo dnf install tesseract\n"
                "  Arch: sudo pacman -S tesseract\n"
                "\n"
                "Then install Python package: pip install pytesseract"
            )
        elif os_type == 'darwin':  # macOS
            return (
                "Install Tesseract OCR on macOS:\n"
                "  Using Homebrew: brew install tesseract\n"
                "\n"
                "Then install Python package: pip install pytesseract"
            )
        elif os_type == 'windows':
            return (
                "Install Tesseract OCR on Windows:\n"
                "  1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "  2. Install Tesseract (add to PATH during installation)\n"
                "  3. Install Python package: pip install pytesseract\n"
                "\n"
                "Or set path manually in settings: pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'"
            )
        else:
            return (
                "Install Tesseract OCR:\n"
                "  1. Install Tesseract OCR engine for your operating system\n"
                "  2. Install Python package: pip install pytesseract\n"
                "\n"
                "See: https://github.com/tesseract-ocr/tesseract"
            )
    
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
        
        # Extract expiration date (enhanced patterns - handles "Exp. Date : 14 JAN 2026")
        date_patterns = [
            # Pattern for "Exp. Date : 14 JAN 2026" format (with label and colon)
            (r'(EXP\.?\s*DATE|EXPIRES?|USE BY|BEST BY|SELL BY|MFG\.?\s*DATE)\s*:?\s*(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', 2),  # Exp. Date : 14 JAN 2026
            # Pattern for date with label but numeric format
            (r'(EXP\.?\s*DATE|EXPIRES?|USE BY|BEST BY|SELL BY)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 2),  # EXP: 01/14/2026
            # Standalone text date format
            (r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', 1),  # 14 JAN 2026
            # Standalone numeric formats
            (r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 1),  # 01/14/2026
            (r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})', 1),  # 2026-01-14
        ]
        
        for pattern, group_num in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(group_num)
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
        
        # Remove common prefixes using regex (handles variations like "Exp. Date :", "EXP:", etc.)
        prefix_pattern = r'^(exp\.?\s*date|expires?|exp\s*:?|use\s+by|best\s+by|sell\s+by|mfg\.?\s*date|manufacturing\s+date|lot\s*&?\s*control\s*no\.?)\s*:?\s*'
        date_str = re.sub(prefix_pattern, '', date_str, flags=re.IGNORECASE).strip()
        
        # Remove leading/trailing colons, spaces, and common separators
        date_str = date_str.strip(' :,.-')
        
        # Normalize month abbreviations (handle uppercase)
        month_map = {
            'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr',
            'MAY': 'May', 'JUN': 'Jun', 'JUL': 'Jul', 'AUG': 'Aug',
            'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'
        }
        for upper, lower in month_map.items():
            date_str = date_str.replace(upper, lower)
        
        # Try common formats (expanded list)
        formats = [
            # Text formats first (common on labels like "14 JAN 2026")
            '%d %b %Y',  # 14 JAN 2026 (after normalization to 14 Jan 2026)
            '%d %B %Y',  # 14 January 2026
            '%b %d, %Y', '%B %d, %Y',  # JAN 14, 2026, January 14, 2026
            '%d-%b-%Y', '%d-%B-%Y',  # 14-JAN-2026
            '%Y %b %d', '%Y %B %d',  # 2026 JAN 14
            # US formats
            '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
            # European formats
            '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y',
            # ISO formats
            '%Y/%m/%d', '%Y-%m-%d',
            # With dots
            '%d.%m.%Y', '%d.%m.%y',
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                # Validate reasonable date
                today = timezone.now().date()
                # Allow dates from 5 years ago (for manufacturing dates) to 10 years in future (for expiration dates)
                if today - timedelta(days=365*5) <= parsed <= today + timedelta(days=365*10):
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
