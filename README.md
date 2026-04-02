# Job BOT Discord

Bot Discord pour faciliter la recherche d'emploi et d'alternance.

## Fonctionnalites
- Scraping automatique d'offres d'emploi
- Extraction et analyse de CV (PDF)
- Evaluation de la pertinence des offres
- Generation de lettres de motivation personnalisees

## Structure du projet

```
bot-emploi-discord/
├── bot.py                        ← Groupe 1
├── requirements.txt
├── .env                          ← NE PAS COMMITER
├── env.example
├── scraping/
│   ├── scraper_site1.py          ← Groupe 2
│   └── scraper_site2.py          ← Groupe 3
├── cv_parser/
│   └── pdf_parser.py             ← Groupe 4
└── llm/
    └── llm_handler.py            ← Groupe 5
```

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/VOTRE_COMPTE/bot-emploi-discord.git
cd bot-emploi-discord

# 2. Créer et activer l'environnement virtuel
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# 3. Installer les packages
pip install -r requirements.txt

# 4. Configurer le token Discord
# Renommer env.example en .env et remplir DISCORD_TOKEN
```

## Lancer le bot

```bash
python bot.py
```

## Utilisation

Dans Discord :
```
!search_job --type "Data Science" --loc Strasbourg
```
(avec votre CV en PDF en pièce jointe)

## Regles GitHub
- Ne jamais commiter `.env`
- Ne jamais commiter `venv/`
- Toujours faire `git pull` avant de commencer a coder
- Mettre a jour `requirements.txt` quand vous ajoutez un package
