import discord
from discord.ext import commands
import requests
import asyncio
import os
from aiohttp import web

# ==============================================================================
# TECH YOU DISCORD BOT - FULL AUTOMATION ENGINE
# Features:
# 1. VIP Key Generation (Connected to Google Sheet)
# 2. Sub2Unlock YouTube Verification Gateway
# 3. Anti-Cheat Auto-Revoke (Revokes GTA 5 Mod Key if member leaves Discord)
# 4. 24/7 Cloud Web Keep-Alive (Compatible with Render / Koyeb)
# Author: Sumit Arora (TECH YOU)
# ==============================================================================

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
if not BOT_TOKEN:
    # Fallback to local config file if exists
    token_path = os.path.join(os.path.dirname(__file__), "token.txt")
    if os.path.exists(token_path):
        with open(token_path, "r") as f:
            BOT_TOKEN = f.read().strip()
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzfPE0UQMqNil1FdhV7J_nZee5I5dQOzEBTQki99VlW-fxPDg5d8JqmkI7SexpXl08qIA/exec"
BOT_API_SECRET = "TECH_YOU_BOT_SECRET_2026"
YOUTUBE_SUB_URL = "https://youtube.com/@techuk7?sub_confirmation=1"

MEMBER_ROLE_NAMES = ["⭐ TECH YOU Member", "TECH YOU Member", "Tech You Member", "Member"]
VERIFIED_ROLE_NAME = "Verified"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------------------------------------------------------------
# 1. SUB2UNLOCK VERIFICATION VIEW
# ------------------------------------------------------------------------------
class Sub2UnlockView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Add URL Button (Step 1)
        self.add_item(discord.ui.Button(
            label="🔴 Step 1: Subscribe on YouTube",
            style=discord.ButtonStyle.link,
            url=YOUTUBE_SUB_URL,
            emoji="▶️"
        ))

    @discord.ui.button(
        label="✅ Step 2: Verify & Unlock Server",
        style=discord.ButtonStyle.success,
        custom_id="verify_sub_unlock_button",
        emoji="🔓"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        guild = interaction.guild

        if not isinstance(user, discord.Member):
            return

        # Find or create Verified role
        role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        if not role:
            # Fallback to Member role if exists
            role = discord.utils.get(guild.roles, name="Member")

        if role:
            try:
                await user.add_roles(role)
            except Exception as e:
                print(f"Role add error: {e}")

        await interaction.followup.send(
            "🎉 **सत्यापन सफल (Verification Success)!**\n\n"
            "आपका डिस्कोर्ड सर्वर पूरी तरह अनलॉक हो चुका है!\n"
            "▶️ हमारे मोड्स डाउनलोड करने के लिए `#tech-you-custom-mods` देखें।\n"
            "▶️ बातचीत के लिए `#general-chat` में आएं।\n\n"
            "*TECH YOU परिवार में आपका स्वागत है!*",
            ephemeral=True
        )

# ------------------------------------------------------------------------------
# 2. VIP MOD KEY CLAIM VIEW
# ------------------------------------------------------------------------------
class KeyClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="👑 Claim VIP Mod Key",
        style=discord.ButtonStyle.success,
        custom_id="claim_vip_mod_key_button",
        emoji="🔑"
    )
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        user = interaction.user
        guild = interaction.guild

        is_member = False
        if isinstance(user, discord.Member):
            if user.guild_permissions.administrator or user == guild.owner:
                is_member = True
            else:
                user_roles = [r.name.lower() for r in user.roles]
                for r_name in MEMBER_ROLE_NAMES:
                    if r_name.lower() in user_roles:
                        is_member = True
                        break

        if not is_member:
            join_view = discord.ui.View()
            join_view.add_item(discord.ui.Button(
                label="👑 Join YouTube Membership Now",
                style=discord.ButtonStyle.link,
                url="https://youtube.com/@techuk7/join",
                emoji="🔴"
            ))
            await interaction.followup.send(
                "❌ **Access Denied! (यह सुविधा केवल YouTube Members के लिए है)**\n\n"
                "यह Real Life RP Master Mod और VIP Keys केवल हमारे **YouTube Channel Members** के लिए विशेष रूप से बनाई गई हैं!\n\n"
                "👉 **अगर आप भी इस मोड को डाउनलोड और एक्टिवेट करना चाहते हैं:**\n"
                "नीचे दिए गए **Join YouTube Membership Now** बटन पर क्लिक करके हमारे चैनल के मेंबर बनें!\n\n"
                "*(मेंबर बनने के बाद Discord Settings -> Connections में अपना YouTube लिंक करें, और तुरंत अपनी Key प्राप्त करें!)*",
                view=join_view,
                ephemeral=True
            )
            return

        params = {
            "action": "generate_key",
            "secret": BOT_API_SECRET,
            "discord_id": str(user.id),
            "discord_name": f"{user.name}"
        }

        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: requests.get(WEB_APP_URL, params=params, timeout=30))
            data = res.json()
        except Exception as e:
            await interaction.followup.send(
                f"⚠️ **Server Busy:** Google API से कनेक्ट करने में दिक्कत आई। कृपया 1 मिनट बाद पुनः प्रयास करें।\n`{str(e)}`",
                ephemeral=True
            )
            return

        status = data.get("status")
        license_key = data.get("key", "N/A")
        download_url = data.get("downloadUrl", "https://drive.google.com/file/d/1l3ncAWBQagr9EVFsW-OiGOwtk1Sdok-E/view?usp=sharing")

        if status == "SUCCESS":
            msg = (
                f"🎉 **बधाई हो {user.mention}! आपकी VIP Mod Key सफलतापूर्वक जारी कर दी गई है:**\n\n"
                f"🔑 **VIP Activation Key:** `{license_key}`\n\n"
                f"📥 **Mod Download Link:** [यहाँ से डाउनलोड करें (Google Drive)]({download_url})\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 **एक्टिवेशन गाइड:**\n"
                f"1. डाउनलोड की गई Zip फाइल को अनज़िप करके GTA 5 के मुख्य फ़ोल्डर में डालें।\n"
                f"2. गेम चालू करें और स्क्रीन पर ऑन-स्क्रीन कीबोर्ड दिखने पर यह Key टाइप करके Enter दबाएं।\n"
                f"*(या `RealLifeRPMaster.ini` फ़ाइल खोलकर `ActivationKey={license_key}` लिखकर सेव कर लें)*\n\n"
                f"⚠️ *ध्यान दें: यह Key केवल 1 PC के लिए मान्य है। इसे किसी के साथ साझा न करें!*"
            )
            await interaction.followup.send(msg, ephemeral=True)

            try:
                await user.send(
                    f"👑 **TECH YOU VIP MOD ACCESS**\n"
                    f"आपकी Key: `{license_key}`\n"
                    f"डाउनलोड: {download_url}\n"
                    f"सुरक्षित रखने के लिए धन्यवाद!"
                )
            except Exception:
                pass

        elif status == "ALREADY_HAS_KEY":
            await interaction.followup.send(
                f"ℹ️ **{user.mention}, आपके पास पहले से एक्टिव Key मौजूद है:**\n\n"
                f"🔑 **आपकी Active Key:** `{license_key}`\n"
                f"📥 **Mod Download:** [Google Drive Download Link]({download_url})\n\n"
                f"यह Key आपके अकाउंट पर पहले से एक्टिव है और काम कर रही है।",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ **Error:** Key जनरेट नहीं हो सकी। कृपया एडमिन से संपर्क करें।\nResponse: `{data.get('message', 'Unknown Error')}`",
                ephemeral=True
            )

# ------------------------------------------------------------------------------
# 3. LEAVE EVENT (ANTI-PIRACY AUTO-REVOKE)
# ------------------------------------------------------------------------------
@bot.event
async def on_member_remove(member: discord.Member):
    print(f"⚠️ Member Left Server: {member.name} ({member.id})")
    # Automatically revoke any active keys in Google Sheet
    params = {
        "action": "revoke_key",
        "secret": BOT_API_SECRET,
        "discord_id": str(member.id)
    }
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: requests.get(WEB_APP_URL, params=params, timeout=10))
        print(f"Revoke response for {member.name}: {res.text}")
    except Exception as e:
        print(f"Failed to auto-revoke for {member.name}: {e}")

# ------------------------------------------------------------------------------
# 4. BOT ON_READY EVENT
# ------------------------------------------------------------------------------
@bot.event
async def on_ready():
    print("=" * 60, flush=True)
    print(f"TECH YOU MOD MANAGER ONLINE: {bot.user.name} (ID: {bot.user.id})", flush=True)
    print("=" * 60, flush=True)

    # Register persistent views
    bot.add_view(KeyClaimView())
    bot.add_view(Sub2UnlockView())

    if not bot.guilds:
        print("Bot is not in any guilds yet. Please invite using the OAuth2 link!", flush=True)

    for guild in bot.guilds:
        print(f"Connected to Guild: {guild.name} (ID: {guild.id})", flush=True)

        # Post VIP Key Panel in #claim-mod-key
        for ch in guild.text_channels:
            if "claim-mod-key" in ch.name.lower():
                has_panel = False
                async for msg in ch.history(limit=10):
                    if msg.author == bot.user and msg.embeds:
                        for emb in msg.embeds:
                            if "VIP MOD ACTIVATION" in str(emb.title):
                                has_panel = True
                                break
                    if has_panel:
                        break

                if not has_panel:
                    embed = discord.Embed(
                        title="👑 TECH YOU VIP - MOD ACTIVATION PANEL",
                        description=(
                            "हमारे सभी **YouTube Channel Members** के लिए एक्सक्लूसिव Real Life RP और कस्टम मोड्स का ऑफिशियल एक्टिवेशन हब!\n\n"
                            "🔑 **अपनी VIP Mod Key प्राप्त करने के लिए:**\n"
                            "नीचे दिए गए **Claim VIP Mod Key** बटन पर क्लिक करें।\n\n"
                            "⚡ बॉट आपकी मेंबरशिप वेरीफाई करके आपको पर्सनल Activation Key और डायरेक्ट डाउनलोड लिंक प्रदान करेगा।\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "▶️ **मेंबरशिप जॉइन करें:** [Join YouTube Membership](https://youtube.com/@techuk7)\n"
                            "⚠️ *यह Key केवल 1 PC के लिए सुरक्षित है।*"
                        ),
                        color=0x00ff88
                    )
                    await ch.send(embed=embed, view=KeyClaimView())
                    print(f"Posted VIP Panel in #{ch.name}!")

            # Post Sub2Unlock Panel in #verify-to-unlock (if channel exists)
            if "verify" in ch.name.lower():
                has_panel = False
                async for msg in ch.history(limit=10):
                    if msg.author == bot.user and msg.embeds:
                        for emb in msg.embeds:
                            if "UNLOCK SERVER" in str(emb.title):
                                has_panel = True
                                break
                    if has_panel:
                        break

                if not has_panel:
                    embed = discord.Embed(
                        title="🔓 UNLOCK SERVER - VERIFICATION GATEWAY",
                        description=(
                            "**TECH YOU Official Discord Server** में आपका स्वागत है!\n\n"
                            "हमारे सभी GTA 5 मोड्स, डाउनलोड्स और कम्युनिटी चैनल्स अनलॉक करने के लिए:\n\n"
                            "1️⃣ **Step 1:** नीचे दिए गए **Subscribe on YouTube** बटन पर क्लिक करके हमारे चैनल **@techuk7** को सब्सक्राइब करें।\n"
                            "2️⃣ **Step 2:** सब्सक्राइब करने के बाद **Verify & Unlock Server** बटन दबाएं।\n\n"
                            "⚡ ऐसा करते ही पूरा सर्वर आपके लिए तुरंत अनलॉक हो जाएगा!"
                        ),
                        color=0xff0044
                    )
                    await ch.send(embed=embed, view=Sub2UnlockView())
                    print(f"Posted Sub2Unlock Panel in #{ch.name}!")

async def run_keep_alive():
    app = web.Application()
    async def index(request):
        return web.Response(text="TECH YOU BOT 24/7 ONLINE & HEALTHY!")
    app.router.add_get("/", index)
    app.router.add_get("/health", index)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web keep-alive server listening on port {port}...", flush=True)

async def main():
    await run_keep_alive()
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
