import fitz
import os
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from google import genai 

# Configuration OCR pour Windows 
# N'oubliez pas d'installer le logiciel Tesseract-OCR sur le PC qui fait tourner ce code !
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 1. Chargement sécurisé de la clé API depuis le fichier .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Clé API introuvable ! Vérifiez votre fichier .env")

# 2. Configuration du NOUVEAU client Gemini
client = genai.Client(api_key=api_key)
