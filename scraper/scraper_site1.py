"""
scraper_site1.py - Groupe 2 : Module de scraping pour LinkedIn Jobs.

Ce module définit la fonction scrape_offers() permettant de récupérer des offres
d'emploi sur LinkedIn via Selenium. Le format de sortie est standardisé pour être
intégré par le bot Discord (bot.py).

Structure des données retournées :
[
    {
        "title": str,        # Titre de l'offre
        "company": str,      # Nom de l'entreprise
        "location": str,     # Ville/Région
        "description": str,  # Texte complet de l'offre
        "url": str           # Lien direct vers l'offre
    },
    ...
]

Maintenance : Les sélecteurs CSS utilisés ici sont sujets à changement par LinkedIn.
"""

from urllib.parse import quote
import time
import logging  # Importation de la bibliothèque standard pour une journalisation professionnelle

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# --- CONFIGURATION DE LA JOURNALISATION (LOGGING) ---
# En production, on utilise les logs plutôt que les 'print' pour ne pas polluer la console du bot.
# Ce format inclut l'heure, le niveau d'erreur, et le message.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# --- CONSTANTES ---
# Nombre maximal d'offres à récupérer lors d'une recherche (pour limiter le temps d'exécution).
MAX_OFFERS = 5


def clean_text(text: str) -> str:
    """Nettoie une chaîne de caractères en supprimant les espaces superflus et retours à la ligne."""
    return " ".join(text.split()) if text else ""


def safe_text(parent, selectors: list) -> str:
    """
    Essaie plusieurs sélecteurs CSS sur un élément parent pour extraire son texte.
    Tente de récupérer .text puis .textContent si nécessaire.
    """
    for selector in selectors:
        try:
            el = parent.find_element(By.CSS_SELECTOR, selector)
            
            # Tentative 1 : Récupération du texte visible
            text = el.text.strip()
            if text:
                return clean_text(text)
            
            # Tentative 2 : Récupération du contenu texte brut (caché ou non)
            text_content = el.get_attribute("textContent")
            if text_content:
                return clean_text(text_content)
                
        except (NoSuchElementException, Exception):
            # Échec silencieux si le sélecteur ne correspond à rien, on tente le suivant
            continue
    return ""


def close_popups(driver: webdriver.Chrome) -> None:
    """
    Ferme les popups de cookies et d'identification qui bloquent l'interface.
    Utilise WebDriverWait au lieu de time.sleep() pour plus d'efficacité.
    """
    # XPATHs pour les différents boutons d'acceptation de cookies possibles.
    cookie_xpaths = [
        "//button[contains(., 'Accepter')]",
        "//button[contains(., 'Accept')]",
        "//button[contains(., 'Tout accepter')]",
        "//button[contains(., 'Refuser')]",
    ]
    
    # Tentative de fermeture des cookies.
    for xp in cookie_xpaths:
        try:
            # On attend maximum 2 secondes que le bouton soit cliquable (rapide si présent).
            btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            btn.click()
            # Si un clic réussit, on suppose que les cookies sont gérés et on quitte la boucle.
            break
        except TimeoutException:
            # Le bouton n'est pas apparu dans les 2s, on tente le XPATH suivant.
            continue
        except Exception:
            continue

    # XPATHs pour les boutons de fermeture des popups d'identification (overlay modal).
    close_xpaths = [
        "//button[@aria-label='Dismiss']",
        "//button[@aria-label='Fermer']",
        "//button[@aria-label='Close']",
        "//button[contains(@class, 'contextual-sign-in-modal__modal-dismiss-icon')]",
        "//button[contains(@class, 'modal__dismiss')]",
    ]

    # Tentative de fermeture des modales d'identification.
    for xp in close_xpaths:
        try:
            # On attend maximum 2 secondes.
            btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            btn.click()
            break
        except TimeoutException:
            continue
        except Exception:
            continue


def get_description_text(driver: webdriver.Chrome) -> str:
    """
    Extrait le texte de la description complète d'une offre sur sa page détaillée.
    Utilise WebDriverWait pour s'assurer du chargement de la description.
    """
    # Sélecteurs CSS connus pour contenir la description complète.
    selectors = [
        "div.show-more-less-html__markup",
        "div.description__text",
        "section.show-more-less-html",
        "div.jobs-description__content",
        "div.jobs-box__html-content",
    ]

    # Parcours des sélecteurs pour trouver l'élément.
    for selector in selectors:
        try:
            # On attend jusqu'à 5 secondes que l'élément soit présent dans le DOM.
            el = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # On privilégie textContent car la description peut être partiellement masquée visuellement.
            text_content = el.get_attribute("textContent")
            if text_content:
                return clean_text(text_content)
                
        except TimeoutException:
            # L'élément n'est pas apparu dans les 5s, on tente le sélecteur suivant.
            continue
        except Exception:
            continue

    # Retourne une chaîne vide si aucun sélecteur n'a fonctionné.
    return ""


def scrape_offers(job_type: str, location: str) -> list:
    """
    Fonction principale lancée par bot.py pour récupérer des offres LinkedIn.
    Se connecte, effectue la recherche, et extrait les données.
    """
    logger.info(f"Début de la récupération des offres pour '{job_type}' à '{location}'.")
    offers = []
    driver = None

    # --- Étape 1: Configuration du navigateur ---
    try:
        # Encodage des paramètres pour l'URL de recherche.
        keywords_encoded = quote(job_type)
        location_encoded = quote(location)

        # Construction de l'URL de recherche LinkedIn sans connexion.
        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={keywords_encoded}&location={location_encoded}"
        )

        options = Options()
        
        # --- RECOMMANDATION P1 : MODE HEADLESS ACTIVÉ ---
        # Nécessaire pour l'exécution sur un serveur sans interface graphique.
        options.add_argument("--headless=new") 
        
        # Options supplémentaires pour maximiser la compatibilité en production.
        options.add_argument("--no-sandbox") # Recommandé pour l'exécution sous Linux (serveurs)
        options.add_argument("--disable-dev-shm-usage") # Évite les problèmes de mémoire partagée
        options.add_argument("--log-level=3") # Masque les erreurs non critiques de Chrome dans les logs

        # Initialisation du driver Chrome.
        driver = webdriver.Chrome(options=options)
        driver.maximize_window() # Important pour que Selenium voie tous les éléments
        
        # --- Étape 2: Navigation et gestion des popups ---
        driver.get(search_url)

        # Instance de WebDriverWait utilisée pour toutes les attentes de cette fonction.
        wait = WebDriverWait(driver, 15)
        
        # RECOMMANDATION P2: On attend que le body soit présent plutôt qu'un sleep fixe.
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            logger.warning("Temps d'attente dépassé pour le chargement initial de la page.")

        # Tentative de fermeture des popups cookies/login avant l'analyse.
        close_popups(driver)

        # --- Étape 3: Analyse de la page de recherche ---
        # On s'assure qu'au moins une carte d'offre est chargée avant de scanner.
        try:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.base-search-card"))
            )
        except TimeoutException:
            logger.warning("Aucune carte d'offre n'a été détectée dans le temps imparti.")
            return [] # On retourne une liste vide tout de suite.

        # Récupération de tous les éléments de carte d'offre présents sur la page.
        cards = driver.find_elements(By.CSS_SELECTOR, "div.base-search-card")
        logger.info(f"{len(cards)} cartes d'offres détectées sur la page.")

        # --- Étape 4: Extraction des informations visibles (Titres, Entreprises, etc.) ---
        # Limité aux MAX_OFFERS premières pour la performance.
        for card in cards[:MAX_OFFERS]:
            # Utilisation de safe_text pour gérer la diversité des sélecteurs.
            title = safe_text(card, [
                "h3.base-search-card__title",
                "h3",
                ".base-search-card__title",
            ])

            company = safe_text(card, [
                "h4.base-search-card__subtitle",
                "h4",
                ".base-search-card__subtitle",
            ])

            job_location = safe_text(card, [
                "span.job-search-card__location",
                ".job-search-card__location",
                "span[class*='location']",
            ])

            # Extraction spécifique du lien href vers l'offre détaillée.
            try:
                job_url = card.find_element(
                    By.CSS_SELECTOR, "a.base-card__full-link"
                ).get_attribute("href")
            except NoSuchElementException:
                # Si le lien n'existe pas, l'offre ne peut pas être analysée en détail.
                job_url = ""

            # Ajout temporaire de l'offre, description vide pour l'instant.
            offers.append({
                "title": title,
                "company": company,
                "location": job_location,
                "description": "",
                "url": job_url,
            })

        logger.info(f"{len(offers)} offres de base extraites.")

        # --- Étape 5: Extraction des descriptions détaillées (Visite individuelle) ---
        # Parcours de chaque offre récupérée précédemment.
        for offer in offers:
            # Si aucune URL n'a été trouvée pour l'offre, on passe à la suivante.
            if not offer["url"]:
                continue
                
            try:
                # Navigation vers la page détaillée de l'offre.
                driver.get(offer["url"])
                
                # RECOMMANDATION P2: On minimise les sleeps et on utilise WebDriverWait.
                # Un court temps mort peut être nécessaire pour l'apparition des popups.
                time.sleep(1) 
                
                # LinkedIn affiche souvent un popup de connexion sur ces pages.
                close_popups(driver)
                
                # Tentative d'extraction de la description complète.
                offer["description"] = get_description_text(driver)
                
                # Petite pause pour ne pas surcharger le serveur de LinkedIn.
                time.sleep(1) 

            except Exception as e:
                # RECOMMANDATION P3: Journalisation professionnelle de l'erreur au lieu de print.
                logger.error(f"Échec de récupération de la description pour {offer['url']}: {e}")
                offer["description"] = "Impossible de récupérer la description."

    except Exception as e:
        # Journalisation de l'erreur globale au cours du processus.
        logger.critical(f"Erreur critique dans scrape_offers: {e}")

    finally:
        # --- Étape 6: Fermeture du navigateur ---
        # Assure la fermeture de Chrome, même si une erreur critique survient.
        if driver is not None:
            driver.quit()
            logger.info("Navigateur Chrome fermé.")

    # Retour de la liste finale d'offres structurées au bot Discord.
    logger.info(f"Récupération terminée. {len(offers)} offres retournées.")
    return offers
 
if __name__ == "__main__":
    # Test avec des exemples
    job = "developpeur"
    location = "Paris"
    
    print(f"Recherche d'offres pour : {job} à {location}")
    results = scrape_offers(job, location)
    
    print(f"\n[SUCCES] {len(results)} offres trouvees :\n")
    
    for i, offer in enumerate(results, 1):
        print(f"--- Offre {i} ---")
        print(f"Titre: {offer['title']}")
        print(f"Entreprise: {offer['company']}")
        print(f"Lieu: {offer['location']}")
        print(f"URL: {offer['url']}")
        if offer['description']:
            print(f"Description: {offer['description'][:200]}...")
        print()
