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

Sorties fichiers :
- offers.json : fichier principal lu par le Groupe 5 (llm_handler.py)
- offers.csv  : export optionnel pour consultation humaine (tableur, etc.)
"""

from urllib.parse import quote
import time
import logging
import json
import csv
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# --- CONFIGURATION DE LA JOURNALISATION (LOGGING) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# --- CONSTANTES ---
MAX_OFFERS = 5

# Le Groupe 5 doit lire depuis ce même chemin.
OUTPUT_DIR = Path(__file__).parent.parent  # racine du projet : bot-emploi-discord/
OUTPUT_JSON = OUTPUT_DIR / "offers.json"
OUTPUT_CSV  = OUTPUT_DIR / "offers.csv"


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
            text = el.text.strip()
            if text:
                return clean_text(text)
            text_content = el.get_attribute("textContent")
            if text_content:
                return clean_text(text_content)
        except (NoSuchElementException, Exception):
            continue
    return ""


def close_popups(driver: webdriver.Chrome) -> None:
    """
    Ferme les popups de cookies et d'identification qui bloquent l'interface.
    """
    cookie_xpaths = [
        "//button[contains(., 'Accepter')]",
        "//button[contains(., 'Accept')]",
        "//button[contains(., 'Tout accepter')]",
        "//button[contains(., 'Refuser')]",
    ]
    for xp in cookie_xpaths:
        try:
            btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            btn.click()
            break
        except TimeoutException:
            continue
        except Exception:
            continue

    close_xpaths = [
        "//button[@aria-label='Dismiss']",
        "//button[@aria-label='Fermer']",
        "//button[@aria-label='Close']",
        "//button[contains(@class, 'contextual-sign-in-modal__modal-dismiss-icon')]",
        "//button[contains(@class, 'modal__dismiss')]",
    ]
    for xp in close_xpaths:
        try:
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
    """
    selectors = [
        "div.show-more-less-html__markup",
        "div.description__text",
        "section.show-more-less-html",
        "div.jobs-description__content",
        "div.jobs-box__html-content",
    ]
    for selector in selectors:
        try:
            el = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            text_content = el.get_attribute("textContent")
            if text_content:
                return clean_text(text_content)
        except TimeoutException:
            continue
        except Exception:
            continue
    return ""


# ---------------------------------------------------------------------------
# EXPORT : fonctions de sauvegarde vers fichiers partagés
# ---------------------------------------------------------------------------

def save_to_json(offers: list) -> None:
    """
    Sauvegarde la liste d'offres dans offers.json (fichier principal pour le Groupe 5).

    Format : tableau JSON avec les clés title, company, location, description, url.
    Encodage UTF-8, indenté pour lisibilité.
    """
    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(offers, f, ensure_ascii=False, indent=2)
        logger.info(f"Offres sauvegardées dans {OUTPUT_JSON} ({len(offers)} entrées).")
    except OSError as e:
        logger.error(f"Impossible d'écrire {OUTPUT_JSON} : {e}")


def save_to_csv(offers: list) -> None:
    """
    Sauvegarde la liste d'offres dans offers.csv (export optionnel, lecture humaine).

    Colonnes : title, company, location, url, description
    La description est placée en dernière colonne car elle peut être longue.
    Encodage UTF-8-BOM pour compatibilité Excel.
    """
    if not offers:
        return
    fieldnames = ["title", "company", "location", "url", "description"]
    try:
        with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(offers)
        logger.info(f"Offres sauvegardées dans {OUTPUT_CSV} ({len(offers)} entrées).")
    except OSError as e:
        logger.error(f"Impossible d'écrire {OUTPUT_CSV} : {e}")


# ---------------------------------------------------------------------------
# SCRAPING PRINCIPAL
# ---------------------------------------------------------------------------

def scrape_offers(job_type: str, location: str) -> list:
    """
    Fonction principale lancée par bot.py pour récupérer des offres LinkedIn.
    Se connecte, effectue la recherche, extrait les données, puis les sauvegarde
    dans offers.json (et offers.csv en bonus).

    Retourne également la liste pour usage direct par bot.py si nécessaire.
    """
    logger.info(f"Début de la récupération des offres pour '{job_type}' à '{location}'.")
    offers = []
    driver = None
    seen_urls = set()
    
    try:
        keywords_encoded = quote(job_type)
        location_encoded = quote(location)
        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={keywords_encoded}&location={location_encoded}"
        )

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=options)
        driver.get(search_url)

        wait = WebDriverWait(driver, 15)
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            logger.warning("Temps d'attente dépassé pour le chargement initial de la page.")

        close_popups(driver)

        try:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.base-search-card"))
            )
        except TimeoutException:
            logger.warning("Aucune carte d'offre n'a été détectée dans le temps imparti.")
            return []

        cards = driver.find_elements(By.CSS_SELECTOR, "div.base-search-card")
        logger.info(f"{len(cards)} cartes d'offres détectées sur la page.")

        for card in cards[:MAX_OFFERS]:
            title = safe_text(card, [
                "h3.base-search-card__title", "h3", ".base-search-card__title",
            ])
            company = safe_text(card, [
                "h4.base-search-card__subtitle", "h4", ".base-search-card__subtitle",
            ])
            job_location = safe_text(card, [
                "span.job-search-card__location",
                ".job-search-card__location",
                "span[class*='location']",
            ])
            try:
                job_url = card.find_element(
                    By.CSS_SELECTOR, "a.base-card__full-link"
                ).get_attribute("href")
            except NoSuchElementException:
                job_url = ""
                
            if job_url and job_url in seen_urls:
               continue
            if job_url:
               seen_urls.add(job_url)
                
            if len(offers) >= MAX_OFFERS:
               break    
            if not title and not company and not job_location and not job_url:
               continue    
                
            offers.append({
                "title": title,
                "company": company,
                "location": job_location,
                "description": "",
                "url": job_url,
            })

        logger.info(f"{len(offers)} offres de base extraites.")

        for offer in offers:
            if not offer["url"]:
                continue
            try:
                driver.get(offer["url"])
                time.sleep(1)
                close_popups(driver)
                offer["description"] = get_description_text(driver)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Échec de récupération de la description pour {offer['url']}: {e}")
                offer["description"] = "Impossible de récupérer la description."

    except Exception as e:
        logger.critical(f"Erreur critique dans scrape_offers: {e}")

    finally:
        if driver is not None:
            driver.quit()
            logger.info("Navigateur Chrome fermé.")

    # --- SAUVEGARDE FICHIERS ---
    # Toujours exécutée, même si la liste est partielle.
    save_to_json(offers)
    save_to_csv(offers)   # Supprimer cette ligne si le CSV n'est pas utile.

    logger.info(f"Récupération terminée. {len(offers)} offres retournées.")
    return offers


if __name__ == "__main__":
    job = "developpeur"
    location = "Paris"

    print(f"Recherche d'offres pour : {job} à {location}")
    results = scrape_offers(job, location)

    print(f"\n[SUCCES] {len(results)} offres trouvees.")
    print(f"Fichiers générés : {OUTPUT_JSON} | {OUTPUT_CSV}")

    for i, offer in enumerate(results, 1):
        print(f"\n--- Offre {i} ---")
        print(f"Titre      : {offer['title']}")
        print(f"Entreprise : {offer['company']}")
        print(f"Lieu       : {offer['location']}")
        print(f"URL        : {offer['url']}")
        if offer['description']:
            print(f"Description: {offer['description'][:200]}...")
