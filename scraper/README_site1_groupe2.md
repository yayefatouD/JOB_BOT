# Module de Scraping - Site 1 - Groupe 2 (LinkedIn)

## Description du module
Ce dossier contient le moteur de recherche et d'extraction de données développé par le Groupe 2. Son rôle exclusif est de naviguer de manière automatisée sur LinkedIn Jobs, de rechercher des offres correspondant à des critères spécifiques, et de renvoyer ces données formatées pour être exploitées par le bot Discord.

## Architecture et Fonctionnement
Le script principal `scraper_site1.py` s'appuie sur Selenium WebDriver configuré en mode "Headless" (exécution en arrière-plan sans interface graphique) pour garantir sa compatibilité avec un hébergement sur serveur.

Le processus de scraping s'exécute en 5 phases distinctes :
1. **Génération de la requête :** Encodage des paramètres métiers et géographiques transmis par l'utilisateur pour forger l'URL de recherche LinkedIn.
2. **Navigation et Nettoyage :** Chargement de la page et exécution de scripts permettant de détecter et de fermer les fenêtres modales bloquantes (bannières de cookies, popups d'authentification).
3. **Scan global :** Identification des cartes d'offres d'emploi sur la page de résultats et extraction des métadonnées primaires (Titre, Entreprise, Localisation, URL).
4. **Scan approfondi :** Itération sur chaque URL récupérée pour visiter la page spécifique de l'offre et en extraire la description complète de manière sécurisée (gestion des éléments partiellement masqués).
5. **Formatage :** Nettoyage des chaînes de caractères et structuration des résultats.

## Packages et Dépendances
Pour fonctionner correctement, ce module requiert l'installation de bibliothèques tierces.

**Packages externes (à installer) :**
- `selenium` : Pour l'automatisation du navigateur Chrome.
  Installation : `pip install selenium`

**Bibliothèques natives Python utilisées (aucune installation requise) :**
- `urllib.parse` : Pour l'encodage des paramètres URL.
- `time` : Pour la gestion des pauses courtes entre les requêtes.
- `logging` : Pour la journalisation des événements et erreurs en production.

## Structure des données (Sortie)
La fonction principale retourne systématiquement une liste de dictionnaires respectant le schéma de données suivant, attendu par le module de publication :

[
    {
        "title": "Nom du poste",
        "company": "Nom de l'entreprise",
        "location": "Lieu de l'offre",
        "description": "Contenu textuel intégral de l'annonce",
        "url": "Lien hypertexte direct vers l'offre"
    }
]

## Pré-requis techniques matériels
L'environnement exécutant ce script doit disposer des éléments suivants :
- Python 3.8 ou supérieur
- Navigateur Google Chrome installé sur le système hôte (requis par Selenium)

## Utilisation et Intégration
Ce module est conçu pour agir comme une bibliothèque interne. Il ne doit pas être exécuté directement en tant que script autonome en production.

Exemple d'intégration dans le fichier principal de l'application :

from scraper.scraper_site1 import scrape_offers

# Appel de la fonction avec paramètres
resultats = scrape_offers("Data Analyst", "Paris")


## Maintenance et Points d'attention
- **Vulnérabilité des sélecteurs :** L'extraction des données repose sur la lecture de classes CSS spécifiques à LinkedIn (ex: `.base-search-card`). Une mise à jour de l'interface graphique de la plateforme nécessitera une actualisation de ces sélecteurs dans le code. Plusieurs sélecteurs de secours (fallbacks) sont déjà implémentés pour limiter ce risque.
- **Journalisation (Logging) :** Pour faciliter le débogage en production sans polluer la sortie standard de l'application principale, le module utilise la bibliothèque `logging` de Python. Les erreurs de timeout ou les éléments introuvables sont tracés silencieusement.
- **Limitations de trafic :** Le code limite volontairement l'extraction aux premières offres (paramètre MAX_OFFERS) pour maintenir un temps de réponse acceptable et éviter le déclenchement des sécurités anti-bot de LinkedIn.
