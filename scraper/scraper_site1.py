"""
scraper_site1.py - Groupe 2 : Scraping du site 1

Format de retour attendu par bot.py :
[
    {
        "title": "Titre du poste",
        "company": "Nom de l'entreprise",
        "location": "Ville",
        "description": "Description complète",
        "url": "lien vers l'offre"
    }, 
    ...
]
"""

from urllib.parse import quote
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def clean_text(text: str) -> str:
    """Nettoie un texte en supprimant les espaces et retours inutiles."""
    return " ".join(text.split()) if text else ""


def safe_text(parent, selectors) -> str:
    """
    Essaie plusieurs sélecteurs CSS pour récupérer le texte d'un élément.
    Retourne une chaîne vide si rien n'est trouvé.
    """
    for selector in selectors:
        try:
            el = parent.find_element(By.CSS_SELECTOR, selector)

            text = el.text.strip()
            if text:
                return clean_text(text)

            text_content = (el.get_attribute("textContent") or "").strip()
            if text_content:
                return clean_text(text_content)
        except:
            pass
    return ""


def close_popups(driver) -> None:
    """Ferme les popups cookies et identification si elles apparaissent."""
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
        except:
            pass

    time.sleep(1)

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
        except Exception:
            pass

    time.sleep(1)


def get_description_text(driver) -> str:
    """
    Récupère la description d'une offre depuis la page de détail LinkedIn.
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

            text = el.text.strip()
            if text:
                return clean_text(text)

            text_content = (el.get_attribute("textContent") or "").strip()
            if text_content:
                return clean_text(text_content)
        except:
            pass

    return ""


from urllib.parse import quote
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def clean_text(text: str) -> str:
    """Nettoie un texte en supprimant les espaces et retours inutiles."""
    return " ".join(text.split()) if text else ""


def safe_text(parent, selectors) -> str:
    """
    Essaie plusieurs sélecteurs CSS pour récupérer le texte d'un élément.
    Retourne une chaîne vide si rien n'est trouvé.
    """
    for selector in selectors:
        try:
            el = parent.find_element(By.CSS_SELECTOR, selector)

            text = el.text.strip()
            if text:
                return clean_text(text)

            text_content = (el.get_attribute("textContent") or "").strip()
            if text_content:
                return clean_text(text_content)
        except:
            pass
    return ""


def close_popups(driver) -> None:
    """Ferme les popups cookies et identification si elles apparaissent."""
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
        except:
            pass

    time.sleep(1)

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
        except:
            pass

    time.sleep(1)


def get_description_text(driver) -> str:
    """
    Récupère la description d'une offre depuis la page de détail LinkedIn.
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

            text = el.text.strip()
            if text:
                return clean_text(text)

            text_content = (el.get_attribute("textContent") or "").strip()
            if text_content:
                return clean_text(text_content)
        except:
            pass

    return ""


def scrape_offers(job_type: str, location: str) -> list:
    """
    TODO Groupe 2 : implémenter avec Selenium

    
    """
    offers = []
    driver = None

    try:
        keywords_encoded = quote(job_type)
        location_encoded = quote(location)

        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={keywords_encoded}&location={location_encoded}"
        )

        options = Options()
        # options.add_argument("--headless=new")  # à activer plus tard si besoin

        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        driver.get(search_url)

        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        close_popups(driver)

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.base-search-card"))
        )

        cards = driver.find_elements(By.CSS_SELECTOR, "div.base-search-card")

        # Première passe : récupérer les informations visibles sur la page de recherche
        for card in cards[:5]:
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

            try:
                job_url = card.find_element(
                    By.CSS_SELECTOR, "a.base-card__full-link"
                ).get_attribute("href")
            except:
                job_url = ""

            offers.append({
                "title": title,
                "company": company,
                "location": job_location,
                "description": "",
                "url": job_url,
            })

        # Deuxième passe : ouvrir chaque offre pour récupérer la description
        for offer in offers:
            if offer["url"]:
                try:
                    driver.get(offer["url"])
                    time.sleep(3)
                    close_popups(driver)
                    time.sleep(2)

                    offer["description"] = get_description_text(driver)

                except Exception as e:
                    print(f"Erreur récupération description pour {offer['url']} : {e}")
                    offer["description"] = ""

    except Exception as e:
        print("Erreur dans scrape_offers :", e)

    finally:
        if driver is not None:
            driver.quit()

    return offers
        
