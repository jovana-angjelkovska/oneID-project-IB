import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"D:\OCR\ocr\tesseract.exe"

print(pytesseract.get_languages(config=''))