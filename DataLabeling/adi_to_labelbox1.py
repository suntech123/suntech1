import json
import uuid
from pathlib import Path

def azure_polygon_to_points(poly):
    """
    Converts Azure's flat list [x1, y1, x2, y2...] 
    to Labelbox points [[x, y], [x, y]...]
    """
    if not poly:
        return []
    return [[poly[i], poly[i+1]] for i in range(0, len(poly), 2)]

def build_read_layer(azure_analyze_result, data_row_id, feature_name="Document Read"):
    """
    Converts Azure Read output to Labelbox Read-layer NDJSON.
    """
    # Extract the root result object
    ar = azure_analyze_result.get("analyzeResult", azure_analyze_result)
    pages = ar.get("pages", [])

    read_tokens = []
    read_lines = []

    for page in pages:
        page_number = page.get("pageNumber")
        
        # Process Words/Tokens
        for w in page.get("words", []):
            poly = w.get("polygon")
            text = w.get("content") or w.get("text")
            if not poly or not text:
                continue
            
            read_tokens.append({
                "text": text,
                "confidence": w.get("confidence", 1.0),
                "polygon": azure_polygon_to_points(poly),
                "page": page_number
            })

        # Process Lines
        for line in page.get("lines", []):
            poly = line.get("polygon")
            text = line.get("content") or line.get("text")
            if not poly or not text:
                continue

            read_lines.append({
                "text": text,
                "polygon": azure_polygon_to_points(poly),
                "page": page_number
            })

    # Construct the Labelbox NDJSON entry
    prediction_id = str(uuid.uuid4())
    
    ndjson_obj = {
        "uuid": str(uuid.uuid4()),
        "dataRow": {"id": data_row_id},
        "predictions": [
            {
                "model": "azure_ai_document_intelligence",
                "prediction_id": prediction_id,
                "result": [
                    {
                        "type": "read",
                        "name": feature_name, # Must match Feature Name in Labelbox Ontology
                        "value": {
                            "tokens": read_tokens,
                            "lines": read_lines
                        }
                    }
                ]
            }
        ]
    }

    return ndjson_obj
