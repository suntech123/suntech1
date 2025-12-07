from dataclasses import dataclass
from typing import Dict
import xml.etree.ElementTree as ET

# 1. Define the Data Structure for the Value
@dataclass(frozen=True)
class FontSpec:
    size: int
    family: str
    color: str

    # Optional: Helper to check if this looks like a header (heuristic)
    def is_likely_header(self) -> bool:
        # Example heuristic: larger than standard body text (usually 10-12)
        return self.size > 14 or "Bold" in self.family

# 2. Define the Extraction Function
def create_font_map(root: ET.Element) -> Dict[str, FontSpec]:
    """
    Scans the XML root for <fontspec> tags and creates a lookup dictionary.
    
    Returns:
        Dict[str, FontSpec]: A map where Key is the font ID (e.g., "0") 
                             and Value is the FontSpec object.
    """
    font_map = {}

    # fontspec tags can appear inside <page> or at the root level depending on
    # the version of pdftohtml. We search globally using specific xpath '//fontspec'
    for spec in root.findall('.//fontspec'):
        font_id = spec.get('id')
        
        # Extract attributes safely
        # XML attributes are strings, so we convert size to int
        try:
            size = int(spec.get('size', 0))
        except ValueError:
            size = 0
            
        family = spec.get('family', 'Unknown')
        color = spec.get('color', '#000000')

        # Create the immutable object
        font_data = FontSpec(
            size=size, 
            family=family, 
            color=color
        )

        # Populate the map
        font_map[font_id] = font_data

    print(f"Font Map Created: Loaded {len(font_map)} unique font definitions.")
    return font_map

# --- Integration with previous steps ---

# Assuming 'clean_root' is the output from your sanitize_xml_root function
# font_lookup = create_font_map(clean_root)

# Example Usage:
# text_node_font_id = "3" 
# if text_node_font_id in font_lookup:
#     info = font_lookup[text_node_font_id]
#     print(f"Font Family: {info.family}, Size: {info.size}")