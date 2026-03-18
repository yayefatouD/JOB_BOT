"""
scraper_site2.py - Groupe 3 : Scraping du site 2 (Scraping de Welcome to the Jungle)

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
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


def clean_text(text: str) -> str:
    """Nettoie un texte en supprimant les blocs parasites de WTTJ."""
    if not text:
        return ""
    text = re.sub(r"D['']autres offres.*", "", text, flags=re.DOTALL)
    text = re.sub(r"Voir plus\s*$", "", text, flags=re.MULTILINE)
    return " ".join(text.split())


def get_description(driver) -> str:
    """Récupère la description d'une offre depuis la page de détail WTTJ."""
    desc, prof = [], []
    DESC_KW = {"poste", "mission", "description", "rôle", "role", "responsabilit"}
    PROF_KW = {"profil", "vous", "candidat", "compétence", "expérience", "requis"}

    for section in driver.find_elements(By.CSS_SELECTOR, "section, [data-testid*='section']"):
        try:
            header = section.find_element(By.CSS_SELECTOR, "h2,h3,h4").text.lower()
        except:
            continue
        if any(k in header for k in DESC_KW):
            desc.append(section.text.strip())
        elif any(k in header for k in PROF_KW):
            prof.append(section.text.strip())

    if not desc:
        for sel in ["[data-testid*='description']", "article", "main"]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.text.strip():
                    desc.append(el.text.strip())
                    break
            except:
                pass

    return clean_text("\n\n".join(desc + prof))


def scrape_offers(job_type: str, location: str) -> list:
    """Scrape les offres WTTJ selon un mot-clé et une localisation."""
    offers = []
    driver = None

    try:
        search_url = (
            "https://www.welcometothejungle.com/fr/jobs"
            f"?refinementList%5Boffices.country_code%5D%5B%5D=FR&query={quote(job_type)}"
        )

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        driver.get(search_url)

        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/jobs/']"))
        )
        time.sleep(3)

        # Collecte des liens d'offres
        links = []
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            try:
                href = a.get_attribute("href") or ""
                if re.search(r"/companies/.+/jobs/", href) and href not in links:
                    links.append(href)
                    if len(links) >= 30:
                        break
            except:
                pass

        # Scraping de chaque offre
        for url in links:
            try:
                driver.get(url)
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2, main"))
                )
                time.sleep(2)

                title = ""
                for sel in ["h1", "h2", "[data-testid*='title']"]:
                    try:
                        el = driver.find_element(By.CSS_SELECTOR, sel)
                        if el.text.strip():
                            title = el.text.strip()
                            break
                    except:
                        pass

                company = re.search(r"/companies/([^/]+)/", url)
                company = company.group(1).replace("-", " ").title() if company else ""

                city = re.search(r"_([a-zà-ü\-]+)(?:_[A-Z]{2,}|$)", url)
                city = city.group(1).replace("-", " ").title() if city else ""

                if not title or not company:
                    continue

                offers.append({
                    "title":       title,
                    "company":     company,
                    "location":    city,
                    "description": get_description(driver),
                    "url":         url,
                })

                time.sleep(2)

            except Exception:
                continue

    except Exception as e:
        print("Erreur dans scrape_offers :", e)

    finally:
        if driver is not None:
            driver.quit()

    return offers
