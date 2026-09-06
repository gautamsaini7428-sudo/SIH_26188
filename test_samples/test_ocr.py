"""Test script to verify EasyOCR extraction on real sample images."""
import os, sys, json
import easyocr
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

reader = easyocr.Reader(['en'], gpu=False)

# Create two distinctly different sample ID document images
os.makedirs("test_samples", exist_ok=True)

# Image 1: Aadhaar for "Rohan Verma", ID "4321 8765 2109", DOB "12/04/1991"
img1 = Image.new('RGB', (800, 500), color=(255, 255, 255))
d1 = ImageDraw.Draw(img1)
d1.rectangle([(20, 20), (780, 480)], outline=(11, 41, 37), width=3)
d1.text((50, 40), "GOVERNMENT OF INDIA", fill=(0, 0, 0))
d1.text((50, 80), "UNIQUE IDENTIFICATION AUTHORITY OF INDIA", fill=(0, 0, 0))
d1.text((50, 150), "Name: Rohan Verma", fill=(0, 0, 0))
d1.text((50, 200), "DOB: 12/04/1991", fill=(0, 0, 0))
d1.text((50, 250), "Gender: Male", fill=(0, 0, 0))
d1.text((50, 300), "Address: Flat 402, Palm Heights, Sector 62, Noida, UP 201301", fill=(0, 0, 0))
d1.text((50, 380), "4321 8765 2109", fill=(0, 0, 0))
# Add a face placeholder
d1.rectangle([(600, 140), (740, 320)], fill=(200, 160, 140), outline=(0, 0, 0))
d1.ellipse([(640, 180), (660, 200)], fill=(0, 0, 0)) # Eye
d1.ellipse([(680, 180), (700, 200)], fill=(0, 0, 0)) # Eye
d1.line([(650, 260), (690, 260)], fill=(0, 0, 0), width=3) # Mouth
img1.save("test_samples/sample_doc_rohan.png")

# Image 2: DL for "Sneha Mukherjee", ID "DL-0420239988776", DOB "28/11/1997"
img2 = Image.new('RGB', (800, 500), color=(245, 250, 255))
d2 = ImageDraw.Draw(img2)
d2.rectangle([(20, 20), (780, 480)], outline=(20, 50, 100), width=3)
d2.text((50, 40), "UNION OF INDIA - DRIVING LICENCE", fill=(0, 0, 0))
d2.text((50, 80), "TRANSPORT DEPARTMENT DELHI", fill=(0, 0, 0))
d2.text((50, 150), "Name: Sneha Mukherjee", fill=(0, 0, 0))
d2.text((50, 200), "DOB: 28/11/1997", fill=(0, 0, 0))
d2.text((50, 250), "DL No: DL-0420239988776", fill=(0, 0, 0))
d2.text((50, 300), "Address: 88 Park Street, Kolkata, West Bengal 700016", fill=(0, 0, 0))
d2.text((50, 360), "Valid Till: 27/11/2037", fill=(0, 0, 0))
# Add another face placeholder
d2.rectangle([(600, 140), (740, 320)], fill=(210, 170, 145), outline=(0, 0, 0))
d2.ellipse([(635, 175), (655, 195)], fill=(50, 30, 0)) # Eye
d2.ellipse([(685, 175), (705, 195)], fill=(50, 30, 0)) # Eye
d2.line([(645, 255), (695, 255)], fill=(150, 0, 0), width=4) # Mouth
img2.save("test_samples/sample_doc_sneha.png")

print("Generated sample documents.")

# Run EasyOCR on both
res1 = reader.readtext("test_samples/sample_doc_rohan.png")
res2 = reader.readtext("test_samples/sample_doc_sneha.png")

text1 = [r[1] for r in res1]
text2 = [r[1] for r in res2]

print("Rohan OCR text:", text1)
print("Sneha OCR text:", text2)
