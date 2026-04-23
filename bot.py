import discord
from discord import app_commands
from discord.ext import commands
from memory_flash import items
import importlib
import memory_flash
import os
import asyncio
import subprocess
import requests
from aiohttp import web

TOKEN = os.environ["TOKEN"]

GITHUB_REPO = "anonymous014-fourteen/FTMG_bot_struct"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
POLL_INTERVAL = 300  # check every 5 minutes

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# group items by category
categories = {}
for key, data in items.items():
    categories.setdefault(data["category"], []).append((key, data))

CATEGORY_COLORS = {
    "Bags":                discord.Color(0xf6b26b),
    "Materials":           discord.Color(0x4285f4),
    "Trash Caches":        discord.Color(0xcccccc),
    "Common Caches":       discord.Color(0xefefef),
    "High Quality Caches": discord.Color(0x00ff00),
    "Rare Caches":         discord.Color(0xfbbc04),
    "Legendary Caches":    discord.Color(0xff00ff),
    "Epic Caches":         discord.Color(0xff0000),
    "Heals":               discord.Color(0x00ffff),
}

def category_color(category):
    return CATEGORY_COLORS.get(category, discord.Color.greyple())

def reload_items():
    global items, categories
    importlib.reload(memory_flash)
    items = memory_flash.items
    categories = {}
    for key, data in items.items():
        categories.setdefault(data["category"], []).append((key, data))
    print("Reloaded memory_flash.py")

def get_latest_sha():
    try:
        resp = requests.get(GITHUB_API, timeout=10)
        if resp.status_code == 200:
            return resp.json()["sha"]
    except Exception as e:
        print(f"GitHub poll error: {e}")
    return None

async def health_server():
    async def handle(request):
        return web.Response(text="OK")
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Health server running on port 8080")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(auto_update())
    bot.loop.create_task(health_server())

async def auto_update():
    current_sha = get_latest_sha()
    print(f"Starting commit SHA: {current_sha[:7] if current_sha else 'unknown'}")

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        latest_sha = get_latest_sha()
        if latest_sha and latest_sha != current_sha:
            print(f"New commit detected: {latest_sha[:7]} — pulling updates...")
            try:
                subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
                subprocess.run(["git", "checkout", "origin/main", "--", "memory_flash.py"], check=True, capture_output=True)
                reload_items()
                current_sha = latest_sha
                print("Update complete.")
            except Exception as e:
                print(f"Update failed: {e}")


# ITEM SELECT
class ItemSelect(discord.ui.Select):
    def __init__(self, category):
        self.category = category

        options = [
            discord.SelectOption(label=data["name"], value=key)
            for key, data in categories[category][:25]
        ]

        super().__init__(placeholder="Choose an item...", options=options)

    async def callback(self, interaction: discord.Interaction):
        data = items[self.values[0]]

        embed = discord.Embed(
            title=f"{data['name']} Price Check",
            description=data["description"],
            color=category_color(self.category),
        )

        embed.add_field(name="📁 Category", value=data["category"], inline=False)
        embed.add_field(name="💰 Average Price", value=f"`{data['avg_price']} AI`", inline=False)
        embed.add_field(name="📊 Low / High", value=f"`{data['low']} AI` — `{data['high']} AI`", inline=False)
        embed.add_field(name="📉 Very Low / Very High", value=f"`{data['very_low']} AI` — `{data['very_high']} AI`", inline=False)
        embed.add_field(name="🔻 🔺 Absolute Min / Absolute Max", value=f"`{data['abs_min']} AI` — `{data['abs_max']} AI`", inline=False)

        await interaction.response.edit_message(embed=embed, view=None)


# ITEM VIEW
class ItemView(discord.ui.View):
    def __init__(self, category):
        super().__init__()
        self.add_item(ItemSelect(category))


# CATEGORY SELECT
class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=cat, value=cat) for cat in categories.keys()
        ]

        super().__init__(placeholder="Choose a category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        embed = discord.Embed(
            title=f"{category}",
            description="Select an item from this category",
            color=category_color(category),
        )

        await interaction.response.edit_message(embed=embed, view=ItemView(category))


# CATEGORY VIEW
class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(CategorySelect())


# SLASH COMMAND
@bot.tree.command(name="pricecheck", description="Check the price of an item from the sheet")
async def find(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Price Finder",
        description="Choose item category",
        color=discord.Color.blurple(),
    )

    await interaction.response.send_message(embed=embed, view=CategoryView())


bot.run(TOKEN)
