# Import required packages
import cv2
import pytesseract
from autocorrect import Speller

# Mention the installed location of Tesseract-OCR in your system
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

file = open("recognized.txt", "a")

# Apply OCR on the cropped image
text = pytesseract.image_to_string(cropped)

# Appending the text into file
file.write(text)
