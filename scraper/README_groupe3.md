# Groupe 3 — Scraping Welcome to the Jungle (WTTJ)

**Membres :** KONAN Lozo · AGOSSOU Abla · Feriel BOUKERMA · Hiba DOUMAR

---

## 🎯 Objectif

Ce module collecte des offres d'emploi depuis le site **Welcome to the Jungle** et les transmet au bot Discord sous forme de dictionnaire structuré, prêt à être exploité par les autres groupes (analyse CV, génération de lettre de motivation).

---

## 📁 Fichier concerné

```
scraper_site2.py
```

---

## ⚙️ Fonctionnement

Le script utilise **Selenium** pour piloter un navigateur Chrome, car WTTJ charge son contenu dynamiquement via JavaScript (une requête HTTP classique ne suffit pas).

### Paramètres fixes

| Paramètre | Valeur |
|---|---|
| **Mot-clé de recherche** | `"data"` |
| **Localisation** | France entière |
| **Nombre max d'offres** | 50 |

### Étapes principales

1. Construction de l'URL de recherche (mot-clé `"data"`, France entière)
2. Lancement de Chrome avec des options anti-détection bot
3. Scroll infini sur la page de résultats pour collecter jusqu'à **50 liens d'offres**
4. Visite individuelle de chaque offre pour en extraire le contenu
5. Export automatique en CSV et JSON + retour du dictionnaire structuré

---

## 📦 Format de sortie

### Dictionnaire Python

La fonction principale `scrape_offres()` retourne un **dictionnaire Python** :

```python
{
    "source": "Welcome to the Jungle",
    "mots_cles": "data",
    "localisation": "",
    "nombre_offres": 50,
    "offres": [
        {
            "titre": "Data Engineer",
            "entreprise": "Acme Corp",
            "lieu": "Lyon",
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

### Fichiers exportés

| Fichier | Format | Colonnes |
|---|---|---|
| `offres_grpe3.csv` | CSV | titre, entreprise, lieu, description, url |
| `offres_grpe3.json` | JSON | structure complète du dictionnaire |

---

## 🔌 Intégration dans bot.py

La fonction à appeler depuis `bot.py` est **`scrape_et_exporter()`** — elle lance le scraping, génère automatiquement les fichiers CSV et JSON, et retourne le dictionnaire :

```python
from scraper_site2 import scrape_et_exporter

resultats = scrape_et_exporter()
```

> ⚠️ Ne pas appeler `scrape_offres()` depuis le bot : cette fonction ne génère pas les fichiers d'export.

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
python scraper_site2.py
```

Le script lance directement la recherche sur `"data"` / France entière, affiche les résultats dans le terminal, et génère `offres_grpe3.csv` et `offres_grpe3.json`.

---

## ⚠️ Points d'attention

| Sujet | Détail |
|---|---|
| **Temps d'exécution** | Compter ~8-15 min pour 50 offres (chaque page est visitée individuellement) |
| **Détection anti-bot** | Le script simule un vrai navigateur, mais WTTJ peut bloquer en cas d'abus |
| **Localisation** | Pas de filtre géographique : toutes les offres en France sont remontées |
| **Nombre d'offres** | Le site n'affiche pas toujours 50 offres selon les mots-clés recherchés |

---

## 🔧 Configuration rapide

Les constantes en haut du fichier permettent d'ajuster le comportement sans toucher à la logique :

```python
MAX_OFFRES      = 50   # Nombre max d'offres à collecter
SCROLL_PAUSE    = 2    # Pause entre chaque scroll (secondes)
MAX_RETRIES     = 2    # Tentatives en cas d'échec sur une offre
PAGE_LOAD_WAIT  = 25   # Timeout chargement de la liste (secondes)
OFFRE_LOAD_WAIT = 20   # Timeout chargement d'une offre (secondes)
```
