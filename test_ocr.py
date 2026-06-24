from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"D:\OCR\ocr\tesseract.exe"

img = Image.open("id_front.jpg")

text = pytesseract.image_to_string(img)

print("===== OCR OUTPUT =====")
print(text)