# Tesseract OCR Installation Guide

## Issue
The OCR feature requires Tesseract OCR engine to be installed on your system. The Python package `pytesseract` is just a wrapper - you need the actual Tesseract binary.

## Installation Instructions

### Ubuntu/Debian (Linux)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Verify Installation
```bash
tesseract --version
```

You should see output like:
```
tesseract 4.1.1
 leptonica-1.78.0
  libgif 5.1.4 : libjpeg 8d (libjpeg-turbo 2.0.3) : libpng 1.6.37 : libtiff 4.1.0 : zlib 1.2.11 : libwebp 0.6.1
```

### macOS
```bash
brew install tesseract
```

### Windows
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. **Important:** During installation, make sure to check "Add to PATH"
4. Or manually add Tesseract to your PATH

### After Installation

1. **Restart your Django development server:**
   ```bash
   python manage.py runserver
   ```

2. **Test OCR:**
   - Go to Uploads page
   - Upload an image (receipt or food label)
   - Click "Process with OCR"
   - OCR should now work!

## Python Package

The Python package `pytesseract` is already in `requirements.txt` and should be installed:
```bash
pip install pytesseract
```

## Troubleshooting

### Error: "tesseract: command not found"
- Tesseract is not in your PATH
- On Linux: Make sure it's installed: `which tesseract`
- On Windows: Add Tesseract installation directory to PATH

### Error: "pytesseract not found"
- Install Python package: `pip install pytesseract`

### Still having issues?
- Check Tesseract is installed: `tesseract --version`
- Check Python package: `python -c "import pytesseract; print(pytesseract.__version__)"`
- Restart Django server after installation

## Alternative: Manual Entry

If you can't install Tesseract, you can still use the application:
- Upload images normally
- Manually enter food information
- OCR is optional - the app works without it!

