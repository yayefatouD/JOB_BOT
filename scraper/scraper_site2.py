"""
Scraping de Welcome to the Jungle

Ce fichier récupère des offres d'emploi depuis le site Welcome to the Jungle (WTTJ).
Il utilise Selenium pour piloter un navigateur Chrome.

Format de retour (dictionnaire) :
{
    "source": "Welcome to the Jungle",
    "mots_cles": "...",
    "localisation": "...",
    "nombre_offres": N,
    "offres": [
        {
            "titre": "Titre du poste",
            "entreprise": "Nom de l'entreprise",
            "lieu": "Ville",
            "description": "Description complète",
            "url": "lien vers l'offre"
        },
        ...
    ]
}
"""

# quote() : encode les caractères spéciaux dans les URLs (ex : "Data Analyst" → "Data%20Analyst")
from urllib.parse import quote
import time
import re

from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,          # L'élément HTML recherché n'existe pas dans la page
    TimeoutException,                # Le délai d'attente a été dépassé sans que la condition soit remplie
    StaleElementReferenceException,  # L'élément existait mais a disparu du DOM depuis (page rechargée)
)


# ---------------------------------------------------------------------------
# Modifier ces valeurs pour ajuster le comportement global du scraper
# ---------------------------------------------------------------------------

MAX_OFFRES      = 100  # Nombre maximum d'offres à collecter au total
SCROLL_PAUSE    = 2    # Secondes à attendre après chaque scroll
OFFRE_PAUSE     = 2    # Secondes à attendre après l'ouverture d'une page d'offre individuelle
MAX_RETRIES     = 2    # Nombre de nouvelles tentatives si une page d'offre échoue à charger
PAGE_LOAD_WAIT  = 25   # Secondes max pour que la liste de résultats apparaisse au démarrage
OFFRE_LOAD_WAIT = 20   # Secondes max pour que le contenu d'une offre individuelle se charge

# URL de base de la page de recherche d'offres WTTJ
BASE_URL = "https://www.welcometothejungle.com/fr/jobs"

# Mots-clés présents dans les titres de sections HTML qui décrivent le poste
# Utilisés pour identifier les blocs "description du poste" dans la page
DESC_KEYWORDS   = {"poste", "mission", "description", "rôle", "role", "responsabilit"}

# Mots-clés présents dans les titres de sections HTML qui décrivent le candidat attendu
# Utilisés pour identifier les blocs "profil recherché" dans la page
PROFIL_KEYWORDS = {"profil", "vous", "candidat", "compétence", "expérience", "requis"}


# ---------------------------------------------------------------------------
# FONCTION : nettoyer_texte
# Rôle : préparer un texte brut issu du DOM pour le stocker proprement
# ---------------------------------------------------------------------------

def nettoyer_texte(texte: str) -> str:
    """
    Nettoie un texte brut extrait d'une page WTTJ.

    Problèmes corrigés :
      - Blocs parasites ("D'autres offres vous correspondent", "Voir plus") ajoutés
        automatiquement par WTTJ en fin de contenu
      - Sauts de ligne multiples qui rendent le texte difficile à lire/stocker
      - Espaces en trop en début et fin de chaîne
    """
    # Si le texte est vide ou None, on retourne une chaîne vide pour éviter les erreurs
    if not texte:
        return ""

    # Supprime tout ce qui suit "D'autres offres" jusqu'à la fin du texte
    # re.DOTALL permet au "." de correspondre aussi aux sauts de ligne
    texte = re.sub(r"D['']autres offres.*", "", texte, flags=re.DOTALL)

    # Supprime "Voir plus" s'il apparaît seul en fin de ligne
    # re.MULTILINE fait que "$" correspond à la fin de chaque ligne (pas seulement la fin du texte)
    texte = re.sub(r"Voir plus\s*$", "", texte, flags=re.MULTILINE)

    # Remplace tous les espaces/tabulations/sauts de ligne consécutifs par un seul espace
    # split() découpe sur tout espace, join(" ") recolle avec un espace simple
    return " ".join(texte.split())


# ---------------------------------------------------------------------------
# FONCTION : extraire_description
# Rôle : récupérer le texte de description d'une offre depuis sa page de détail
# ---------------------------------------------------------------------------

def extraire_description(driver) -> str:
    """
    Extrait la description complète d'une offre depuis la page actuellement ouverte.

    Stratégie en deux étapes :
      1. Cherche des <section> dont le titre contient des mots-clés métier
         (ex : "Missions du poste", "Profil recherché") → méthode précise
      2. Si rien n'est trouvé, utilise des sélecteurs génériques (article, main)
         pour ne pas repartir les mains vides → méthode de secours (fallback)
    """
    blocs_description = []  # Stocke les sections liées au poste
    blocs_profil      = []  # Stocke les sections liées au profil candidat

    # --- Étape 1 : lecture des sections titrées ---
    # On récupère tous les éléments <section> et ceux dont l'attribut data-testid contient "section"
    for section in driver.find_elements(By.CSS_SELECTOR, "section, [data-testid*='section']"):
        try:
            # Récupère le titre de la section (h2, h3 ou h4) en minuscules pour la comparaison
            titre_section = section.find_element(By.CSS_SELECTOR, "h2, h3, h4").text.lower()
        except (NoSuchElementException, StaleElementReferenceException):
            # Pas de titre trouvé dans cette section ou section disparue du DOM → on passe à la suivante
            continue

        # Vérifie si le titre contient un mot-clé de description de poste
        if any(kw in titre_section for kw in DESC_KEYWORDS):
            blocs_description.append(section.text.strip())  # Ajoute le texte complet de la section

        # Vérifie si le titre contient un mot-clé de profil candidat
        elif any(kw in titre_section for kw in PROFIL_KEYWORDS):
            blocs_profil.append(section.text.strip())

    # --- Étape 2 : fallback si aucun bloc description n'a été trouvé ---
    if not blocs_description:
        # On essaie des sélecteurs CSS génériques, dans l'ordre du plus précis au plus large
        for selecteur in ["[data-testid*='description']", "article", "main"]:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selecteur)
                if element.text.strip():  # Vérifie que l'élément contient bien du texte
                    blocs_description.append(element.text.strip())
                    break  # On s'arrête dès le premier sélecteur qui fonctionne
            except NoSuchElementException:
                continue  # Ce sélecteur n'existe pas dans la page, on essaie le suivant

    # Assemble tous les blocs en un seul texte, puis le nettoie avant de le retourner
    texte_complet = "\n\n".join(blocs_description + blocs_profil)
    return nettoyer_texte(texte_complet)


# ---------------------------------------------------------------------------
# FONCTION : extraire_ville_depuis_page
# Rôle : lire la ville directement dans le HTML de la page d'offre (méthode principale)
# ---------------------------------------------------------------------------

def extraire_ville_depuis_page(driver) -> str:
    """
    Cherche la ville dans le contenu HTML de la page d'offre.

    Teste plusieurs sélecteurs CSS dans l'ordre, s'arrête au premier qui fonctionne.
    """
    # Liste des sélecteurs CSS à tester, du plus spécifique au plus générique
    selecteurs_ville = [
        "[data-testid*='location']",  # Attribut data-testid contenant "location"
        "[data-testid*='city']",      # Attribut data-testid contenant "city"
        "address",                    # Balise HTML sémantique <address>
        "li[class*='location']",      # Élément <li> avec une classe contenant "location"
        "span[class*='location']",    # Élément <span> avec une classe contenant "location"
    ]

    for selecteur in selecteurs_ville:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selecteur)
            texte = element.text.strip()
            if texte:
                # WTTJ affiche parfois "Paris · France" ou "Paris\nFrance"
                # On garde uniquement la première partie avant "·" ou le saut de ligne
                return texte.split("\n")[0].split("·")[0].strip()
        except NoSuchElementException:
            continue  # Ce sélecteur n'existe pas dans la page, on passe au suivant

    return ""  # Aucun sélecteur n'a fonctionné : on retourne une chaîne vide


# ---------------------------------------------------------------------------
# FONCTION : extraire_ville_depuis_url
# Rôle : déduire la ville depuis le slug de l'URL (méthode de secours)
# ---------------------------------------------------------------------------

def extraire_ville_depuis_url(url: str) -> str:
    """
    Extrait la ville depuis le slug de l'URL WTTJ quand la page HTML ne suffit pas.

    Structure typique d'une URL WTTJ :
      .../companies/acme/jobs/123456_data-analyst_paris_FR
                                                  ^^^^^
                                                  ville extraite ici

    La regex cherche un groupe de lettres minuscules (avec accents et tirets)
    suivi d'un code pays en majuscules (FR, BE...) ou de la fin de l'URL.
    """
    correspondance = re.search(r"_([a-zà-ü\-]+)(?:_[A-Z]{2,}|$)", url)
    if correspondance:
        # Remplace les tirets par des espaces et met en forme titre (ex : "ile-de-france" → "Ile De France")
        return correspondance.group(1).replace("-", " ").title()
    return ""  # Aucune ville détectable dans l'URL


# ---------------------------------------------------------------------------
# FONCTION : configurer_driver
# Rôle : créer et configurer le navigateur Chrome avant de lancer le scraping
# ---------------------------------------------------------------------------

def configurer_driver() -> webdriver.Chrome:
    """
    Initialise Chrome avec des options pensées pour contourner la détection anti-bot.

    WTTJ (comme beaucoup de sites) bloque les navigateurs automatisés détectés
    via des empreintes JavaScript (navigator.webdriver = true) ou des en-têtes suspects.
    Ces options rendent Chrome moins détectable.
    """
    options = Options()

    # Nécessaire dans les environnements Linux sans interface graphique (serveurs, CI)
    options.add_argument("--no-sandbox")

    # Réduit l'utilisation de la mémoire partagée, évite les crashs sur Linux
    options.add_argument("--disable-dev-shm-usage")

    # Désactive le flag interne qui signale à JavaScript que Chrome est piloté automatiquement
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Lance Chrome en plein écran pour mieux simuler un utilisateur réel
    options.add_argument("--start-maximized")

    # Remplace le user-agent par celui d'un Chrome standard Windows
    # Sans ça, le user-agent contient "HeadlessChrome" ou "Selenium", facilement détectable
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # Supprime les indicateurs visuels d'automatisation dans Chrome (bandeau, icônes)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Désactive l'extension interne d'automatisation de Chrome
    options.add_experimental_option("useAutomationExtension", False)

    # Crée le driver Chrome avec toutes les options configurées ci-dessus
    driver = webdriver.Chrome(options=options)

    # Injecte du JavaScript exécuté à chaque nouveau chargement de page
    # Ce script redéfinit navigator.webdriver pour retourner undefined au lieu de true
    # Certains sites vérifient cette propriété pour détecter Selenium
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    return driver  # Retourne le driver prêt à être utilisé


# ---------------------------------------------------------------------------
# FONCTION : collecter_liens_offres
# Rôle : faire défiler la page de résultats et récupérer les URLs des offres
# ---------------------------------------------------------------------------

def collecter_liens_offres(driver, max_offres: int = MAX_OFFRES) -> list:
    """
    Collecte les liens vers les offres d'emploi depuis la page de résultats WTTJ.

    Pourquoi scroller ?
      WTTJ utilise le "scroll infini" : les offres ne sont pas toutes chargées
      d'un coup, elles apparaissent au fur et à mesure que l'utilisateur descend.
      Le script simule ce scroll pour forcer le chargement des offres suivantes.

    Protection contre les doublons :
      Un set() (ensemble) est utilisé pour stocker les URLs, ce qui garantit
      automatiquement qu'aucune URL n'est collectée deux fois.
    """
    liens_collectes  = set()  # Ensemble d'URLs uniques (les doublons sont ignorés automatiquement)
    derniere_hauteur = 0      # Mémorise la hauteur de page précédente pour détecter la fin du scroll

    print(f"  Collecte des liens (objectif : {max_offres} offres)...")

    # Continue à scroller tant qu'on n'a pas atteint le nombre d'offres souhaité
    while len(liens_collectes) < max_offres:

        # Parcourt tous les liens <a> visibles dans la page à ce stade du scroll
        for element_a in driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            try:
                href = element_a.get_attribute("href") or ""
                # Vérifie que le lien correspond bien au format d'une offre WTTJ :
                # /companies/<slug-entreprise>/jobs/<slug-offre>
                if re.search(r"/companies/.+/jobs/", href):
                    liens_collectes.add(href)  # Le set ignore automatiquement les doublons
            except StaleElementReferenceException:
                # L'élément a été retiré du DOM pendant qu'on l'analysait (rechargement JS)
                continue

        # Si l'objectif est déjà atteint, inutile de scroller davantage
        if len(liens_collectes) >= max_offres:
            break

        # Récupère la hauteur totale actuelle de la page (en pixels) avant de scroller
        nouvelle_hauteur = driver.execute_script("return document.body.scrollHeight")

        # Simule un scroll jusqu'en bas de la page via JavaScript
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Attend que le contenu dynamique déclenché par le scroll se charge
        time.sleep(SCROLL_PAUSE)

        # Récupère la hauteur de la page après le scroll et la pause
        nouvelle_hauteur_apres = driver.execute_script("return document.body.scrollHeight")

        # Si la hauteur n'a pas changé, on est arrivé au bas de la page : plus rien à charger
        if nouvelle_hauteur_apres == derniere_hauteur:
            print(f"  Bas de page atteint ({len(liens_collectes)} liens collectés).")
            break

        # Met à jour la hauteur de référence pour la prochaine itération
        derniere_hauteur = nouvelle_hauteur_apres
        print(f"  {len(liens_collectes)} liens collectés, scroll en cours...")

    # Convertit le set en liste (plus pratique pour itérer avec un index)
    # Tronque à max_offres au cas où on en aurait collecté légèrement plus
    return list(liens_collectes)[:max_offres]


# ---------------------------------------------------------------------------
# FONCTION : scraper_offre
# Rôle : ouvrir la page d'une offre individuelle et en extraire toutes les données
# ---------------------------------------------------------------------------

def scraper_offre(driver, url: str) -> dict | None:
    """
    Visite la page d'une offre WTTJ et extrait ses informations clés.

    Gestion des erreurs :
      Si la page met trop de temps à charger (TimeoutException), le script
      réessaie jusqu'à MAX_RETRIES fois avant d'abandonner cette offre.
      Toute autre erreur abandonne immédiatement l'offre sans planter le programme.

    Retourne None si les données minimales (titre + entreprise) sont introuvables.
    """
    # Boucle de retry : tente MAX_RETRIES fois en cas de timeout
    for tentative in range(1, MAX_RETRIES + 1):
        try:
            # Ouvre la page de l'offre dans le navigateur
            driver.get(url)

            # Attend que le navigateur ait fini d'exécuter tout le JavaScript de la page
            # document.readyState == "complete" signifie que tout le contenu est chargé
            WebDriverWait(driver, OFFRE_LOAD_WAIT).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Attend en plus qu'au moins un élément de contenu soit présent dans le DOM
            # (h1 = titre principal, h2 = titre secondaire, main = contenu principal)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2, main"))
            )

            # Pause supplémentaire pour laisser les éléments dynamiques se rendre complètement
            time.sleep(OFFRE_PAUSE)


            # --- Extraction du titre du poste ---
            titre = ""
            # Teste les sélecteurs dans l'ordre du plus précis (h1) au moins précis
            for selecteur in ["h1", "h2", "[data-testid*='title']"]:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selecteur)
                    if element.text.strip():        # Vérifie que le texte n'est pas vide
                        titre = element.text.strip()
                        break                       # On s'arrête au premier titre trouvé
                except NoSuchElementException:
                    continue                        # Ce sélecteur n'existe pas, on passe au suivant


            # --- Extraction du nom de l'entreprise ---
            # Méthode principale : extraire depuis l'URL, plus fiable que la page
            # Les URLs WTTJ suivent le format : /companies/<nom-entreprise>/jobs/...
            correspondance_entreprise = re.search(r"/companies/([^/]+)/", url)
            if correspondance_entreprise:
                # Convertit le slug "acme-corp" en "Acme Corp" (tirets → espaces, première lettre en majuscule)
                entreprise = correspondance_entreprise.group(1).replace("-", " ").title()
            else:
                # Fallback : cherche un élément HTML dont le data-testid ou la classe contient "company"
                try:
                    entreprise = driver.find_element(
                        By.CSS_SELECTOR, "[data-testid*='company'], [class*='company']"
                    ).text.strip()
                except NoSuchElementException:
                    entreprise = ""  # Aucune source ne permet de trouver l'entreprise

            # Si le titre ou l'entreprise sont manquants, cette offre est inexploitable : on l'abandonne
            if not titre or not entreprise:
                return None


            # --- Extraction de la ville ---
            # On essaie d'abord depuis la page HTML (plus précis), sinon depuis l'URL en fallback
            ville = extraire_ville_depuis_page(driver) or extraire_ville_depuis_url(url)


            # --- Extraction de la description ---
            # Délégué à la fonction dédiée qui gère les deux stratégies d'extraction
            description = extraire_description(driver)


            # Retourne le dictionnaire de l'offre avec toutes les données collectées
            return {
                "titre":       titre,
                "entreprise":  entreprise,
                "lieu":        ville,
                "description": description,
                "url":         url,
            }

        except TimeoutException:
            # La page a mis trop de temps à répondre
            print(f"    Timeout sur {url} (tentative {tentative}/{MAX_RETRIES})")
            if tentative == MAX_RETRIES:
                return None           # Toutes les tentatives épuisées : on abandonne cette offre
            time.sleep(SCROLL_PAUSE)  # Courte pause avant de réessayer

        except Exception as erreur:
            # Toute autre erreur inattendue : on abandonne cette offre sans relancer
            print(f"    Erreur sur {url} : {erreur}")
            return None

    return None  # Sécurité : ne devrait pas être atteint grâce aux return dans la boucle


# ---------------------------------------------------------------------------
# FONCTION PRINCIPALE : scrape_offres
# Rôle : orchestrer toutes les étapes du scraping et retourner le dictionnaire final
# C'est la seule fonction à appeler depuis l'extérieur (ex : bot.py)
# ---------------------------------------------------------------------------

def scrape_offres(mots_cles: str, localisation: str) -> dict:
    """
    Fonction principale du scraper WTTJ.

    Déroulement :
      1. Validation des paramètres d'entrée
      2. Construction de l'URL de recherche WTTJ
      3. Lancement du navigateur Chrome
      4. Collecte des liens d'offres (scroll infini)
      5. Scraping individuel de chaque offre
      6. Fermeture du navigateur (même en cas d'erreur)
      7. Retour du dictionnaire de résultats

    En cas d'erreur à n'importe quelle étape, retourne un dictionnaire
    avec une clé "erreur" au lieu de faire planter le programme.
    """
    # Vérifie que des mots-clés ont bien été fournis (paramètre obligatoire pour la recherche)
    if not mots_cles:
        return {"erreur": "Les mots-clés sont obligatoires."}

    # --- Construction de l'URL de recherche ---
    # Filtre obligatoire sur la France (country_code=FR) + encodage des mots-clés pour l'URL
    params_url = f"refinementList%5Boffices.country_code%5D%5B%5D=FR&query={quote(mots_cles)}"

    # Si une localisation est précisée, on l'ajoute comme filtre géographique dans l'URL
    if localisation:
        params_url += f"&aroundQuery={quote(localisation)}"

    # Assemble l'URL complète qui sera ouverte dans Chrome
    url_recherche = f"{BASE_URL}?{params_url}"

    driver            = None  # Initialisé à None pour que le bloc finally puisse vérifier son état
    offres_collectees = []    # Accumulera les dictionnaires d'offres valides au fil du scraping

    try:
        # --- Lancement du navigateur ---
        print(f"Lancement du scraper WTTJ pour '{mots_cles}' à '{localisation}'...")
        driver = configurer_driver()  # Crée et configure Chrome avec les options anti-détection
        driver.get(url_recherche)     # Ouvre la page de recherche WTTJ dans Chrome

        # Attend que les premiers liens d'offres soient visibles dans la page
        # Sans cette attente, on risque de collecter 0 lien si le JS n'a pas encore rendu les résultats
        WebDriverWait(driver, PAGE_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/jobs/']"))
        )

        # Pause supplémentaire pour s'assurer que tous les éléments JS sont bien rendus
        time.sleep(3)


        # --- Collecte des liens ---
        # Fait défiler la page jusqu'à avoir MAX_OFFRES liens uniques d'offres
        liens = collecter_liens_offres(driver, max_offres=MAX_OFFRES)
        print(f"  {len(liens)} liens d'offres collectés.")


        # --- Scraping offre par offre ---
        for i, url in enumerate(liens, start=1):
            print(f"  Scraping offre {i}/{len(liens)} : {url}")
            offre = scraper_offre(driver, url)  # Tente d'extraire les données de cette offre

            if offre:  # scraper_offre retourne None si l'offre est invalide ou a échoué
                offres_collectees.append(offre)

        print(f"Scraping terminé : {len(offres_collectees)} offres récupérées.")


        # --- Retour du dictionnaire structuré ---
        return {
            "source":        "Welcome to the Jungle",  # Identifie la source des données
            "mots_cles":     mots_cles,                # Mots-clés utilisés pour la recherche
            "localisation":  localisation,             # Ville ou région ciblée
            "nombre_offres": len(offres_collectees),   # Nombre d'offres valides collectées
            "offres":        offres_collectees,        # Liste des dictionnaires d'offres
        }

    except TimeoutException:
        # La page de résultats n'a pas chargé dans le délai imparti (PAGE_LOAD_WAIT secondes)
        return {"erreur": "La page de recherche WTTJ n'a pas chargé à temps. Réessayez."}

    except Exception as erreur:
        # Toute autre erreur non anticipée : on la remonte proprement sans crasher le programme
        print(f"Erreur critique dans scrape_offres : {erreur}")
        return {"erreur": f"Erreur inattendue : {str(erreur)}"}

    finally:
        # Ce bloc s'exécute TOUJOURS, même si une exception a été levée plus haut
        # Il garantit que Chrome est bien fermé pour libérer la mémoire et les processus système
        if driver is not None:
            driver.quit()


# ---------------------------------------------------------------------------
# Point d'entrée en ligne de commande
# Ce bloc ne s'exécute que si on lance ce fichier directement : python scraper_wttj.py
# Il ne s'exécute PAS si le fichier est importé depuis un autre module (ex : bot.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import pprint  # pprint affiche les dictionnaires imbriqués de façon lisible dans le terminal

    # Demande les paramètres de recherche à l'utilisateur dans le terminal
    mots_cles    = input("Entrez les mots-clés du poste recherché : ")
    localisation = input("Entrez la ville (laisser vide pour toute la France) : ")

    # Lance le scraping et stocke tous les résultats dans un dictionnaire
    resultats = scrape_offres(mots_cles, localisation)

    # Affichage conditionnel selon le contenu du dictionnaire retourné
    if "erreur" in resultats:
        # Le scraping a échoué : affiche le message d'erreur
        print(f"\nErreur : {resultats['erreur']}")
    else:
        # Le scraping a réussi : affiche un résumé lisible offre par offre
        print(f"\nRésultats pour '{resultats['mots_cles']}' "
              f"à '{resultats['localisation']}' "
              f"({resultats['nombre_offres']} offres) :\n")

        for i, offre in enumerate(resultats["offres"], start=1):
            print(f"Offre {i}/{resultats['nombre_offres']} :")
            print(f"  Titre      : {offre['titre']}")
            print(f"  Entreprise : {offre['entreprise']}")
            print(f"  Lieu       : {offre['lieu']}")
            print(f"  URL        : {offre['url']}")
            # Affiche uniquement les 200 premiers caractères pour ne pas surcharger le terminal
            print(f"  Description: {offre['description'][:200]}...")
            print("\n" + "-" * 60 + "\n")

    # Affiche la structure complète du dictionnaire retourné (utile pour déboguer ou intégrer)
    pprint.pprint(resultats)
