import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
import os
import asyncio
from datetime import datetime, timedelta
import random

# Chargement de la configuration
with open('config.json', 'r') as f:
    config = json.load(f)

steam_url = config['steam_url']
token = config['token']
private_server = int(config['private_server'])  # Assurez-vous que l'ID est un entier

# Définir les intentions
intents = discord.Intents.default()
intents.message_content = True

# Créer le bot
bot = commands.Bot(command_prefix='!', intents=intents)

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

@bot.event
async def on_ready():
    print(f'{bot.user} est là !')
    await check_free_games()  # Appel unique pour le démarrage
    schedule_check.start()
    send_weekly_message.start()

@tasks.loop(hours=96)
async def schedule_check():
    await check_free_games()  # Appels programmés

@tasks.loop(hours=24)
async def send_weekly_message():
    now = datetime.utcnow()
    next_thursday = now + timedelta((3 - now.weekday()) % 7)  # Trouver le prochain jeudi
    next_thursday = next_thursday.replace(hour=18, minute=0, second=0, microsecond=0)
    delay = (next_thursday - now).total_seconds()
    
    await asyncio.sleep(delay)
    
    channel = bot.get_channel(private_server)
    if channel:
        await channel.send('Bonjour Epic.\n Aurevoir Epic.')
    else:
        print('Channel not found')

    # Redémarrer le timer pour le jeudi suivant
    await send_weekly_message.change_interval(weeks=1)

async def check_free_games():
    try:
        response = requests.get(steam_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        game_elements = soup.select('.search_result_row')
        print(f'Found {len(game_elements)} game elements')

        free_game_urls = set()  # Utiliser un set pour éviter les duplications

        for game in game_elements:
            print(game.prettify())  # Afficher le contenu HTML de chaque élément de jeu pour le débogage

            discount_pct_element = game.select_one('.discount_pct')
            discount_final_price_element = game.select_one('.discount_final_price')
            url_element = game.get('href') or game.select_one('a')['href']

            print(f'Discount element: {discount_pct_element}')  # Débogage : afficher l'élément de réduction
            print(f'Final price element: {discount_final_price_element}')  # Débogage : afficher l'élément de prix
            print(f'URL element: {url_element}')  # Débogage : afficher l'URL trouvée

            if discount_final_price_element:
                final_price = discount_final_price_element.text.strip()
                print(f'Final price: {final_price}')

                if final_price == '0,00€':
                    if discount_pct_element:
                        discount_pct = discount_pct_element.text.strip()
                        print(f'Discount percentage: {discount_pct}')
                        if discount_pct == '-100%':
                            if url_element and url_element.startswith('https://store.steampowered.com/app/'):
                                free_game_urls.add(url_element)  # Ajouter l'URL au set
                                print(f'Found free game URL: {url_element}')
                            else:
                                print('URL element not found for a free game or does not match the expected pattern')
                    else:
                        # Cas où l'élément de réduction n'est pas trouvé mais le prix final est correct
                        if url_element and url_element.startswith('https://store.steampowered.com/app/'):
                            free_game_urls.add(url_element)  # Ajouter l'URL au set
                            print(f'Found free game URL (without discount pct): {url_element}')
                else:
                    print('Final price is not 0,00€')
            else:
                print('Final price element not found for a game')

        # Envoyer un message avec le nombre de jeux gratuits trouvés
        if free_game_urls:
            num_games = len(free_game_urls)  # Obtenir le nombre de jeux gratuits trouvés
            print(f'Attempting to send message to channel {private_server}...')
            channel = bot.get_channel(private_server)
            if channel:
                # Créer un bloc de message avec les URLs
                message_content = f'@everyone, j\'ai trouvé {num_games} jeu(x) gratuit(s) !\n' + '\n'.join(free_game_urls)

                # Lire les identifiants des messages envoyés précédemment
                sent_messages = read_sent_messages()
                
                # Créer une version unique de l'identifiant du message
                unique_message_id = hash(message_content)  # Crée un hash unique basé sur le contenu du message
                
                # Vérifier si le message est déjà envoyé
                if str(unique_message_id) in sent_messages:
                    print('Message content already sent. Skipping send.')
                    return

                # Envoyer le message
                sent_message = await channel.send(message_content)
                
                # Écrire l'identifiant du message dans le fichier de suivi
                write_sent_message(unique_message_id)
                print('Message sent to channel')
            else:
                print('Channel not found')
        else:
            print('No free game URLs found')

    except requests.RequestException as e:
        print(f'Error fetching Steam page: {e}')
    except Exception as e:
        print(f'Error parsing Steam page: {e}')

@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        title="Pong!",
        description="Ayohoho!",
        color=discord.Color.green()
    )
    file = discord.File("goofy.jpg", filename="goofy.jpg")
    embed.set_image(url="attachment://goofy.jpg")
    await ctx.send(embed=embed, file=file)

@bot.command()
async def coin(ctx):
    result = random.choice(['Face', 'Pile'])
    
    # Define the file path based on the result
    if result == 'face': 
        file_path = "coin.gif"
        color = discord.Color.red()
    else:
        file_path = "coin.gif"
        color = discord.Color.blue()
    
    embed = discord.Embed(
        title="Pile ou Face",
        description=f"In **{result}** we trust!",
        color=color
    )
    # Attach the local image file
    file = discord.File(file_path, filename="coin.gif")
    embed.set_image(url="attachment://coin.gif")
    
    await ctx.send(embed=embed, file=file)

@bot.command()
async def merci(ctx):
    embed = discord.Embed(
        title="De rien!",
        description="Avec plaisir!",
        color=discord.Color.pink()
    )
    file = discord.File("mybeloved.gif", filename="mybeloved.gif")
    embed.set_image(url="attachment://mybeloved.gif")
    await ctx.send(embed=embed, file=file)

bot.run(token)