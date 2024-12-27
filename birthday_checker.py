import discord
import json
import asyncio
from datetime import datetime, timezone

# Charger la configuration
with open('config.json', 'r') as f:
    config = json.load(f)

TOKEN = config['token']
GENERAL_CHANNEL = int(config['general_channel'])  # ID du canal général (entier)

# Définir les intentions
intents = discord.Intents.default()
intents.message_content = True


async def birthday_check(bot_token, general_channel):
    # Initialiser le bot
    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        try:
            # Obtenir la date actuelle
            now = datetime.now(timezone.utc)
            current_day = now.day
            current_month = now.month

            # Charger les données des anniversaires
            with open('birthday.json', 'r') as file:
                birthday_data = json.load(file)

            # Parcourir chaque utilisateur et vérifier si c'est son anniversaire aujourd'hui
            for user_name, details in birthday_data.items():
                birthday = datetime.strptime(details["birthday"], "%d/%m/%Y")
                if birthday.day == current_day and birthday.month == current_month:
                    print(f"{user_name} fête son anniversaire aujourd'hui!")

                    user_id = int(details["user_id"])
                    message = details["message"]

                    # Obtenir le canal général
                    channel = bot.get_channel(general_channel)
                    if channel:
                        # Créer un embed pour souhaiter un joyeux anniversaire
                        embed = discord.Embed(
                            title=f"Ouais ouais ouais {message} **{user_name}** !",
                            description=f"🎉🎂 @everyone, on souhaite un joyeux anniversaire à <@{user_id}> ! 🎂🎉",
                            color=discord.Color.yellow(),
                        )

                        # Ajouter une image au message
                        file = discord.File("birthdaygif.gif", filename="birthdaygif.gif")
                        embed.set_image(url="attachment://birthdaygif.gif")

                        # Envoyer le message avec l'embed et l'image
                        await channel.send(embed=embed, file=file)
                    else:
                        print("Canal non trouvé")
        except Exception as e:
            print(f"Erreur lors de la vérification des anniversaires ou de l'envoi des messages : {e}")
        finally:
            await bot.close()  # Fermer le bot après l'exécution

    await bot.start(bot_token)

# Exécuter la fonction principale
asyncio.run(birthday_check(TOKEN, GENERAL_CHANNEL))