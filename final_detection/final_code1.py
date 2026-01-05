import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple

import cv2
import numpy as np
import pandas as pd
import pypdfium2 as pdfium
from PIL import Image

# --- CONFIGURATION ---
@dataclass(frozen=True)
class TableDetectionConfig:
    """Configuration parameters for table detection algorithms."""
    # Rendering
    render_scale: float = 4.0  # ~300 DPI
    
    # Preprocessing
    adaptive_block_size: int = 15
    adaptive_c: int = 4
    
    # Line Detection Scaling (Image dim / value)
    line_scale_factor: int = 40
    
    # Line Validation Thresholds
    min_h_line_w_ratio: float = 0.05
    max_h_line_h_ratio: float = 0.05
    min_h_aspect: float = 5.0
    
    min_v_line_h_ratio: float = 0.02
    max_v_line_w_ratio: float = 0.02
    min_v_aspect: float = 10.0
    
    min_line_density: float = 0.50
    
    # Clustering
    cluster_v_smear: float = 0.01
    
    # Table Logic Rules
    min_spanning_ratio: float = 0.85
    min_structure_lines: int = 3
    connected_max_v_len_ratio: float = 0.4
    
    # Specific Rule Thresholds
    rule_row_dense_h: int = 6
    rule_row_dense_v: int = 1
    rule_list_width_ratio: float = 0.5

class TableStats(NamedTuple):
    """Immutable return object for detection stats."""
    has_table: bool
    h_lines: int
    v_lines: int
    debug_image: np.ndarray | None = None

# --- UTILITIES ---
def convert_pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Converts a PIL image to an OpenCV BGR numpy array."""
    # Convert RGB to BGR for OpenCV
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# --- CORE LOGIC ---
class TableDetector:
    """
    Handles the Computer Vision logic for detecting tables in images.
    """
    def __init__(self, config: TableDetectionConfig = TableDetectionConfig()):
        self.cfg = config

    def detect(self, image: np.ndarray, generate_debug_mask: bool = False) -> TableStats:
        """
        Main entry point to detect tables in a single image.
        """
        if image is None:
            raise ValueError("Image provided to detector is None")

        h, w = image.shape[:2]
        
        # 1. Preprocessing
        combined_raw = self._preprocess_image(image)
        
        # 2. Get Line Candidates
        h_candidates, v_candidates = self._get_line_candidates(combined_raw, h, w)
        
        # 3. Validate Lines
        clean_h = self._validate_lines(h_candidates, combined_raw, is_horizontal=True, img_shape=(h, w))
        clean_v = self._validate_lines(v_candidates, combined_raw, is_horizontal=False, img_shape=(h, w))
        
        # 4. Cluster and Analyze
        has_table, total_h, total_v, debug_mask = self._analyze_clusters(clean_h, clean_v, (h, w))
        
        return TableStats(
            has_table=has_table,
            h_lines=total_h,
            v_lines=total_v,
            debug_image=debug_mask if generate_debug_mask else None
        )

    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Adaptive Threshold (Preserve faint headers)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY_INV, 
            self.cfg.adaptive_block_size, 
            self.cfg.adaptive_c
        )
        
        # Sobel Edges (Preserve colored blocks)
        sobel_y = cv2.Sobel(gray, cv2.CV_8U, 0, 1, ksize=3)
        _, edges_h = cv2.threshold(sobel_y, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        sobel_x = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=3)
        _, edges_v = cv2.threshold(sobel_x, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        combined = cv2.bitwise_or(thresh, edges_h)
        return cv2.bitwise_or(combined, edges_v)

    def _get_line_candidates(self, binary_map: np.ndarray, h: int, w: int) -> tuple[np.ndarray, np.ndarray]:
        h_scale = int(w / self.cfg.line_scale_factor)
        v_scale = int(h / self.cfg.line_scale_factor)
        
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_scale, 1))
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_scale))
        
        h_cand = cv2.morphologyEx(binary_map, cv2.MORPH_OPEN, h_kernel)
        v_cand = cv2.morphologyEx(binary_map, cv2.MORPH_OPEN, v_kernel)
        return h_cand, v_cand

    def _validate_lines(self, candidates: np.ndarray, binary_map: np.ndarray, 
                        is_horizontal: bool, img_shape: tuple[int, int]) -> np.ndarray:
        h, w = img_shape
        clean_mask = np.zeros_like(binary_map)
        contours, _ = cv2.findContours(candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            
            # Geometric validation
            if is_horizontal:
                if cw < (w * self.cfg.min_h_line_w_ratio): continue
                if ch > (h * self.cfg.max_h_line_h_ratio): continue
                if cw / ch < self.cfg.min_h_aspect: continue
            else:
                if ch < (h * self.cfg.min_v_line_h_ratio): continue
                if cw > (w * self.cfg.max_v_line_w_ratio): continue
                if ch / cw < self.cfg.min_v_aspect: continue
            
            # Density validation
            roi = binary_map[y:y+ch, x:x+cw]
            density = cv2.countNonZero(roi) / (cw * ch)
            
            if density > self.cfg.min_line_density:
                cv2.drawContours(clean_mask, [cnt], -1, 255, -1)
                
        return clean_mask

    def _analyze_clusters(self, clean_h: np.ndarray, clean_v: np.ndarray, 
                          img_shape: tuple[int, int]) -> tuple[bool, int, int, np.ndarray]:
        h, w = img_shape
        grid_structure = cv2.bitwise_or(clean_h, clean_v)
        
        # Cluster nearby lines
        cluster_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, 
            (15, int(h * self.cfg.cluster_v_smear))
        )
        rough_clustering = cv2.morphologyEx(grid_structure, cv2.MORPH_CLOSE, cluster_kernel)
        candidates, _ = cv2.findContours(rough_clustering, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        final_mask = np.zeros_like(grid_structure)
        total_h_lines = 0
        total_v_lines = 0
        tables_found = 0
        
        for cnt in candidates:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            
            # Extract local ROIs
            roi_h = clean_h[cy:cy+ch, cx:cx+cw]
            roi_v = clean_v[cy:cy+ch, cx:cx+cw]
            
            local_h_cnts, _ = cv2.findContours(roi_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            local_v_cnts, _ = cv2.findContours(roi_v, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            n_h = len(local_h_cnts)
            n_v = len(local_v_cnts)
            
            # Logic Pre-calculations
            spanning_h_count = 0
            for h_c in local_h_cnts:
                _, _, lw, _ = cv2.boundingRect(h_c)
                if lw > (cw * self.cfg.min_spanning_ratio):
                    spanning_h_count += 1
            
            roi_intersect = cv2.bitwise_and(roi_h, roi_v)
            joints_cnts, _ = cv2.findContours(roi_intersect, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            num_joints = len(joints_cnts)
            
            # Apply Rules
            if self._is_table_cluster(n_h, n_v, spanning_h_count, num_joints, cw, ch, w, local_v_cnts):
                cv2.drawContours(final_mask, local_h_cnts, -1, 255, -1, offset=(cx, cy))
                cv2.drawContours(final_mask, local_v_cnts, -1, 255, -1, offset=(cx, cy))
                total_h_lines += n_h
                total_v_lines += n_v
                tables_found += 1
                
        return (tables_found > 0), total_h_lines, total_v_lines, cv2.bitwise_not(final_mask)

    def _is_table_cluster(self, n_h: int, n_v: int, spanning_h: int, joints: int, 
                          cw: int, ch: int, img_w: int, v_contours: list) -> bool:
        """Determines if a cluster of lines represents a table based on business rules."""
        
        has_structure = (spanning_h >= self.cfg.min_structure_lines) or (n_v >= 3)
        
        # Connectivity Check
        is_connected = True
        if n_v >= 2:
            max_v_len = 0
            for v_c in v_contours:
                _, _, _, v_h = cv2.boundingRect(v_c)
                max_v_len = max(max_v_len, v_h)
            if max_v_len < (ch * self.cfg.connected_max_v_len_ratio):
                is_connected = False

        # Rule E: Comparison Table
        is_comparison = (n_v == 1) and (spanning_h >= 3) and (joints >= 3)
        
        # Rule F: Row-Density (Zebra)
        is_row_dense = (n_h >= self.cfg.rule_row_dense_h) and (n_v >= self.cfg.rule_row_dense_v)
        
        # Rule B: List Table
        relative_width = cw / img_w
        is_list = (n_v < 1) and (spanning_h >= 3) and (relative_width > self.cfg.rule_list_width_ratio)
        
        # Rule C: Standard Grid
        is_standard = (joints >= 4) and has_structure and is_connected
        
        return is_standard or is_list or is_comparison or is_row_dense


class PDFProcessor:
    """Handles PDF loading, iteration, and orchestration."""
    
    def __init__(self, detector: TableDetector):
        self.detector = detector

    def process_file(self, pdf_path: Path) -> list[int]:
        """
        Scans a PDF file and returns a list of page numbers containing tables.
        """
        if not pdf_path.exists():
            logging.error(f"PDF file not found: {pdf_path}")
            return []

        # Open PDF efficiently
        try:
            pdf = pdfium.PdfDocument(str(pdf_path))
            num_pages = len(pdf)
        except Exception as e:
            logging.error(f"Failed to open PDF {pdf_path}: {e}")
            return []

        logging.info(f"Analyzing {num_pages} pages in: {pdf_path.name}")
        pages_with_tables = []

        for i in range(num_pages):
            try:
                page_stats = self._process_page(pdf, i)
                
                log_msg = (
                    f"Page {i+1}: "
                    f"Table={page_stats.has_table} "
                    f"(H:{page_stats.h_lines}, V:{page_stats.v_lines})"
                )
                
                if page_stats.has_table:
                    logging.info(f"  [+] {log_msg}")
                    pages_with_tables.append(i + 1)
                else:
                    logging.debug(f"  [-] {log_msg}")
                    
            except Exception as e:
                logging.error(f"  [!] Error on page {i+1}: {e}")
                
        return pages_with_tables

    def _process_page(self, pdf_doc: pdfium.PdfDocument, page_num: int) -> TableStats:
        """Renders and processes a single page."""
        page = pdf_doc[page_num]
        bitmap = page.render(scale=self.detector.cfg.render_scale, rotation=0)
        pil_image = bitmap.to_pil()
        cv_image = convert_pil_to_cv2(pil_image)
        
        return self.detector.detect(cv_image)


# --- MAIN EXECUTION ---
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    setup_logging()
    
    # Paths (Use Pathlib)
    input_dir = Path("./data_files/cleaned_pdfs")
    output_dir = Path("./data_files/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialization
    config = TableDetectionConfig()
    detector = TableDetector(config)
    processor = PDFProcessor(detector)
    
    results = {}
    
    # Gather files
    pdf_files = sorted(list(input_dir.glob("*.pdf")) + list(input_dir.glob("*.PDF")))
    
    if not pdf_files:
        logging.warning(f"No PDF files found in {input_dir}")
        return

    # Processing Loop
    for pdf_path in pdf_files:
        logging.info("=" * 40)
        detected_pages = processor.process_file(pdf_path)
        
        file_stem = pdf_path.stem.strip()
        results[file_stem] = detected_pages
        logging.info("=" * 40)

    # Export
    try:
        df = pd.DataFrame(list(results.items()), columns=['Filename', 'Page_Content'])
        out_csv = output_dir / 'pdf_output.csv'
        df.to_csv(out_csv, index=False)
        logging.info(f"Successfully saved results to {out_csv}")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")

if __name__ == "__main__":
    main()