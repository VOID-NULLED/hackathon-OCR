"""
GPU-Accelerated OCR processing service with EasyOCR.
Includes frame quality metrics (blur detection, illumination analysis).
"""
import os
import re
import logging
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import easyocr
import torch
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_path
from django.conf import settings

logger = logging.getLogger(__name__)


class GPUOCRService:
    """
    GPU-accelerated OCR service using EasyOCR with CUDA support.
    Automatically falls back to CPU if GPU not available.
    """
    
    def __init__(self):
        # Check GPU availability
        self.use_gpu = torch.cuda.is_available()
        if self.use_gpu:
            logger.info(f"🚀 GPU DETECTED: {torch.cuda.get_device_name(0)}")
            logger.info(f"   CUDA Version: {torch.version.cuda}")
            logger.info(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        else:
            logger.warning("⚠️  No GPU detected. Using CPU for OCR (slower).")
        
        # Initialize EasyOCR reader with GPU support
        self.supported_languages = getattr(settings, 'OCR_LANGUAGES', ['en'])
        logger.info(f"Initializing EasyOCR with languages: {self.supported_languages}")
        
        self.reader = easyocr.Reader(
            self.supported_languages,
            gpu=self.use_gpu,
            verbose=False
        )
        
        logger.info(f"✅ EasyOCR initialized successfully (GPU: {self.use_gpu})")
    
    def calculate_blur_variance(self, image: np.ndarray) -> float:
        """
        Calculate Laplacian variance to measure image blur.
        Higher values = sharper image, lower values = blurry.
        
        Args:
            image: OpenCV image array (BGR or grayscale)
        
        Returns:
            Blur variance (Laplacian variance)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Calculate Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        return float(variance)
    
    def calculate_illumination_mean(self, image: np.ndarray) -> float:
        """
        Calculate mean brightness/illumination of image.
        
        Args:
            image: OpenCV image array (BGR or grayscale)
        
        Returns:
            Mean illumination value (0-255)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Calculate mean brightness
        mean_brightness = gray.mean()
        
        return float(mean_brightness)
    
    def process_image(self, image_path: str, language: str = 'en') -> Dict:
        """
        Process a single image file and extract text using GPU-accelerated OCR.
        
        Args:
            image_path: Path to the image file
            language: Language code for OCR (default: 'en')
        
        Returns:
            Dictionary with extracted text, confidence, and metrics
        """
        start_time = time.time()
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Calculate quality metrics
            blur_var = self.calculate_blur_variance(image)
            illum_mean = self.calculate_illumination_mean(image)
            
            # Perform OCR with EasyOCR
            results = self.reader.readtext(image_path)
            
            # Extract text and confidences
            texts = []
            confidences = []
            
            for (bbox, text, conf) in results:
                if text.strip():
                    texts.append(text)
                    confidences.append(conf * 100)  # Convert to percentage
            
            # Combine all text
            full_text = ' '.join(texts)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            return {
                'text': full_text.strip(),
                'confidence': round(avg_confidence, 2),
                'language': language,
                'processing_time': round(processing_time, 2),
                'word_count': len(full_text.split()),
                'blur_variance': blur_var,
                'illumination_mean': illum_mean,
                'gpu_used': self.use_gpu,
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
                'blur_variance': 0,
                'illumination_mean': 0,
                'gpu_used': self.use_gpu,
                'success': False,
                'error': str(e)
            }
    
    def process_image_from_array(self, image_array: np.ndarray, enhanced: bool = False) -> Dict:
        """
        Process an image from numpy array (for real-time camera frames).
        
        Args:
            image_array: OpenCV image array (BGR format)
            enhanced: Whether this is an enhanced frame
        
        Returns:
            Dictionary with OCR results and quality metrics
        """
        start_time = time.time()
        
        try:
            # Calculate quality metrics
            blur_var = self.calculate_blur_variance(image_array)
            illum_mean = self.calculate_illumination_mean(image_array)
            
            # Perform OCR with EasyOCR (pass numpy array directly)
            results = self.reader.readtext(image_array)
            
            # Extract text and confidences
            texts = []
            confidences = []
            
            for (bbox, text, conf) in results:
                if text.strip():
                    texts.append(text)
                    confidences.append(conf * 100)
            
            # Combine all text
            full_text = ' '.join(texts)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            return {
                'text': full_text.strip(),
                'confidence': round(avg_confidence, 2),
                'processing_time': round(processing_time, 2),
                'word_count': len(full_text.split()),
                'blur_variance': blur_var,
                'illumination_mean': illum_mean,
                'enhanced': enhanced,
                'gpu_used': self.use_gpu,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error processing image array: {str(e)}")
            return {
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'word_count': 0,
                'blur_variance': 0,
                'illumination_mean': 0,
                'enhanced': enhanced,
                'gpu_used': self.use_gpu,
                'success': False,
                'error': str(e)
            }
    
    def process_pdf(self, pdf_path: str, language: str = 'en') -> List[Dict]:
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


# Singleton instance for global access
_gpu_ocr_service = None


def get_gpu_ocr_service() -> GPUOCRService:
    """Get or create the global GPU OCR service instance."""
    global _gpu_ocr_service
    
    if _gpu_ocr_service is None:
        _gpu_ocr_service = GPUOCRService()
    
    return _gpu_ocr_service
