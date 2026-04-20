import discord
from discord import app_commands
from discord.ext import commands
from memory_flash import items
import os

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 🧠 group items by category
categories = {}
for key, data in items.items():
    categories.setdefault(data["category"], []).append((key, data))


# 🔽 ITEM SELECT
class ItemSelect(discord.ui.Select):
    def __init__(self, category):
        self.category = category

        options = [
            discord.SelectOption(
                label=data["name"],
                value=key
            )
            for key, data in categories[category][:25]
        ]

        super().__init__(
            placeholder="Choose an item...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        data = items[self.values[0]]

        embed = discord.Embed(
            title=data["name"],
            description=data["description"],
            color=discord.Color.green()
        )

        embed.add_field(name="Category", value=data["category"])
        embed.add_field(name="Avg Price", value=data["avg_price"])
        embed.add_field(name="Min / Max", value=f"{data['abs_min']} / {data['abs_max']}")
        embed.add_field(name="Low / High", value=f"{data['low']} / {data['high']}")

        await interaction.response.edit_message(embed=embed, view=None)


# 🔲 ITEM VIEW
class ItemView(discord.ui.View):
    def __init__(self, category):
        super().__init__()
        self.add_item(ItemSelect(category))


# 🔽 CATEGORY SELECT
class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=cat, value=cat)
            for cat in categories.keys()
        ]

        super().__init__(
            placeholder="Choose a category...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        embed = discord.Embed(
            title=f"{category}",
            description="Select an item from this category",
            color=discord.Color.blue()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=ItemView(category)
        )


# 🔲 CATEGORY VIEW
class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(CategorySelect())


# 🔥 SLASH COMMAND
@bot.tree.command(name="find", description="Find an item")
async def find(interaction: discord.Interaction):

    embed = discord.Embed(
        title="Item Finder",
        description="Choose a category to begin",
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(
        embed=embed,
        view=CategoryView()
    )


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


bot.run(TOKEN)
