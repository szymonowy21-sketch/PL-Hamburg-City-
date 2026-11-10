import discord
from discord import app_commands
from discord.ext import commands
import requests
import os
from flask import Flask
from threading import Thread

# Serwer podtrzymujący bota na Renderze
app = Flask('')

@app.route('/')
def home():
    return "Bot banów Hamburg RP działa 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Pobieranie tokenu z bezpiecznych ustawień serwera Render
TOKEN = os.environ.get("DISCORD_TOKEN")

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Automatyczna rejestracja komend ukośnika w pamięci Discorda
        await self.tree.sync()
        print("Zsynchronizowano komendę ukośnika /ban.")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Bot banów zalogowany jako {bot.user.name}")

# Formularz okienka modalnego
class BanModal(discord.ui.Modal, title='Formularz Blokady Gier (BAN)'):
    kto_wystawil = discord.ui.TextInput(label='👮 Kto wystawił bana:', placeholder='Twój nick i ranga', required=True)
    zbanowany_roblox = discord.ui.TextInput(label='👤 Zbanowany gracz (Nick z Roblox):', placeholder='np. Builderman', required=True)
    na_ile = discord.ui.TextInput(label='⏳ Na ile (Czas):', placeholder='np. 7 dni, Permanentnie', required=True)
    powod = discord.ui.TextInput(label='📝 Powód bana:', style=discord.TextStyle.paragraph, placeholder='Wpisz powód...', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        username = self.zbanowany_roblox.value.replace("@", "").strip()
        rbx_id, rbx_avatar = None, None
        
        try:
            res = requests.post("https://roblox.com", json={"usernames": [username], "excludeBannedUsers": False}, timeout=3)
            if res.status_code == 200 and res.json()['data']:
                rbx_id = res.json()['data']['id']
                thumb_res = requests.get(f"https://roblox.com{rbx_id}&size=352x352&format=Png&isCircular=false", timeout=3)
                if thumb_res.status_code == 200 and thumb_res.json()['data']:
                    rbx_avatar = thumb_res.json()['data']['imageUrl']
        except Exception as e:
            print(f"Roblox API lag: {e}")
        
        embed = discord.Embed(title="🔨 NOWA BLOKADA (BAN)", color=discord.Color.red())
        embed.add_field(name="👮 Administrator", value=self.kto_wystawil.value, inline=True)
        
        if rbx_id:
            embed.add_field(name="👤 Ukarany gracz", value=f"@{username}\nID: {rbx_id}", inline=True)
            if rbx_avatar:
                embed.set_thumbnail(url=rbx_avatar)
        else:
            embed.add_field(name="👤 Ukarany gracz", value=f"@{username}\n*(Brak zdjęcia postaci)*", inline=True)
            
        embed.add_field(name="⏳ Czas kary", value=self.na_ile.value, inline=False)
        embed.add_field(name="📝 Powód", value=self.powod.value, inline=False)
        embed.set_footer(text="ℹ️ Jeśli chcesz się odwołać, napisz w tickecie odwołanie do bana lub wbij na poczekalnię.")
        
        await interaction.channel.send(embed=embed)

# OFICJALNA KOMENDA UKOŚNIKA /BAN
@bot.tree.command(name="ban", description="[ADMIN] Otwiera formularz banowania")
async def ban_command(interaction: discord.Interaction):
    WYMAGANA_ROLA_ID = 1553090239831220324
    WYMAGANY_KANAL_ID = 1566188945476292716

    # Sprawdzanie czy użytkownik ma wymaganą rolę
    ma_role = any(role.id == WYMAGANA_ROLA_ID for role in interaction.user.roles)
    if not ma_role:
        await interaction.response.send_message("❌ Nie posiadasz wymaganej rangi moderacyjnej, aby użyć tej komendy!", ephemeral=True)
        return

    # Sprawdzanie czy komenda jest wpisana na dobrym kanale
    if interaction.channel_id != WYMAGANY_KANAL_ID:
        await interaction.response.send_message(f"❌ Tę komendę możesz wykonać tylko na kanale <#{WYMAGANY_KANAL_ID}>!", ephemeral=True)
        return

    # Bezpośrednie otwarcie formularza na ekranie
    await interaction.response.send_modal(BanModal())

keep_alive()
bot.run(TOKEN)
