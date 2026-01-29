import json
import os
import pytest
import uuid
from pathlib import Path
from your_script_name import load_adi_result, build_read_layer

# 1. Variables from your image for consistency
USER_DIR = '/home/azureuser/cloudfiles/code/Users'
SRC_PATH = f'{USER_DIR}/david.brennan/dev/adi/data/adi_md_output/incoming/including_hf/02-OCT'
FILE_ID = 'Peter-Kiewit_e35cc6ae-67bd-4b2b-b61e-b271969c8786'

# 2. Test for the File Loading Logic
def test_load_adi_result_success():
    """Tests if the file loads correctly from the specific SRC_PATH."""
    # This check ensures the file actually exists on your Azure VM before testing
    file_path = Path(SRC_PATH) / f"{FILE_ID}.json"
    if not file_path.exists():
        pytest.skip(f"Test file not found at {file_path}. Skipping local file test.")

    result = load_adi_result(FILE_ID)
    
    assert isinstance(result, dict), "The loaded result should be a dictionary."
    # Standard ADI JSON check
    assert "analyzeResult" in result or "pages" in result, "JSON missing ADI root keys."

# 3. Test for the Labelbox NDJSON Structure
def test_build_read_layer_conversion():
    """Tests if the conversion result matches the Labelbox Read Layer schema."""
    # Load the real data
    azure_result = load_adi_result(FILE_ID)
    data_row_id = FILE_ID
    
    # Run conversion
    ndjson_entry = build_read_layer(azure_result, data_row_id)

    # Validate Top Level
    assert ndjson_entry["dataRow"]["id"] == data_row_id
    assert "uuid" in ndjson_entry
    assert isinstance(ndjson_entry["predictions"], list)

    # Validate the 'read' type structure shown in your second image
    prediction = ndjson_entry["predictions"][0]
    result_layer = prediction["result"][0]
    
    assert result_layer["type"] == "read"
    assert "value" in result_layer
    assert "tokens" in result_layer["value"]
    assert "lines" in result_layer["value"]

# 4. Test the NDJSON File Output Logic
def test_ndjson_file_format(tmp_path):
    """Verifies that the written file is valid NDJSON (single line JSON)."""
    azure_result = load_adi_result(FILE_ID)
    ndjson_entry = build_read_layer(azure_result, FILE_ID)

    # Create a temporary output file
    out_path = tmp_path / "labelbox_read_predictions.ndjson"
    
    # Logic from your image: single-line writing
    with out_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(ndjson_entry, ensure_ascii=False) + "\n")

    # Read it back and verify
    with open(out_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1, "NDJSON for a single asset should be exactly one line."
        
        parsed_back = json.loads(lines[0])
        assert parsed_back["dataRow"]["id"] == FILE_ID

# 5. Test Error Handling
def test_load_adi_result_not_found():
    """Tests if the function handles missing files gracefully as per your try-except block."""
    result = load_adi_result("non_existent_id")
    # Based on your image's code: result is initialized to '' then returns if except triggers
    assert result == ''
