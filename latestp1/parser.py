# parser.py
from typing import List, Optional
from models import RawLine, ParsedSection
import config
import logging

logger = logging.getLogger(__name__)

class HierarchyParser:
    def __init__(self):
        # State machine variables
        self.current_h1: Optional[str] = None
        self.current_h2: Optional[str] = None
        self.current_h3: Optional[str] = None
        self.buffer_text: List[str] = []
        self.sections: List[ParsedSection] = []
        self.last_page: int = 1

    def _flush_buffer(self):
        """Saves the current accumulated text into a record."""
        if self.buffer_text:
            combined_text = " ".join(self.buffer_text).strip()
            if combined_text:
                self.sections.append(ParsedSection(
                    header_l1=self.current_h1,
                    header_l2=self.current_h2,
                    header_l3=self.current_h3,
                    body_text=combined_text,
                    page_number=self.last_page
                ))
            self.buffer_text = []

    def process_line(self, line: RawLine):
        """Decides if a line is a header or body text based on config rules."""
        self.last_page = line.page_number
        text = line.text.strip()
        size = line.font_size

        if not text:
            return

        # --- Hierarchy Logic ---
        
        # Level 1 Header detection
        if size >= config.HEADER_1_MIN_SIZE:
            self._flush_buffer()
            self.current_h1 = text
            self.current_h2 = None # Reset lower levels
            self.current_h3 = None
            logger.info(f"Detected H1: {text}")

        # Level 2 Header detection
        elif size >= config.HEADER_2_MIN_SIZE:
            self._flush_buffer()
            self.current_h2 = text
            self.current_h3 = None # Reset lower levels
            logger.debug(f"Detected H2: {text}")

        # Level 3 Header detection
        elif size >= config.HEADER_3_MIN_SIZE and line.is_bold:
            self._flush_buffer()
            self.current_h3 = text

        # Body Text
        else:
            self.buffer_text.append(text)

    def finalize(self) -> List[ParsedSection]:
        """Call this after the last line is processed to catch remaining text."""
        self._flush_buffer()
        return self.sections