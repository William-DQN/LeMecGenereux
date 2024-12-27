import discord
import json
import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime

# Charger la configuration
with open('config.json', 'r', encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config['token']
PRIVATE_SERVER_CHANNEL = int(config['private_server'])  # ID du canal privé
STEAM_URL = config['steam_url']

# Définir les intentions
intents = discord.Intents.default()
intents.message_content = True
# Chemin du fichier de suivi des messages envoyés
sent_messages_file = 'sent_messages.txt'
def read_sent_messages():
    if not os.path.exists(sent_messages_file):
        return set()
    with open(sent_messages_file, 'r') as file:
        return set(line.strip() for line in file)

def write_sent_message(message_id):
    with open(sent_messages_file, 'a') as file:
        file.write(f'{message_id}\n')


async def steam_free_games_check(bot_token, channel_id, steam_url):
    # Initialiser le bot
    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        try:
            print(f"Bot connecté en tant que {bot.user}")
            channel = bot.get_channel(channel_id)

            if not channel:
                print("Canal non trouvé.")
                await bot.close()
                return

            # Récupérer les jeux gratuits sur Steam
            response = requests.get(steam_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            game_elements = soup.select('.search_result_row')

            free_game_info = []

            for game in game_elements:
                discount_pct_element = game.select_one('.discount_pct')
                discount_final_price_element = game.select_one('.discount_final_price')
                url_element = game.get('href') or game.select_one('a')['href']

                if discount_final_price_element:
                    final_price = discount_final_price_element.text.strip()
                    if final_price == '0,00€' and discount_pct_element and discount_pct_element.text.strip() == '-100%':
                        if url_element and url_element.startswith('https://store.steampowered.com/app/'):
                            # Ajouter le jeu à la liste des jeux gratuits
                            game_info = {'url': url_element, 'end_date': 'Inconnue'}

                            # Obtenir la date de fin de l'offre
                            game_page_response = requests.get(url_element)
                            game_page_soup = BeautifulSoup(game_page_response.text, 'html.parser')
                            date_element = game_page_soup.find('div', class_='game_area_purchase_game_wrapper')

                            if date_element:
                                offer_end_text = date_element.get_text(strip=True)
                                try:
                                    end_date = datetime.strptime(offer_end_text, "%B %d, %Y").strftime("%d %B %Y")
                                    game_info['end_date'] = end_date
                                except ValueError:
                                    print('Impossible de parser la date de fin.')

                            free_game_info.append(game_info)

            # Préparer le message à envoyer
            if free_game_info:
                message_content = f"@everyone, voici {len(free_game_info)} jeu(x)/dlc(s) gratuit(s) sur Steam !\n"
                for game in free_game_info:
                    message_content += f"- {game['url']} (Offre valable jusqu'au : {game['end_date']})\n"

                await channel.send(message_content)
                print("Message envoyé avec succès.")
            else:
                print("Aucun jeu gratuit trouvé.")

        except requests.RequestException as e:
            print(f"Erreur lors de la récupération des données Steam : {e}")
        except Exception as e:
            print(f"Erreur inattendue : {e}")
        finally:
            await bot.close()

    await bot.start(bot_token)


# Exécuter la fonction principale
asyncio.run(steam_free_games_check(TOKEN, PRIVATE_SERVER_CHANNEL, STEAM_URL))
