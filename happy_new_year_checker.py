import discord
import json
import asyncio
from datetime import datetime

# Charger la configuration
with open('config.json', 'r') as f:
    config = json.load(f)

TOKEN = config['token']
GENERAL_CHANNEL = int(config['general_channel'])  # ID du canal privé (entier)

# Définir les intentions
intents = discord.Intents.default()
intents.message_content = True

async def send_new_year_message(bot_token, general_channel):
    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        try:
            # Récupérer le canal
            channel = bot.get_channel(general_channel)
            if channel:
                # Préparer le message
                current_year = datetime.now().year
                next_year = current_year + 1

                embed = discord.Embed(
                    title=f"Bonne année **{next_year}** ! 🎉🎆",
                    description="Que cette année soit pleine de joie, de bonheur et de réussite pour vous tous ! (une année de plus à vous supporter...) 🎇🎊",
                    color=discord.Color.dark_gold()
                )
                file = discord.File("fireworks.gif", filename="fireworks.gif")
                embed.set_image(url="attachment://fireworks.gif")

                # Envoyer le message
                await channel.send(embed=embed, file=file)
                print("Message envoyé avec succès !")
            else:
                print("Channel non trouvé")
        except Exception as e:
            print(f"Erreur : {e}")
        finally:
            await bot.close()

    await bot.start(bot_token)

# Exécuter la fonction principale
asyncio.run(send_new_year_message(TOKEN, GENERAL_CHANNEL))