import discord
from discord.ext import commands
from discord import app_commands, Interaction
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SHOP_ID = os.getenv("SELLAUTH_SHOP_ID")
API_KEY = os.getenv("SELLAUTH_API_KEY")
GUILD_ID = 1432550511495610472
ROLE_ID = 1438358929187934310

class InvoiceRedeem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="invoice", description="Redeem your invoice to receive a role.")
    @app_commands.describe(invoice_id="Your SellAuth invoice ID")
    async def invoice(self, interaction: Interaction, invoice_id: str):

        if not SHOP_ID or not API_KEY:
            return await interaction.response.send_message(
                "⚠️ SellAuth API is not configured. Please set SELL_AUTH_SHOP_ID and SELL_AUTH_API_KEY in `.env`.",
                ephemeral=True
            )

        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return await interaction.response.send_message("Guild not found.", ephemeral=True)

        role = guild.get_role(ROLE_ID)
        if not role:
            return await interaction.response.send_message("Required role does not exist anymore.", ephemeral=True)

        await interaction.response.defer(ephemeral=True, thinking=True)

        url = f"https://api.sellauth.com/v1/shops/{SHOP_ID}/invoices/{invoice_id}"
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }

        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            return await interaction.followup.send(f"⚠️ API request failed: `{e}`", ephemeral=True)

        if response.status_code == 404:
            return await interaction.followup.send("❌ Invoice not found.", ephemeral=True)

        if response.status_code != 200:
            return await interaction.followup.send(
                f"❌ SellAuth API error: `{response.status_code}`\n```{response.text}```",
                ephemeral=True
            )

        data = response.json()

        if not data.get("paid", False):
            return await interaction.followup.send(
                "⚠️ Invoice exists, but it is **not paid**.", ephemeral=True
            )

        try:
            await interaction.user.add_roles(role, reason=f"Invoice {invoice_id} verified via SellAuth")
        except discord.Forbidden:
            return await interaction.followup.send("⚠️ Missing permission to assign role.", ephemeral=True)

        await interaction.followup.send(
            f"✅ Invoice **{invoice_id}** verified!\nYou received **{role.name}**.",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(InvoiceRedeem(bot))
