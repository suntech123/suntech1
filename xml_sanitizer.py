import xml.etree.ElementTree as ET

def get_xml_root(xml_file_path):
    """
    Parses the XML file and returns the root element.
    """
    try:
        tree = ET.parse(xml_file_path)
        return tree.getroot()
    except FileNotFoundError:
        print(f"Error: The file '{xml_file_path}' was not found.")
        return None
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

def sanitize_xml_root(root):
    """
    Accepts the XML root element, removes <text> nodes that contain 
    only whitespace or empty strings, and returns the modified root.
    """
    if root is None:
        return None

    removed_count = 0

    # Iterate over every <page> element within the root
    for page in root.findall('page'):
        # specific list to store nodes to remove for this page
        nodes_to_remove = []

        # Check every <text> node
        for text_node in page.findall('text'):
            # 1. Capture text content (handling nested <b>, <i>, etc.)
            # .itertext() gets all text segments from current node and children
            raw_content = "".join(text_node.itertext())

            # 2. Check if it is purely whitespace
            if not raw_content.strip():
                nodes_to_remove.append(text_node)

        # 3. Perform removal safely
        for node in nodes_to_remove:
            page.remove(node)
            removed_count += 1

    print(f"Sanitization Complete: Removed {removed_count} empty text fragments.")
    
    # Return the modified root so it can be passed to the next step
    return root

# --- Usage Example ---

# 1. Get the root using the standalone function
root_element = get_xml_root('your_input_file.xml')

# 2. Pass that root into the sanitizer
clean_root = sanitize_xml_root(root_element)

# 3. (Optional) Verify by printing the first few elements of the clean root
if clean_root:
    print("Root is ready for data extraction.")