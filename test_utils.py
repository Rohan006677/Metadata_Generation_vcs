from utils.extract_text import extract_text
from utils.ocr_utils import extract_text_from_scanned_pdf
from utils.metadata_utils import generate_metadata
import json

# === CHANGE THIS TO YOUR FILE ===
file_path = "data/sample_pdf2.pdf"     # Can also use .docx or .txt

# Normal extract
#try:
 ## text = extract_text(file_path)
#except Exception as e:
 #  print("⚠️ Regular extraction failed. Trying OCR...")
  #  text = extract_text_from_scanned_pdf(file_path)


print("🟢 Trying regular text extraction...")
text = extract_text(file_path)

# Check if text is too short or blank
if len(text.strip()) < 5:  # You can adjust the threshold
    print("⚠️ Regular extraction is not applicable. Trying OCR...")
    text = extract_text_from_scanned_pdf(file_path)
else:
    print("✅ Regular extraction successful.")

# Display raw extracted text
print("\n📄 Extracted Text Preview:\n", text[:1000], "\n...")

# Generate metadata
metadata = generate_metadata(text)

print("\n🧠 Generated Metadata:\n")
print(json.dumps(metadata, indent=4))


