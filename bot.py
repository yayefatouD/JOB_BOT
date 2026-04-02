"""
bot.py - Groupe 1 : Point d'entrée principal du bot Discord
"""

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import unicodedata
import pandas as pd
from pathlib import Path

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

engine = None
generator = None

# Dossier data/ à la racine du projet (attendu par le groupe 5)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OFFERS_CSV = DATA_DIR / "offers.csv"


def slugify(text):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower().strip()
    return "".join([c for c in text if c.isalnum() or c == ' ']).replace(' ', '_')


def save_offers_to_csv(offers: list):
    """Sauvegarde les offres dans data/offers.csv pour le groupe 5."""
    df = pd.DataFrame(offers)
    df.to_csv(OFFERS_CSV, index=False, encoding="utf-8-sig")


@bot.event
async def on_ready():
    global engine, generator
    print(f"Bot connecte en tant que {bot.user}")
    try:
        from llm_handler.embeddings import EmbeddingEngine
        from llm_handler.generator import LetterGenerator
        engine = EmbeddingEngine()
        generator = LetterGenerator()
        print("Moteur LLM initialise avec succes.")
    except Exception as e:
        print(f"Erreur initialisation LLM : {e}")


@bot.command(name="search_job")
async def search_job(ctx, *, args: str = ""):
    """
    Usage : !search_job --type Data Science --loc Strasbourg
    (avec le CV en PDF en piece jointe)
    """
    await ctx.send("Recherche en cours... Veuillez patienter.")

    # Parsing des arguments
    job_type, location = "", ""
    if "--type" in args:
        job_type = args.split("--type")[1].split("--")[0].strip()
    if "--loc" in args:
        location = args.split("--loc")[1].split("--")[0].strip()

    # Etape 1 : Extraction du CV (Groupe 4)
    cv_text = ""
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if attachment.filename.endswith(".pdf"):
                await ctx.send("CV detecte, extraction en cours...")
                pdf_bytes = await attachment.read()
                try:
                    from cv_parser.pdf_parser import extract_text_from_pdf
                    cv_text = extract_text_from_pdf(pdf_bytes)
                    await ctx.send("CV extrait avec succes.")
                except Exception as e:
                    await ctx.send(f"Erreur extraction CV : {e}")
    else:
        await ctx.send("Aucun CV PDF joint. Envoyez votre CV en piece jointe.")
        return

    # Etape 2 : Scraping des offres (Groupes 2 & 3)
    await ctx.send(f"Recherche d'offres : {job_type} a {location}...")
    all_offers = []
    for scraper_path, label in [
        ("scraper.scraper_site1", "Scraper LinkedIn (Groupe 2)"),
        ("scraper.scraper_site2", "Scraper WTTJ (Groupe 3)"),
    ]:
        try:
            import importlib
            mod = importlib.import_module(scraper_path)
            offers = mod.scrape_offers(job_type=job_type, location=location)
            all_offers.extend(offers)
        except Exception as e:
            await ctx.send(f"{label} indisponible : {e}")

    if not all_offers:
        await ctx.send("Aucune offre trouvee.")
        return

    await ctx.send(f"{len(all_offers)} offre(s) trouvee(s).")

    # Sauvegarde dans data/offers.csv pour le groupe 5
    try:
        save_offers_to_csv(all_offers)
    except Exception as e:
        await ctx.send(f"Erreur sauvegarde CSV : {e}")

    # Etape 3 : Analyse LLM + lettres de motivation (Groupe 5)
    if engine is None or generator is None:
        await ctx.send("Erreur : le moteur LLM n'est pas disponible.")
        return

    try:
        await ctx.send("Analyse de la pertinence des offres en cours...")
        df_jobs = pd.read_csv(OFFERS_CSV)
        descriptions = df_jobs["description"].fillna("").tolist()
        cv_emb = engine.encode(cv_text)
        job_embs = engine.encode(descriptions)
        results = engine.find_similar(cv_emb, job_embs, top_k=min(3, len(all_offers)))
    except Exception as e:
        await ctx.send(f"Erreur lors de l'analyse : {e}")
        return

    for rank, result in enumerate(results):
        idx = result["index"]
        score = result["score"]
        offer = all_offers[idx]

        embed = discord.Embed(
            title=f"Offre {rank+1} : {offer.get('title', 'N/A')}",
            description=offer.get("company", "N/A"),
            color=discord.Color.green()
        )
        embed.add_field(name="Localisation", value=offer.get("location", "N/A"), inline=True)
        embed.add_field(name="Score de pertinence", value=f"{score:.0%}", inline=True)
        if offer.get("url"):
            embed.add_field(name="Lien", value=offer.get("url"), inline=False)
        await ctx.send(embed=embed)

        try:
            await ctx.send(f"Generation de la lettre de motivation pour l'offre {rank+1}...")
            lettre_latex = generator.generate(cv_text, offer.get("description", ""))

            if "ERREUR_CRITIQUE" in lettre_latex:
                await ctx.send(f"Erreur generation lettre : {lettre_latex}")
                continue

            safe_title = slugify(offer.get("title", f"offre_{rank+1}"))
            filename = f"lettre_{safe_title}"
            tex_path = generator.save_latex(lettre_latex, filename)

            if tex_path:
                await ctx.send(
                    f"Lettre de motivation generee pour l'offre {rank+1} :",
                    file=discord.File(tex_path)
                )
                os.remove(tex_path)
        except Exception as e:
            await ctx.send(f"Erreur LLM offre {rank+1} : {e}")


@bot.command(name="ping")
async def ping(ctx):
    latence = round(bot.latency * 1000)
    await ctx.send(f"Pong ! Latence : {latence}ms")


@bot.command(name="aide")
async def aide(ctx):
    embed = discord.Embed(
        title="Bot Emploi - Aide",
        description="Recherchez des offres d'emploi et generez des lettres de motivation.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="!search_job",
        value="Recherche des offres et genere une lettre de motivation.\n"
              "**Usage :** `!search_job --type [metier] --loc [ville]`\n"
              "**Exemple :** `!search_job --type Data Science --loc Strasbourg`\n"
              "Joindre le CV en PDF en piece jointe.",
        inline=False
    )
    embed.add_field(
        name="!ping",
        value="Verifie que le bot est en ligne et affiche la latence.",
        inline=False
    )
    embed.add_field(
        name="!aide",
        value="Affiche ce message.",
        inline=False
    )
    embed.set_footer(text="Pensez a joindre votre CV en PDF lors de la commande !search_job")
    await ctx.send(embed=embed)


if __name__ == "__main__":
    if not TOKEN:
        print("ERREUR : le token Discord est manquant.")
        print("Verifie que le fichier .env contient bien DISCORD_TOKEN=ton_token")
        exit(1)
    bot.run(TOKEN)
