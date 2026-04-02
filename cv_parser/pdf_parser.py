import fitz
import re
import pytesseract
from PIL import Image

# Indiquez à Python où vous avez installé le logiciel Tesseract (à adapter par celui qui lance le bot)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extraire_texte_cv(chemin_pdf):
    """
    Extrait le texte d'un CV et renvoie un dictionnaire structuré.
    Gère l'extraction classique et l'OCR en cas d'image.
    """
    texte_complet = ""
    
    try:
        document = fitz.open(chemin_pdf)
        
        for page_num, page in enumerate(document):
            blocs = page.get_text("blocks")
            blocs_texte = [b for b in blocs if b[6] == 0]
            
            # Lecture de la droite vers la gauche
            blocs_tries = sorted(blocs_texte, key=lambda b: ((b[0] // 150), b[1]))
            
            texte_page = ""
            for b in blocs_tries:
                texte_page += b[4] + "\n"
            
            # OCR si la page semble vide (image)
            if len(texte_page.strip()) < 50:
                pixmap = page.get_pixmap(dpi=300)
                image_pil = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                texte_page = pytesseract.image_to_string(image_pil, lang='fra+eng')
            
            texte_complet += texte_page + "\n"
                
        document.close()
        
        # Le formatage propre attendu par le projet :
        return {
            "statut": "succes",
            "texte_cv": nettoyer_texte(texte_complet),
            "erreur": None
        }
        
    except Exception as e:
        # En cas de fichier corrompu ou introuvable :
        return {
            "statut": "erreur",
            "texte_cv": "",
            "erreur": str(e)
        }

def nettoyer_texte(texte):
    texte = re.sub(r'\n{3,}', '\n\n', texte)
    texte = re.sub(r' {2,}', ' ', texte)
    return texte.strip()

# --- Zone de test ---
if __name__ == "__main__":
    fichier_test = r"C:\Users\alpha\OneDrive\Desktop\Conduite de projet\CV E.pdf"
    
    print("--- Lancement de l'extraction structurée ---")
    resultat = extraire_texte_cv(fichier_test)
    
    if resultat["statut"] == "succes":
        print("Extraction réussie ! Voici un aperçu du texte (les 200 premiers caractères) :")
        print(resultat["texte_cv"][:200] + "...\n")
    else:
        print(f"Échec de l'extraction : {resultat['erreur']}")
