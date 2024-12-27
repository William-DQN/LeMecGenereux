import discord
import json
import asyncio

# Charger la configuration
with open('config.json', 'r') as f:
    config = json.load(f)

TOKEN = config['token']
PRIVATE_SERVER = int(config['private_server'])  # ID du canal privé (entier)

# Définir les intentions
intents = discord.Intents.default()
intents.message_content = True

async def send_weekly_message(bot_token, private_server):
    try:
        # Initialiser le bot
        bot = discord.Client(intents=intents)

        @bot.event
        async def on_ready():
            try:
                print(f"Connecté en tant que {bot.user}")
                # Récupérer le canal
                channel = bot.get_channel(private_server)
                if channel:
                    await channel.send("@everyone , Bonjour Epic.\nAurevoir Epic.")
                    print(f"Message envoyé au canal ID : {private_server}")
                else:
                    print("Channel non trouvé")
            except Exception as e:
                print(f"Erreur lors de l'envoi du message : {e}")
            finally:
                # Déconnecter le bot après l'envoi
                await bot.close()

        # Démarrer le bot
        await bot.start(bot_token)

    except Exception as e:
        print(f"Erreur : {e}")

# Lancer la fonction
asyncio.run(send_weekly_message(TOKEN, PRIVATE_SERVER))