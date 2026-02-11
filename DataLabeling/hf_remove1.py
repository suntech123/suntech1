import os
import fitz  # PyMuPDF
from collections import Counter
from typing import List, Dict, Any, Tuple

# Assuming these imports exist in your project structure
# from modules.pdf_extractor import PDFHeaderFooterExtractor
# from modules.adi_helper import get_adi_results
# from modules.base import PDFProcessor, time_it, logger

class RedactionPDFProcessor(PDFProcessor):
    """
    PDF processor that removes headers and footers using redaction.
    Refactored for single-pass extraction and "Title Protection" logic.
    """

    @time_it
    def process(self, pdf_path: str, output_pdf_path: str):
        """Process the PDF to remove headers and footers."""
        doc = None
        try:
            logger.info(f"Processing {pdf_path}")
            
            # 1. Configuration & Thresholds
            # Increase thresholds slightly to ensure we only target truly repeating elements
            header_count_threshold = int(os.environ.get("header_count_threshold", 5))
            footer_count_threshold = int(os.environ.get("footer_count_threshold", 7))
            
            # 2. External Analysis (Azure ADI)
            # Used for reliable page number detection and table overlap prevention
            page_numbers_y_coords, tables_y_coords = get_adi_results(pdf_path)

            # 3. Preliminary Check
            doc = fitz.open(pdf_path)
            if len(doc) < 10:
                print(f"Document length ({len(doc)}) < 10 pages. Skipping processing.")
                doc.close()
                return

            # Capture geometry (assuming standard size, otherwise move inside loop)
            first_page_rect = doc[0].rect
            page_height = first_page_rect.height
            page_width = first_page_rect.width

            # 4. Extract Headers/Footers (Single Pass Optimization)
            extractor = PDFHeaderFooterExtractor(pdf_path, tables_y_coords)
            
            # page_map structure: { page_index: [header_bbox_list, footer_bbox_list] }
            # headers/footers lists contain the raw text found at top/bottom
            headers, footers, page_map = extractor.extract_headers_footers()
            
            # Access cleaned versions for frequency analysis
            cleaned_headers = extractor.cleaned_headers
            cleaned_footers = extractor.cleaned_footers
            
            # 5. Frequency Analysis
            valid_headers = [h for h in cleaned_headers if h]
            valid_footers = [f for f in cleaned_footers if f]

            header_counts = Counter(valid_headers)
            footer_counts = Counter(valid_footers)

            # Identify "True" Headers/Footers (high frequency)
            possible_headers = {
                h for h, count in header_counts.items() 
                if count > header_count_threshold
            }
            possible_footers = {
                f for f, count in footer_counts.items() 
                if count > footer_count_threshold
            }

            has_header_margin = bool(possible_headers)
            has_footer_margin = bool(possible_footers)

            # 6. Calculate Default Geometric Margins (Modes)
            # Used as fallback coordinates if specific bounding boxes aren't found
            
            all_header_y1 = [
                coords[0][3] for coords in page_map.values() if coords[0]
            ]
            all_footer_y0 = [
                coords[1][1] for coords in page_map.values() if coords[1]
            ]

            def get_mode(values, default):
                return Counter(values).most_common(1)[0][0] if values else default

            # Default: Header ends at 50px, Footer starts at Bottom - 50px
            result_header_y = get_mode(all_header_y1, default=50)
            result_footer_y = get_mode(all_footer_y0, default=page_height - 50)

            # 7. Safety Constraints
            # If header calculation is crazy deep (>10% of page), reset to safe default
            if result_header_y > (0.10 * page_height):
                result_header_y = 50
            
            # If footer calculation is crazy high (<85% of page down), reset to safe default
            if result_footer_y < (0.85 * page_height):
                result_footer_y = page_height - 50

            # 8. Redaction Loop
            for page_index in range(len(doc)):
                page = doc[page_index]
                p_width = page.rect.width
                p_height = page.rect.height

                # Retrieve extraction data for this page
                current_h_text = cleaned_headers[page_index]
                current_f_text = cleaned_footers[page_index]
                
                # BBoxes: [x0, y0, x1, y1]
                # page_map.get might return None if page was empty
                coords = page_map.get(page_index, [None, None])
                current_h_bbox = coords[0]
                current_f_bbox = coords[1]

                # ==================================================
                # HEADER LOGIC (With "Title Protection")
                # ==================================================
                header_rect = None
                
                # Check frequency of the specific text found on this page
                h_count = header_counts.get(current_h_text, 0)

                # Case A: High-Frequency Header (Safe to delete)
                if has_header_margin and (current_h_text in possible_headers) and current_h_bbox:
                    # Redact exactly what we found + 2px buffer
                    header_rect = fitz.Rect(0, 0, p_width, current_h_bbox[3] + 2)
                
                # Case B: Page Number (Verified by Azure)
                elif (page_index + 1) in page_numbers_y_coords:
                    p_num_y = page_numbers_y_coords[page_index + 1]
                    # Only if it's actually at the top
                    if p_num_y < (0.10 * p_height):
                        header_rect = fitz.Rect(0, 0, p_width, p_num_y + 2)

                # Case C: Fallback / Default Margin
                # CRITICAL CHANGE: Only apply blind margin if text is NOT unique.
                elif has_header_margin:
                    # If we found text, but it appears rarely (<= threshold), it is likely a 
                    # Section Title (e.g., "Schedule of Covered Benefits"). DO NOT REDACT.
                    if current_h_text and h_count <= header_count_threshold:
                        # Log identifying we skipped a title
                        # logger.debug(f"Page {page_index}: Skipping header redaction for title: '{current_h_text}'")
                        header_rect = None 
                    else:
                        # Text is empty, or garbage, or we just missed the exact bbox match.
                        # Apply safe default margin.
                        header_rect = fitz.Rect(0, 0, p_width, result_header_y)

                if header_rect:
                    page.add_redact_annot(header_rect, fill=(1, 1, 1))

                # ==================================================
                # FOOTER LOGIC
                # ==================================================
                footer_rect = None
                f_count = footer_counts.get(current_f_text, 0)

                # Case A: High-Frequency Footer
                if has_footer_margin and (current_f_text in possible_footers) and current_f_bbox:
                    # Redact from top of footer text to bottom of page
                    footer_rect = fitz.Rect(0, current_f_bbox[1] - 2, p_width, p_height)

                # Case B: Page Number (Verified by Azure)
                elif (page_index + 1) in page_numbers_y_coords:
                    p_num_y = page_numbers_y_coords[page_index + 1]
                    # Only if it's actually at the bottom
                    if p_num_y > (0.85 * p_height):
                        footer_rect = fitz.Rect(0, p_num_y - 2, p_width, p_height)

                # Case C: Fallback
                elif has_footer_margin:
                    # Similar protection: If unique text is at the bottom, it might be a specific footnote.
                    # However, footers are less likely to be titles. We apply stricter check.
                    if current_f_text and f_count <= footer_count_threshold:
                        footer_rect = None
                    else:
                        footer_rect = fitz.Rect(0, result_footer_y, p_width, p_height)

                if footer_rect:
                    page.add_redact_annot(footer_rect, fill=(1, 1, 1))

                # Commit redactions for this page to free memory
                page.apply_redactions()

            # 9. Save & Close
            doc.save(output_pdf_path, garbage=4, deflate=True)
            doc.close()

            # 10. Logging (Legacy format)
            final_h_content = header_counts.most_common(1)[0][0] if header_counts else ""
            final_f_content = footer_counts.most_common(1)[0][0] if footer_counts else ""
            
            output_line = (
                f"{os.path.basename(pdf_path)}; \n"
                f"header_margin = {result_header_y}; footer_margin = {result_footer_y}; \n"
                f"header_content = {final_h_content}; footer_content = {final_f_content}; \n"
                f"number_of_pages = {len(headers)}\n"
            )
            print(f"output_line => {output_line}")

        except FileNotFoundError:
            logger.error(f"Error: The file {pdf_path} was not found.")
        except PermissionError:
            logger.error(f"Error: Not sufficient permission to access {pdf_path}.")
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            if doc: doc.close()
            raise