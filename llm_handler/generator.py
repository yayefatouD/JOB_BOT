import os
import time
from google import genai
from .config import config

class LetterGenerator:
    def __init__(self):
        if not config.llm.api_key:
            raise ValueError("Clé API manquante dans le .env")
        self.client = genai.Client(api_key=config.llm.api_key)

        # Détection automatique du modèle pour éviter les 404
        try:
            available_models = [m.name for m in self.client.models.list()]
            flash_models = [name for name in available_models if "flash" in name.lower()]
            self.model_to_use = flash_models[0] if flash_models else config.llm.model_name
        except Exception:
            self.model_to_use = config.llm.model_name

    def generate(self, cv_text: str, job_description: str, retries=3) -> str:
        """
        Génère une lettre de motivation structurée en LaTeX pur.
        """
        prompt = rf"""
        Rédige une lettre de motivation professionnelle en utilisant la structure "Vous-Moi-Nous".
        Le format de sortie doit être du code LaTeX valide (\documentclass{{article}}).

        STRUCTURE DE RÉDACTION :
        1. Fait une en-tête classique d'une lettre de motivation (coordonné de l'expéditeur en haut à gauche et du receveur en bas à droite)
        2. LE VOUS : Accroche originale montrant la connaissance de l'entreprise et de ses besoins.
        3. LE MOI : 2-3 réalisations concrètes issues du CV avec verbes d'action et résultats chiffrés.
        4. LE NOUS : Projection de la collaboration et résolution de leurs problématiques.
        5. Ne précise jamais le VOUS-MOI-NOUS

        TON ET STYLE :
        - Assertif, factuel, professionnel, direct, précis et rigoureux (250-300 mots).
        - Paragraphes courts, utilisation de listes à puces (\begin{{itemize}}).

        CONSIGNES LATEX :
        - Classe : \documentclass{{article}}
        - Packages : fontenc, inputenc (utf8), babel (french), geometry (margin=2cm).
        - Retourne UNIQUEMENT le code source complet.

        INFOS :
        Offre : {job_description}
        CV : {cv_text}
        """

        for i in range(retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_to_use,
                    contents=prompt
                )

                if not response.text:
                    continue

                # Nettoyage des balises Markdown ```latex ... ```
                content = response.text
                if "```latex" in content:
                    content = content.split("```latex")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                return content.strip()

            except Exception as e:
                if "429" in str(e): # Gestion du quota
                    print(f"⏳ Quota atteint, attente... (Essai {i+1})")
                    time.sleep(20)
                    continue
                return f"ERREUR_CRITIQUE : {str(e)}"

        return "ERREUR_CRITIQUE : Impossible de générer la lettre après plusieurs essais."

    def save_latex(self, latex_code: str, filename: str):
        """
        Sauvegarde simplement le code dans un fichier .tex
        """
        if "ERREUR_CRITIQUE" in latex_code:
            return None

        tex_path = f"{filename}.tex"
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
        return tex_path
