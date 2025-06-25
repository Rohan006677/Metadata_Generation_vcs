from pdfminer.high_level import extract_text as extract_pdf_text
import docx2txt
import os

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return extract_pdf_text(file_path)
    elif ext == '.docx':
        return docx2txt.process(file_path)
    elif ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError("Unsupported file type. Only PDF, DOCX, and TXT are supported.")
 
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLine

def extract_title_by_font_block(pdf_path):
    try:
        for page_layout in extract_pages(pdf_path):
            title_lines = []
            base_font = None

            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        if not isinstance(text_line, LTTextLine):
                            continue

                        # Get average font size of this line
                        font_sizes = [char.size for char in text_line if isinstance(char, LTChar)]
                        if not font_sizes:
                            continue
                        avg_font = sum(font_sizes) / len(font_sizes)

                        text = text_line.get_text().strip()

                        # Skip garbage
                        if len(text) < 5 or any(x in text.lower() for x in ['abstract', 'doi', 'email', 'university', 'introduction']):
                            if title_lines:
                                break  # if we already started, stop on keywords
                            else:
                                continue

                        # First valid line: mark as title
                        if base_font is None and text[0].isupper() and avg_font > 8:
                            base_font = avg_font
                            title_lines.append(text)
                        elif base_font:
                            # Add line only if font matches (within 5% tolerance)
                            if abs(avg_font - base_font) / base_font < 0.05:
                                title_lines.append(text)
                            else:
                                break

            return " ".join(title_lines).strip() if title_lines else "N/A"

    except Exception as e:
        print(f"[extract_title_by_font_block] Error: {e}")
        return "N/A"
