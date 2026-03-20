# Groupe 3 — Scraping Welcome to the Jungle (WTTJ)

**Membres :** Konan Lozo · Agossou Abla · Feriel · Hiba

---

## 🎯 Objectif

Ce module collecte des offres d'emploi depuis le site **Welcome to the Jungle** et les transmet au bot Discord sous forme de dictionnaire structuré, prêt à être exploité par les autres groupes (analyse CV, génération de lettre de motivation).

---

## 📁 Fichier concerné

```
scraper_wttj.py
```

---

## ⚙️ Fonctionnement

Le script utilise **Selenium** pour piloter un navigateur Chrome, car WTTJ charge son contenu dynamiquement via JavaScript (une requête HTTP classique ne suffit pas).

### Étapes principales

1. Construction de l'URL de recherche à partir des mots-clés et de la localisation
2. Lancement de Chrome avec des options anti-détection bot
3. Scroll infini sur la page de résultats pour collecter jusqu'à **100 liens d'offres**
4. Visite individuelle de chaque offre pour en extraire le contenu
5. Retour d'un dictionnaire structuré

---

## 📦 Format de sortie

La fonction principale `scrape_offres()` retourne un **dictionnaire Python** :

```python
{
    "source": "Welcome to the Jungle",
    "mots_cles": "Data Analyst",
    "localisation": "Paris",
    "nombre_offres": 87,
    "offres": [
        {
            "titre": "Data Analyst",
            "entreprise": "Acme Corp",
            "lieu": "Paris",
            "description": "...",
            "url": "https://www.welcometothejungle.com/..."
        },
        ...
    ]
}
```

En cas d'erreur, le dictionnaire contient uniquement une clé `"erreur"` :

```python
{ "erreur": "Les mots-clés sont obligatoires." }
```

---

## 🔌 Intégration dans bot.py

La seule fonction à appeler depuis `bot.py` est :

```python
from scraper_wttj import scrape_offres

resultats = scrape_offres(mots_cles="Data Analyst", localisation="Paris")
```

---

## 🛠️ Installation

Assurez-vous d'avoir activé l'environnement virtuel commun, puis installez les dépendances :

```bash
pip install selenium
```

> **Google Chrome** doit être installé sur la machine, ainsi que le **ChromeDriver** correspondant à votre version de Chrome.
> Vérifiez votre version Chrome : `chrome://settings/help`, puis téléchargez le driver sur [chromedriver.chromium.org](https://chromedriver.chromium.org).

Pensez à mettre à jour `requirements.txt` après installation et à prévenir les autres groupes sur Discord.

---

## ▶️ Test rapide en ligne de commande

```bash
python scraper_wttj.py
```

Le script demandera les mots-clés et la ville, puis affichera les résultats dans le terminal.

---

## ⚠️ Points d'attention

| Sujet | Détail |
|---|---|
| **Temps d'exécution** | Compter ~15-30 min pour 100 offres (chaque page est visitée individuellement) |
| **Détection anti-bot** | Le script simule un vrai navigateur, mais WTTJ peut bloquer en cas d'abus |
| **Localisation** | Le filtre géographique est indicatif, WTTJ peut retourner des offres hors zone |
| **Nombre d'offres** | Le site n'affiche pas toujours 100 offres selon les mots-clés recherchés |

---

## 🔧 Configuration rapide

Les constantes en haut du fichier permettent d'ajuster le comportement sans toucher à la logique :

```python
MAX_OFFRES      = 100  # Nombre max d'offres à collecter
SCROLL_PAUSE    = 2    # Pause entre chaque scroll (secondes)
MAX_RETRIES     = 2    # Tentatives en cas d'échec sur une offre
PAGE_LOAD_WAIT  = 25   # Timeout chargement de la liste (secondes)
OFFRE_LOAD_WAIT = 20   # Timeout chargement d'une offre (secondes)
```
