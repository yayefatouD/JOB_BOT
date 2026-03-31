import os
import pandas as pd
import sys
import unicodedata

# Ajout du répertoire courant au PATH pour l'import des modules locaux
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler.embeddings import EmbeddingEngine
from llm_handler.generator import LetterGenerator

def slugify(text):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower().strip()
    return "".join([c for c in text if c.isalnum() or c == ' ']).replace(' ', '_')

def run_test():
    # Chemins des fichiers
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cv_path = os.path.join(script_dir, "data", "mock_cv_nathan.txt")
    jobs_path = os.path.join(script_dir, "data", "mock_jobs.csv")

    # Vérification de l'existence des données
    if not os.path.exists(cv_path) or not os.path.exists(jobs_path):
        print(f"❌ Erreur : Fichiers manquants dans {os.path.join(script_dir, 'data')}")
        return

    # Lecture des fichiers
    with open(cv_path, "r", encoding="utf-8") as f:
        cv_text = f.read()
    df_jobs = pd.read_csv(jobs_path)

    # Initialisation des moteurs
    engine = EmbeddingEngine()
    generator = LetterGenerator()

    print("1. ANALYSE DU CV ET DES OFFRES")
    print("Calcul des similarités sémantiques...")

    cv_emb = engine.encode(cv_text)
    job_embs = engine.encode(df_jobs["description"].tolist())

    # Recherche du meilleur match
    results = engine.find_similar(cv_emb, job_embs, top_k=1)
    best_job = df_jobs.iloc[results[0]["index"]]
    score = results[0]["score"]

    print(f"✅ Match trouvé : {best_job['title']} (Score : {score:.2f})")

    print("\n--- 2. GÉNÉRATION DE LA LETTRE (GEMINI) ---")
    print("Appel à l'API en cours...")

    # Génération du contenu LaTeX
    lettre_latex = generator.generate(cv_text, best_job["description"])

    # Vérification du résultat
    if "ERREUR_CRITIQUE" in lettre_latex:
        print(f"❌ Échec de la génération : {lettre_latex}")
        return

    print("\n--- 3. SAUVEGARDE DU FICHIER ---")

    # Création d'un nom de fichier propre
    safe_title = slugify(best_job['title'])
    filename = f"lettre_motivation_{safe_title}"

    # Sauvegarde en .tex
    path_tex = generator.save_latex(lettre_latex, filename)

    if path_tex:
        print(f" Succès ! Le code LaTeX a été généré.")
        print(f" Chemin : {os.path.abspath(path_tex)}")
        print("\nVous pouvez maintenant copier ce code dans Overleaf ou le compiler via R.")
        print("-" * 90)
        print("Aperçu du code :\n")
        print(lettre_latex[:200] + "...")
    else:
        print("❌ Erreur lors de l'écriture du fichier .tex")

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur.")
    except Exception as e:
        print(f"\nUne erreur inattendue est survenue : {e}")