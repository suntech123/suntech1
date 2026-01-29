import json

def explain_page_conversion(adi_result, target_page_num):
    """
    Extracts a specific page from ADI result and shows its Labelbox conversion.
    """
    # 1. Access the root results (handles both common ADI JSON structures)
    ar = adi_result.get("analyzeResult") or adi_result
    pages = ar.get("pages", [])
    
    # 2. Find the specific page requested
    page_data = next((p for p in pages if p.get("pageNumber") == target_page_num), None)
    
    if not page_data:
        return f"Error: Page {target_page_num} not found in ADI result."

    # Internal helper to convert polygon format [x1, y1, x2, y2...] -> [[x, y], ...]
    def to_lb_poly(poly):
        return [[poly[i], poly[i+1]] for i in range(0, len(poly), 2)] if poly else []

    # 3. Convert Words to Labelbox Tokens
    lb_tokens = []
    for word in page_data.get("words", []):
        lb_tokens.append({
            "text": word.get("content") or word.get("text"),
            "confidence": word.get("confidence", 1.0),
            "polygon": to_lb_poly(word.get("polygon")),
            "page": target_page_num
        })

    # 4. Convert ADI Lines to Labelbox Lines
    lb_lines = []
    for line in page_data.get("lines", []):
        lb_lines.append({
            "text": line.get("content") or line.get("text"),
            "polygon": to_lb_poly(line.get("polygon")),
            "page": target_page_num
        })

    # 5. Return a "Before & After" style summary
    return {
        "summary": {
            "page_number": target_page_num,
            "total_tokens_found": len(lb_tokens),
            "total_lines_found": len(lb_lines)
        },
        "labelbox_format": {
            "tokens": lb_tokens,
            "lines": lb_lines
        }
    }

# --- Example of how to use this in your code ---
# page_summary = explain_page_conversion(azure_result, 1)
# print(json.dumps(page_summary, indent=2))
