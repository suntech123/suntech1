import pypdfium2 as pdfium
from PIL import Image
import cv2
import numpy as np
import os
from pathlib import Path
import glob
import pandas as pd

def render_page_for_detection(pdf_path, page_num):
    # 1. Load the PDF
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page_num]

    # 2. Render the page to a high-quality image (e.g., 300 DPI)
    # scale=4 roughly equals 300 DPI (72 * 4 ≈ 288)
    bitmap = page.render(scale=4, rotation=0)

    # 3. Convert to PIL Image
    pil_image = bitmap.to_pil()

    return pil_image