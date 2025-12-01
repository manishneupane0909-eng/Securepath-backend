from pypdf import PdfReader
import sys

try:
    reader = PdfReader("/Users/nish/securepath-backend/.github/workflows/ATP draft1.pdf")
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    print(text)
except Exception as e:
    print(f"Error reading PDF: {e}")
