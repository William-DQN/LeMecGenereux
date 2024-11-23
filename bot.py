import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
import os
import asyncio
import pytz
from datetime import datetime, timezone, timedelta

import random
import string

# Chargement de la configuration
with open('config.json', 'r') as f:
    config = json.load(f)

steam_url = config['steam_url']
token = config['token']
private_server = int(config['private_server'])  # Assurez-vous que l'ID est un entier
api_tenor_key = config['api_tenor_key']
general_channel = int(config['general_channel'])  # Assurez-vous que l'ID est un entier
gnome_sticker = config['gnome_sticker']
# Définir les intentions
intents = discord.Intents.default()
intents.message_content = True

# Créer le bot
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
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
    # Appel unique pour le démarrage

    # Attention à décommenter les lignes suivantes pour activer les appels programmés
    await check_free_games()  
    schedule_check.start()
    send_weekly_message.start()
    birthday_check.start()
    bot.loop.create_task(happy_new_year())

@tasks.loop(hours=24)
async def birthday_check():
    try:
        # Obtenir la date et l'heure actuelles en UTC avec timezone-aware
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
                
                try:
                    # Obtenir l'utilisateur par son ID
                    user = await bot.fetch_user(user_id)

                    # Obtenir le canal général où envoyer le message
                    channel = bot.get_channel(general_channel)  # Remplacez general_channel par l'ID réel du canal
                    if channel:
                        # Créer un embed pour souhaiter joyeux anniversaire
                        embed = discord.Embed(
                            title=f"Ouais ouais ouais {message} **{user_name}** !",
                            description=f"🎉🎂 @everyone, on souhaite un joyeux anniversaire à {(user.mention)} ! 🎂🎉",
                            color=discord.Color.yellow()
                        )

                        # Ajouter une image au message
                        file = discord.File("birthdaygif.gif", filename="birthdaygif.gif")
                        embed.set_image(url="attachment://birthdaygif.gif")

                        # Envoyer le message avec l'embed et l'image
                        await channel.send(embed=embed, file=file)
                    else:
                        print("Canal non trouvé")
                except Exception as e:
                    print(f"Erreur lors de l'envoi du message d'anniversaire à {user_name}: {e}")
    except Exception as e:
        print(f"Erreur lors de la vérification des anniversaires: {e}")

@tasks.loop(hours=96)
async def schedule_check():
    await check_free_games()  # Appels programmés

@tasks.loop(hours=24)
async def send_weekly_message():
    now = datetime.now(pytz.timezone("Europe/Paris"))  # GMT+1 avec gestion des changements d'heure
    target_time = now.replace(hour=17, minute=30, second=0, microsecond=0)
    
    # Si aujourd'hui est jeudi et qu'il est avant 17h30, on envoie le message aujourd'hui
    if now.weekday() == 3 and now < target_time:  # 3 correspond à jeudi
        next_thursday = now
    else:
        # Trouver le prochain jeudi
        days_until_thursday = (3 - now.weekday()) % 7
        next_thursday = now + timedelta(days=days_until_thursday)
        next_thursday = next_thursday.replace(hour=17, minute=30, second=0, microsecond=0)

    delay = (next_thursday - now).total_seconds()

    # Attendre jusqu'à jeudi 17h30
    await asyncio.sleep(delay)

    # Envoyer le message à 17h30 le jeudi
    channel = bot.get_channel(private_server)  # Remplacez private_server par l'ID réel du canal
    if channel:
        await channel.send('Bonjour Epic.\nAurevoir Epic.')
    else:
        print('Channel not found')

    # Reprogrammer pour la semaine suivante (exactement dans 7 jours à 17h30)
    await asyncio.sleep(7 * 24 * 60 * 60)  # 7 jours en secondes

async def check_free_games():
    try:
        response = requests.get(steam_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        game_elements = soup.select('.search_result_row')
        print(f'Found {len(game_elements)} game elements')

        free_game_info = []  # Liste pour stocker les jeux gratuits et leurs dates de fin

        for game in game_elements:
            discount_pct_element = game.select_one('.discount_pct')
            discount_final_price_element = game.select_one('.discount_final_price')
            url_element = game.get('href') or game.select_one('a')['href']

            if discount_final_price_element:
                final_price = discount_final_price_element.text.strip()

                if final_price == '0,00€':
                    if discount_pct_element:
                        discount_pct = discount_pct_element.text.strip()
                        if discount_pct == '-100%':
                            if url_element and url_element.startswith('https://store.steampowered.com/app/'):
                                # Analyser la page du jeu pour obtenir la date limite
                                game_info = {'url': url_element, 'end_date': 'Inconnue'}  # Par défaut la date est 'Inconnue'
                                
                                # Récupérer la page du jeu pour obtenir la date de fin de l'offre
                                game_page_response = requests.get(url_element)
                                game_page_soup = BeautifulSoup(game_page_response.text, 'html.parser')
                                
                                # Rechercher l'élément contenant la date de fin de l'offre (la classe peut varier)
                                date_element = game_page_soup.find('div', class_='game_area_purchase_game_wrapper')
                                
                                if date_element:
                                    offer_end_text = date_element.get_text(strip=True)
                                    
                                    # Tenter de formater la date (en supposant un format spécifique de date)
                                    try:
                                        # Vous pouvez ajuster le format de la date en fonction de ce qui est trouvé
                                        end_date = datetime.strptime(offer_end_text, "%B %d, %Y").strftime("%d %B %Y")
                                        game_info['end_date'] = end_date  # Ajouter la date limite correcte
                                        print(f'Offer ends on: {end_date}')
                                    except ValueError:
                                        print('Unable to parse the offer end date.')
                                
                                free_game_info.append(game_info)  # Ajouter l'info complète du jeu à la liste
                                print(f'Found free game URL: {url_element}')
                            else:
                                print('URL element not found for a free game or does not match the expected pattern')

        # Envoyer un message avec le nombre de jeux gratuits trouvés
        if free_game_info:
            num_games = len(free_game_info)  # Obtenir le nombre de jeux gratuits trouvés
            print(f'Attempting to send message to channel {private_server}...')
            channel = bot.get_channel(private_server)
            if channel:
                # Créer un bloc de message avec les URLs et les dates limites
                message_content = f"@everyone, j'ai trouvé {num_games} jeu(x) gratuit(s) !\n"
                for game in free_game_info:
                    message_content += f"- {game['url']} (Offre valable jusqu'au : {game['end_date']})\n"

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
        
# Fonction pour envoyer le message de bonne année
async def happy_new_year():
    channel = bot.get_channel(private_server)  # Remplacez private_server par l'ID réel du canal
    
    # Avoir l'année en cours et l'année suivante
    check_current_year = datetime.now(pytz.timezone("Europe/Paris")).year
    next_year = check_current_year + 1
    
    # Date exacte du 1er janvier à minuit
    first_jan = datetime(next_year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone("Europe/Paris"))
    now = datetime.now(pytz.timezone("Europe/Paris"))
    
    # Calcul du temps restant jusqu'au nouvel an
    time_until_new_year = (first_jan - now).total_seconds()
    
    # Attendre jusqu'au 1er janvier à minuit
    await asyncio.sleep(time_until_new_year)

    # Envoyer le message une fois le nouvel an arrivé
    if channel:
        embed = discord.Embed(
            title=f"Bonne année **{next_year}** ! 🎉🎆",
            description="Que cette année soit pleine de joie, de bonheur et de réussite pour vous tous ! 🎇🎊",
            color=discord.Color.dark_gold()
        )
        file = discord.File("fireworks.gif", filename="fireworks.gif")
        embed.set_image(url="attachment://fireworks.gif")
        await channel.send(embed=embed, file=file)
    else:
        print('Channel not found')

    # Planifier à nouveau pour l'année suivante
    await happy_new_year()

@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        title="Pong !",
        description="Ayohoho !",
        color=discord.Color.green()
    )
    file = discord.File("goofy.jpg", filename="goofy.jpg")
    embed.set_image(url="attachment://goofy.jpg")
    await ctx.send(embed=embed, file=file)

@bot.command()
async def coin(ctx):
    result = random.choice(['Face', 'Pile'])
    
    # Define the file path based on the result
    if result == 'Face': 
        file_path = "coin.gif"
        color = discord.Color.red()
    elif result == 'Pile':
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
        title="De rien !",
        description="Tout pour mon pote à la compote !",
        color=discord.Color.pink()
    )
    file = discord.File("mybeloved.gif", filename="mybeloved.gif")
    embed.set_image(url="attachment://mybeloved.gif")
    await ctx.send(embed=embed, file=file)


# Définir la fonction pour générer une chaîne aléatoire
def random_string(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_letters, k=length))

@bot.command()
async def pauline(ctx):
    searching_url = f"https://tenor.googleapis.com/v2/search?q=Taz&key={api_tenor_key}&limit=50"
    response = requests.get(searching_url)
    
    # Vérification du statut HTTP
    if response.status_code != 200:
        await ctx.send(f"Erreur lors de la requête à l'API Tenor : {response.status_code}")
        return
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        await ctx.send("Erreur de décodage JSON de la réponse de l'API Tenor.")
        print("Réponse brute:", response.text)  # Impression de la réponse brute pour le diagnostic
        return
    
    if 'results' in data:
        gif_url = random.choice(data['results'])['media_formats']['gif']['url']
        embed = discord.Embed(
            title="D'accord Madame Taz.",
            description= random_string() + " à toi aussi **Pauline**.",
            color=discord.Color.dark_grey()
        )
        embed.set_image(url=gif_url)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Désolé, je n'ai pas pu trouver de GIF de Taz.")


@bot.command()
async def amimir(ctx):
    searching_url = f"https://tenor.googleapis.com/v2/search?q=amimir&key={api_tenor_key}&limit=150"
    response = requests.get(searching_url)
    
    # Vérification du statut HTTP
    if response.status_code != 200:
        await ctx.send(f"Erreur lors de la requête à l'API Tenor : {response.status_code}")
        return
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        await ctx.send("Erreur de décodage JSON de la réponse de l'API Tenor.")
        print("Réponse brute:", response.text)  # Impression de la réponse brute pour le diagnostic
        return
    
    if 'results' in data:
        gif_url = random.choice(data['results'])['media_formats']['gif']['url']
        embed = discord.Embed(
            title="A mimir les gars.",
            description= "Il est l'heure d'aller se coucher.",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=gif_url)
        await ctx.send(embed=embed)
    else:
        await ctx.send("No mimir ?")

@bot.command()
async def trololo(ctx):
    if ctx.author.voice:  # Vérifie si l'auteur est dans un canal vocal
        current_channel = ctx.author.voice.channel
        voice_client = await current_channel.connect()  # Utilisation correcte de current_channel
        noise = discord.FFmpegPCMAudio(r"soundboard/trololo.mp3")  # Chemin du fichier audio
        
        if not voice_client.is_playing():
            voice_client.play(noise)
            await ctx.send(f"Tu as été trollé !")
            
            while voice_client.is_playing():  # Attend la fin de la lecture
                await asyncio.sleep(1)
                
            await voice_client.disconnect()  # Déconnecte une fois la lecture terminée
    else:
        await ctx.send(f"N'essaie même pas de me troller {ctx.author.mention} !")  # Mentionne l'auteur si pas dans un canal vocal

@bot.command()
async def gnome(ctx):
    if ctx.author.voice:  # Vérifie si l'auteur est dans un canal vocal
        current_channel = ctx.author.voice.channel
        voice_client = await current_channel.connect()  # Utilisation correcte de current_channel
        noise = discord.FFmpegPCMAudio(r"soundboard/youve_been_gnomed.mp3")  # Chemin du fichier audio
        
        if not voice_client.is_playing():
            voice_client.play(noise)
            await ctx.send(f"Tu as été Gnomé ! \n {gnome_sticker}")
            
            while voice_client.is_playing():  # Attend la fin de la lecture
                await asyncio.sleep(1)
                
            await voice_client.disconnect()  # Déconnecte une fois la lecture terminée
    else:
        await ctx.send(f"N'essaie même pas de me gnomer {ctx.author.mention} ! (sinon Baldur when ?)")  # Mentionne l'auteur si pas dans un canal vocal

@bot.command()
async def help(ctx):

    # Envoyer l'image en tant que fichier joint
    file = discord.File("mecgenereux.jpg", filename="mecgenereux.jpg")

    # Créer l'embed
    embed = discord.Embed(
        title="**Commandes du Bot :**",
        description="Utilisez les commandes ci-dessous pour interagir avec le bot.",
        color=discord.Color.dark_gold(),
    )

    # Utiliser l'image comme miniature
    embed.set_thumbnail(url="attachment://mecgenereux.jpg")

    embed.add_field(
        name="!ping 🏓", 
        value="Vérifie si le bot est en ligne et répond avec 'Pong !'", 
        inline=False
    )
    embed.add_field(
        name="!coin 🪙", 
        value="Lance une pièce pour obtenir **Face** ou **Pile** (Fear and Hunger moment).",
        inline=False
    )
    embed.add_field(
        name="!merci 🙏", 
        value="Répond avec un GIF de remerciement. C'est toujours sympa de dire merci !", 
        inline=False
    )
    embed.add_field(
        name="!pauline 🌀", 
        value="Répond avec un GIF aléatoire de Taz pour saluer Pauline.", 
        inline=False
    )
    embed.add_field(
        name="!amimir 😴", 
        value="Répond avec un GIF aléatoire pour dire bonne nuit.", 
        inline=False
    )

    embed.add_field(
        name="!trololo 🎶", 
        value="Fait un son magique dans le channel du lanceur.", 
        inline=False
    )

    embed.add_field(
        name="!help 📜", 
        value="Affiche cette liste de commandes avec des descriptions détaillées.", 
        inline=False
    )

    # Envoyer le message avec l'embed et le fichier joint
    await ctx.send(embed=embed, file=file)

bot.run(token)
