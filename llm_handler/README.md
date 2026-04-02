# LLM Handler(Groupe 5)

Ce module est une brique logicielle autonome conçue pour analyser un CV, identifier l'offre d'emploi la plus pertinente parmi une liste, et générer une lettre de motivation personnalisée au format **LaTeX**.

## Fonctionnalités

* **Analyse Sémantique** : Utilisation de `Sentence-BERT` (modèle multilingue) pour calculer la similarité entre le CV et les offres.
* **Génération par IA** : Rédaction structurée via `Gemini 2.5 Flash` en suivant la méthode "Vous-Moi-Nous".
* **Sortie LaTeX** : Production d'un code source `.tex` complet, prêt à être compilé dans Overleaf.
* **Système de Cache** : Optimisation des performances via la mise en cache des embeddings locaux.

---

## 🛠️ Installation

1.  **Cloner le projet** (assurez-vous d'avoir le dossier `llm_handler` à la racine).
2.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuration des clés API** :
    * Copiez le fichier `.env.example` et renommez-le en `.env`.
    * Ajoutez votre clé API Gemini :
        ```text
        GEMINI_API_KEY=votre_cle_ici
        ```

---

## Guide d'intégration dans le bot.py (Pour le groupe 1)

Le module a été conçu pour être intégré facilement dans le `bot.py` principal. Voici comment l'appeler :

```python
from llm_handler.embeddings import EmbeddingEngine
from llm_handler.generator import LetterGenerator

# Prenez la trame dans le fichier main (posté à la racine du projet)

# 1. Initialisation (à faire une seule fois au lancement du bot)
engine = EmbeddingEngine()
generator = LetterGenerator()

# 2. Matching (Entrée : texte du CV + Liste des descriptions d'offres)
# Retourne l'index de la meilleure offre et son score de similarité
cv_emb = engine.encode(cv_text)
job_embs = engine.encode(df_jobs["description"].tolist())
results = engine.find_similar(cv_emb, job_embs, top_k=1)

best_job = df_jobs.iloc[results[0]["index"]]

# 3. Génération de la lettre en LaTeX
lettre_latex = generator.generate(cv_text, best_job["description"])

# 4. Sauvegarde locale (Optionnel)
generator.save_latex(lettre_latex, "nom_du_fichier") 
