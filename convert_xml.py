import subprocess
from pathlib import Path

def convert_pdf_to_xml(pdf_path: Path | str, xml_path: Path | str) -> None:
    """
    Converts a PDF to XML using the external 'pdftohtml' tool.
    Raises RuntimeError if the conversion fails or the tool is missing.
    """
    command = [
        "pdftohtml",
        "-xml",
        "-i",              # Ignore images (faster)
        "-fontfullname",   # Output full font names
        "-zoom", "1.5",    # Scaling factor
        str(pdf_path),
        str(xml_path)
    ]

    try:
        # check=True automatically raises CalledProcessError if returncode != 0
        subprocess.run(command, check=True, capture_output=True, text=True)

    except subprocess.CalledProcessError as e:
        # Handles cases where pdftohtml runs but encounters an error (e.g., corrupted PDF)
        raise RuntimeError(f"pdftohtml conversion failed: {e.stderr}") from e

    except FileNotFoundError:
        # Handles cases where 'pdftohtml' is not installed on the system
        raise RuntimeError("The 'pdftohtml' tool is not installed or not in PATH.")