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

def extraire_et_restructurer_cv(chemin_pdf):
    """
    Extrait le texte d'un CV avec PyMuPDF.
    Basule sur l'OCR (Tesseract) si le PDF est une image.
    Utilise ensuite Gemini pour réparer les problèmes de colonnes et de mise en page.
    """
    try:
        # --- PHASE 1 : Extraction brute avec PyMuPDF et OCR ---
        document = fitz.open(chemin_pdf)
        texte_brut = ""
        
        for page_num, page in enumerate(document):
            # On tente l'extraction texte normale
            texte_page = page.get_text("text")
            
            # Si la page est (presque) vide de texte informatique, c'est une image/scanné
            if len(texte_page.strip()) < 50:
                print(f"Page {page_num + 1} détectée comme image. Lancement de l'OCR...")
                
                # On convertit la page en image HD
                pixmap = page.get_pixmap(dpi=300)
                image_pil = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                
                # On lance la lecture optique
                texte_page = pytesseract.image_to_string(image_pil, lang='fra+eng')
                
            texte_brut += texte_page + "\n"
            
        document.close()


# --- Zone de test ---
if __name__ == "__main__":
    fichier_test = r"C:\Users\alpha\OneDrive\Desktop\Conduite de projet\C-V Alpha Oumar DIALLO.pdf"
    
    print("--- 1. Lancement de l'extraction (PyMuPDF/OCR) et connexion à Gemini... ---")
    resultat = extraire_et_restructurer_cv(fichier_test)
    
    if resultat["statut"] == "succes":
        print("\n EXTRACTION ET RESTRUCTURATION RÉUSSIES !\n")
        print("=== Voici le CV parfaitement organisé par l'IA ===")
        print(resultat["texte_propre"])
        print("==================================================")
    else:
        print(f"\n Échec : {resultat['erreur']}")
