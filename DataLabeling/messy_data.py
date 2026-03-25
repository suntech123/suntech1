'''
Handling messy text from PDFs is a classic "last-mile" problem in RAG pipelines. When you're dealing with "meriads" of special characters—like smart quotes, ligatures, or encoding artifacts (mojibake)—you need a multi-layered approach rather than a single regex.
​Here is the enterprise-grade blueprint for text cleaning in Python.

​1. Unicode Normalization (The Foundation)
​PDFs often store characters as "decomposed" forms (e.g., an 'e' and an accent separately). Normalizing them to a standard form (NFC) ensures your LLM and vector database see them as a single token.


import unicodedata

def normalize_unicode(text):
    # NFKC handles compatibility characters (e.g., converting '②' to '2')
    return unicodedata.normalize('NFKC', text)


2. Fixing "Smart" Characters & Ligatures
​PDF extractors frequently turn apostrophes and dashes into "curly" versions (like ’ or —) or combine letters like 'fi' into a single ligature character. The library unidecode is the industry standard for "transliterating" these into ASCII-equivalent clean text.


from unidecode import unidecode

def clean_special_chars(text):
    # Converts curly quotes to straight, removes accents, handles ligatures
    return unidecode(text)


3. Handling Mojibake (Encoding Repair)
​If your PDF was encoded in Latin-1 but read as UTF-8, you’ll see gibberish like Ã©. The ftfy (Fixed That For You) library is specifically designed for enterprise pipelines to "guess" and repair these encoding errors automatically.

import ftfy

def fix_encoding(text):
    return ftfy.fix_text(text)


4. Structural Cleaning for RAG
​For RAG, preserving semantic meaning is more important than perfect grammar. You should:
​Remove Control Characters: Non-printing characters (like \x00-\x1f) can break some tokenizers.
​Whitespace Collapse: Turn multiple newlines or tabs into single spaces to maintain a consistent density for your embedding model.


​Recommended Enterprise Pipeline
​In a production environment, you should wrap these into a single utility class:
'''

import re
import unicodedata
import ftfy
from unidecode import unidecode

class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""
        
        # 1. Fix encoding/mojibake
        text = ftfy.fix_text(text)
        
        # 2. Transliterate to ASCII (removes curly quotes, accents)
        text = unidecode(text)
        
        # 3. Unicode Normalization
        text = unicodedata.normalize('NFKC', text)
        
        # 4. Remove non-printable control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 5. Normalize whitespace (collapse multiple spaces/newlines)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

# Example usage
raw_text = "Who’s Eligible for Coverage? \n\n  Cost is 100€"
clean_text = TextCleaner.clean(raw_text)
# Result: "Who's Eligible for Coverage? Cost is 100EUR"

'''
Pro Tip for RAG
​If your PDFs contain tables or multi-column layouts, PyMuPDF (fitz) is great, but consider using layoutparser or marker (a deep-learning based PDF-to-Markdown tool) before cleaning. This prevents the "cleaner" from accidentally merging text from two different columns into a single unreadable sentence.

​Would you like me to show you how to integrate this cleaning step into a specific RAG framework like LangChain or LlamaIndex?
'''