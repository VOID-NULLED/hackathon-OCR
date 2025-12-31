"""
OCR processing service with pytesseract and image preprocessing.
"""
import os
import re
import logging
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import pytesseract
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_path
from django.conf import settings

logger = logging.getLogger(__name__)


class OCRService:
    """
    Service class for OCR processing with image preprocessing and optimization.
    """
    
    def __init__(self):
        # Configure tesseract path if specified
        if settings.OCR_TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.OCR_TESSERACT_PATH
        
        self.supported_languages = settings.OCR_LANGUAGES
    
    def process_image(self, image_path: str, language: str = 'eng') -> Dict:
        """
        Process a single image file and extract text.
        
        Args:
            image_path: Path to the image file
            language: Language code for OCR (default: 'eng')
        
        Returns:
            Dictionary with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            preprocessed_image = self._preprocess_image(image)
            
            # Perform OCR with detailed data
            ocr_data = pytesseract.image_to_data(
                preprocessed_image,
                lang=language,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text = pytesseract.image_to_string(
                preprocessed_image,
                lang=language
            )
            
            # Calculate confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            return {
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'language': language,
                'processing_time': round(processing_time, 2),
                'word_count': len(text.split()),
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {
                'text': '',
                'confidence': 0,
                'language': language,
                'processing_time': 0,
                'word_count': 0,
                'success': False,
                'error': str(e)
            }
    
    def process_pdf(self, pdf_path: str, language: str = 'eng') -> List[Dict]:
        """
        Process a PDF file and extract text from all pages.
        
        Args:
            pdf_path: Path to the PDF file
            language: Language code for OCR
        
        Returns:
            List of dictionaries with results for each page
        """
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            results = []
            for page_num, image in enumerate(images, start=1):
                # Save temporary image
                temp_path = f"/tmp/page_{page_num}.png"
                image.save(temp_path, 'PNG')
                
                # Process image
                result = self.process_image(temp_path, language)
                result['page_number'] = page_num
                results.append(result)
                
                # Clean up
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return results
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return [{
                'text': '',
                'confidence': 0,
                'language': language,
                'page_number': 1,
                'success': False,
                'error': str(e)
            }]
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
        
        Returns:
            Preprocessed PIL Image
        """
        # Convert PIL Image to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Apply thresholding
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Deskew if needed
        deskewed = self._deskew(thresh)
        
        # Convert back to PIL Image
        return Image.fromarray(deskewed)
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew an image by detecting and correcting rotation.
        
        Args:
            image: OpenCV image array
        
        Returns:
            Deskewed image array
        """
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
        
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Rotate image to deskew
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    def detect_code_blocks(self, text: str) -> List[Dict]:
        """
        Detect code blocks in extracted text.
        
        Args:
            text: Extracted text from OCR
        
        Returns:
            List of detected code blocks with metadata
        """
        code_blocks = []
        
        # Common code patterns
        patterns = {
            'python': r'(def |class |import |from |if __name__|print\()',
            'javascript': r'(function |const |let |var |=>|console\.log)',
            'java': r'(public class|private |protected |void |System\.out)',
            'cpp': r'(#include|int main\(|std::|cout|cin)',
            'sql': r'(SELECT |INSERT |UPDATE |DELETE |FROM |WHERE )',
            'html': r'(<html|<div|<body|<head|<script)',
            'css': r'(\{[^}]*:[^}]*\}|@media|\.[\w-]+\s*\{)',
        }
        
        lines = text.split('\n')
        current_block = []
        block_start = 0
        detected_lang = 'unknown'
        
        for i, line in enumerate(lines):
            # Check if line contains code patterns
            is_code_line = False
            for lang, pattern in patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    is_code_line = True
                    if not current_block:
                        detected_lang = lang
                        block_start = i
                    break
            
            # Check for indentation (common in code)
            if line.startswith((' ' * 4, '\t')) and line.strip():
                is_code_line = True
            
            if is_code_line:
                current_block.append(line)
            elif current_block:
                # End of code block
                code_blocks.append({
                    'code': '\n'.join(current_block),
                    'language': detected_lang,
                    'line_start': block_start + 1,
                    'line_end': i,
                })
                current_block = []
                detected_lang = 'unknown'
        
        # Add last block if exists
        if current_block:
            code_blocks.append({
                'code': '\n'.join(current_block),
                'language': detected_lang,
                'line_start': block_start + 1,
                'line_end': len(lines),
            })
        
        return code_blocks
    
    def analyze_text_type(self, text: str) -> str:
        """
        Analyze the type of content (text, code, or mixed).
        
        Args:
            text: Extracted text
        
        Returns:
            Content type: 'text', 'code', or 'mixed'
        """
        code_blocks = self.detect_code_blocks(text)
        
        if not code_blocks:
            return 'text'
        
        # Calculate code vs text ratio
        total_lines = len(text.split('\n'))
        code_lines = sum(block['line_end'] - block['line_start'] + 1 
                        for block in code_blocks)
        
        code_ratio = code_lines / total_lines if total_lines > 0 else 0
        
        if code_ratio > 0.7:
            return 'code'
        elif code_ratio > 0.2:
            return 'mixed'
        else:
            return 'text'
