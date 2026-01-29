import pytest
import uuid
from your_script_name import build_read_layer, azure_polygon_to_points

# 1. Mock Data: A minimal Azure Document Intelligence response
@pytest.fixture
def mock_azure_result():
    return {
        "analyzeResult": {
            "pages": [
                {
                    "pageNumber": 1,
                    "words": [
                        {
                            "content": "Hello",
                            "polygon": [0, 0, 10, 0, 10, 5, 0, 5],
                            "confidence": 0.99
                        }
                    ],
                    "lines": [
                        {
                            "content": "Hello World",
                            "polygon": [0, 0, 50, 0, 50, 10, 0, 10]
                        }
                    ]
                }
            ]
        }
    }

# 2. Test the specific polygon helper function
def test_azure_polygon_to_points():
    flat_poly = [1, 2, 3, 4, 5, 6, 7, 8]
    expected = [[1, 2], [3, 4], [5, 6], [7, 8]]
    assert azure_polygon_to_points(flat_poly) == expected
    assert azure_polygon_to_points([]) == []
    assert azure_polygon_to_points(None) == []

# 3. Comprehensive test for the conversion logic
def test_build_read_layer_structure(mock_azure_result):
    dr_id = "cl_datarow_123"
    feature_name = "OCR_Layer"
    
    result = build_read_layer(mock_azure_result, dr_id, feature_name)

    # Test Top-level Structure
    assert "uuid" in result
    assert result["dataRow"]["id"] == dr_id
    assert len(result["predictions"]) == 1
    
    prediction = result["predictions"][0]
    assert prediction["model"] == "azure_ai_document_intelligence"
    
    # Test Result/Value mapping
    payload = prediction["result"][0]
    assert payload["type"] == "read"
    assert payload["name"] == feature_name
    
    tokens = payload["value"]["tokens"]
    lines = payload["value"]["lines"]

    # Validate Tokens (Words)
    assert len(tokens) == 1
    assert tokens[0]["text"] == "Hello"
    assert tokens[0]["confidence"] == 0.99
    assert tokens[0]["page"] == 1
    assert tokens[0]["polygon"] == [[0, 0], [10, 0], [10, 5], [0, 5]]

    # Validate Lines
    assert len(lines) == 1
    assert lines[0]["text"] == "Hello World"
    assert lines[0]["page"] == 1
    assert lines[0]["polygon"] == [[0, 0], [50, 0], [50, 10], [0, 10]]

# 4. Test Error Handling / Edge Cases
def test_empty_azure_result():
    empty_result = {"analyzeResult": {"pages": []}}
    result = build_read_layer(empty_result, "id")
    
    # Structure should still exist, but lists should be empty
    tokens = result["predictions"][0]["result"][0]["value"]["tokens"]
    assert tokens == []

def test_missing_analyze_result_root():
    # Test fallback if 'analyzeResult' key is missing but 'pages' is at root
    alt_result = {"pages": [{"pageNumber": 1, "words": []}]}
    result = build_read_layer(alt_result, "id")
    assert result["dataRow"]["id"] == "id"

def test_missing_confidence_defaults_to_one(mock_azure_result):
    # Remove confidence from mock
    del mock_azure_result["analyzeResult"]["pages"][0]["words"][0]["confidence"]
    
    result = build_read_layer(mock_azure_result, "id")
    token = result["predictions"][0]["result"][0]["value"]["tokens"][0]
    
    # It should default to 1.0 based on common logic
    assert token["confidence"] == 1.0
