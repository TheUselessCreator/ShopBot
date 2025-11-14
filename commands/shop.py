import discord
from discord.ext import commands, tasks
from discord import app_commands, ui, Interaction
import asyncio
from utils.supabase import get_supabase

SHOP_CHANNEL_ID = 1438316497343610920
LOG_CHANNEL_ID = 1438335336718798952
GUILD_ID = 1432550511495610472
SHOP_URL = "https://glxyshop.mysellauth.com"
BOT_LOGO_URL = "https://cdn.discordapp.com/icons/1432550511495610472/a_default.png?size=1024"

supabase = get_supabase()

class ShopView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

        self.add_item(ui.Button(label="Purchase Keys", url=SHOP_URL, style=discord.ButtonStyle.link))

    @ui.button(label="Redeem Key", style=discord.ButtonStyle.primary)
    async def redeem_key(self, interaction: Interaction, button: ui.Button):
        """Redeem key button — opens a modal."""
        await interaction.response.send_modal(RedeemKeyModal(self.bot))

class RedeemKeyModal(ui.Modal, title="Redeem Your Product Key"):
    key_input = ui.TextInput(label="Enter your key", placeholder="xxxx-xxxx-xxxx", required=True)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: Interaction):
        key = self.key_input.value.strip()

        response = supabase.table("products").select("*").eq("key", key).execute()

        if not response.data:
            await interaction.response.send_message("Invalid or already used key.", ephemeral=True)
            return

        product_row = response.data[0]
        product_name = product_row.get("product", "Unknown Product")
        product_context = product_row.get("context", "No data provided")

        embed = discord.Embed(
            title="Product Redeemed",
            description=f"Thanks for your order of **{product_name}**!\n"
                        f"This can also be found in your product list.\n\n"
                        f"Here’s your product:\n\n||```\n{product_context}\n```||",
            color=discord.Color.green()
        )
        embed.set_footer(text=SHOP_URL)

        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I couldn’t DM you. Please enable DMs and try again.", ephemeral=True)
            return

        supabase.table("products").delete().eq("key", key).execute()

        log_channel = self.bot.get_guild(GUILD_ID).get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="Key Redeemed",
                color=discord.Color.orange()
            )
            log_embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
            log_embed.add_field(name="Product", value=product_name, inline=False)
            log_embed.add_field(name="Key", value=key, inline=False)
            await log_channel.send(embed=log_embed)

        await interaction.response.send_message("Key redeemed successfully! Check your DMs.", ephemeral=True)

class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shop_message = None
        self.refresh_shop.start()

    def cog_unload(self):
        self.refresh_shop.cancel()

    @tasks.loop(minutes=1)
    async def refresh_shop(self):
        """Refresh the shop embed every minute to prevent expired interactions."""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(SHOP_CHANNEL_ID)
        if not channel:
            return

        try:
            async for msg in channel.history(limit=10):
                if msg.author == self.bot.user:
                    await msg.delete()
        except Exception as e:
            print(f"Could not delete old messages: {e}")

        embed = discord.Embed(
            title="SHOP DASHBOARD",
            description=(
                "Welcome to the Account Dashboard.\n"
                "Use the options below to navigate features and manage your account.\n"
                "**Warning** If your code fails, try running the /code-redeem command."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text=SHOP_URL)
        embed.set_thumbnail(url=BOT_LOGO_URL)

        view = ShopView(self.bot)
        self.shop_message = await channel.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
