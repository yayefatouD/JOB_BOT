"""
bot.py - Groupe 1 : Point d'entrée principal du bot Discord
"""

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")


@bot.command(name="search_job")
async def search_job(ctx, *, args: str = ""):
    """
    Usage : !search_job --type Data Science --loc Strasbourg
    (avec le CV en PDF en pièce jointe)
    """
    await ctx.send("Recherche en cours... Veuillez patienter.")

    # Parsing des arguments
    job_type, location = "", ""
    if "--type" in args:
        job_type = args.split("--type")[1].split("--")[0].strip()
    if "--loc" in args:
        location = args.split("--loc")[1].split("--")[0].strip()

    # Étape 1 : Extraction du CV (Groupe 4)
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

    # Étape 2 : Scraping des offres (Groupes 2 & 3)
    await ctx.send(f"Recherche d'offres : {job_type} a {location}...")
    all_offers = []
    for scraper_path, label in [
        ("scraper.scraper_site1", "Scraper 1"),
        ("scraper.scraper_site2", "Scraper 2"),
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

    # Étape 3 : Analyse LLM + lettres de motivation (Groupe 5)
    for i, offer in enumerate(all_offers[:3]):
        await ctx.send(f"\nOffre {i+1} : {offer.get('title', 'N/A')} - {offer.get('company', 'N/A')}")
        try:
            from llm.llm_handler import analyze_offer, generate_cover_letter
            score = analyze_offer(cv_text=cv_text, offer=offer)
            await ctx.send(f"Pertinence : {score}")
            letter = generate_cover_letter(cv_text=cv_text, offer=offer)
            for j in range(0, len(letter), 1900):
                await ctx.send(f"```{letter[j:j+1900]}```")
        except Exception as e:
            await ctx.send(f"Erreur LLM offre {i+1} : {e}")

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
        name="!aide",
        value="Affiche ce message.",
        inline=False
    )
    embed.add_field(
        name="!ping",
        value="Verifie que le bot est en ligne et affiche la latence.",
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
