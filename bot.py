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
with open('config.json', 'r', encoding="utf-8") as f:
    config = json.load(f)

steam_url = config['steam_url']
token = config['token']
private_server = int(config['private_server'])  # Assurez-vous que l'ID est un entier
api_tenor_key = config['api_tenor_key']
general_channel = int(config['general_channel'])  # Assurez-vous que l'ID est un entier
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

@bot.command()
async def jumpscare(ctx):
    embed = discord.Embed(
        title="J'ai peur !",
        description="J'suis cardiaque enculé !",
        color=discord.Color.dark_magenta()
    )
    file = discord.File("jumpscared.gif", filename="jumpscared.gif")
    embed.set_image(url="attachment://jumpscared.gif")
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
            embed = discord.Embed(
                title="Tu as été gnomé(e) !",
                description="Sinon baldur when ?",
                color=discord.Color.dark_teal()
            )
            file = discord.File("gnome.gif", filename="gnome.gif")
            embed.set_image(url="attachment://gnome.gif")
            await ctx.send(embed=embed, file=file)
                    
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
        name="!gnome 🎶", 
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