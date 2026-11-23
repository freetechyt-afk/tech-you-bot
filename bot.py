import discord
from discord.ext import commands
import requests
import asyncio
import os
import xml.etree.ElementTree as ET
from aiohttp import web

# ==============================================================================
# TECH YOU DISCORD BOT - FULL AUTOMATION & PROGRESSIVE VERIFICATION ENGINE
# Features:
# 1. Progressive Verification (#verify-to-unlock: Step 1 Free Unlock -> Step 2 VIP Unlock)
# 2. VIP Key Generation & Smart 30-Day Auto-Renewal (1 Member = 1 Key = 1 PC Only)
# 3. Anti-Piracy Auto-Revoke (Revokes GTA 5 Mod Key if member leaves Discord)
# 4. Automatic YouTube Video Alerts (Pings #youtube-videos every 2 minutes)
# 5. 24/7 Cloud Web Keep-Alive (Compatible with Render / Koyeb)
# Author: Sumit Arora (TECH YOU)
# ==============================================================================

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
if not BOT_TOKEN:
    token_path = os.path.join(os.path.dirname(__file__), "token.txt")
    if os.path.exists(token_path):
        with open(token_path, "r") as f:
            BOT_TOKEN = f.read().strip()

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzz1ajljW-WEYAIu4wv-PgFCJkDQ5fQ5fdWMvm-iGJfqjqvMqX3b0CWzPlG0iAB1cPP5w/exec"
BOT_API_SECRET = "TECH_YOU_BOT_SECRET_2026"
YOUTUBE_SUB_URL = "https://youtube.com/@techuk7?sub_confirmation=1"
YOUTUBE_JOIN_URL = "https://youtube.com/@techuk7/join"
YOUTUBE_CHANNEL_ID = "UCuhKDpdEVkTJNSdc_zgeCww"
g_last_posted_video_id = "YAUnKq0ZWi0"

MEMBER_ROLE_NAMES = ["⭐ TECH YOU Member", "TECH YOU Member", "Tech You Member", "VIP Member", "Member"]
VERIFIED_ROLE_NAMES = ["Verified", "verified", "Member", "member"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------------------------------------------------------------
# STEP 2 VIEW: VIP MEMBERSHIP UNLOCK (Shown AFTER Step 1 is completed!)
# ------------------------------------------------------------------------------
class Step2VipView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="⭐ Join YouTube Membership",
            style=discord.ButtonStyle.link,
            url=YOUTUBE_JOIN_URL,
            emoji="👑"
        ))

    @discord.ui.button(
        label="👑 Step 2: Verify VIP Membership",
        style=discord.ButtonStyle.primary,
        custom_id="verify_step2_vip_button",
        emoji="✨"
    )
    async def verify_step2_vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        guild = interaction.guild

        if not isinstance(user, discord.Member):
            return

        is_member = False
        user_roles = [r.name.lower() for r in user.roles]
        for r_name in MEMBER_ROLE_NAMES:
            if r_name.lower() in user_roles:
                is_member = True
                break

        if user.guild_permissions.administrator or user == guild.owner:
            is_member = True

        if is_member:
            await interaction.followup.send(
                "🎉 **सत्यापन सफल! आप एक आधिकारिक TECH YOU VIP Member हैं!** 👑\n\n"
                "✅ आपका **`#🔑-claim-mod-key`** चैनल अनलॉक हो चुका है!\n"
                "👉 अभी `#🔑-claim-mod-key` चैनल में जाएं और **[👑 Claim VIP Mod Key]** बटन दबाकर अपनी 30-Day Key और डायरेक्ट डाउनलोड लिंक प्राप्त करें!",
                ephemeral=True
            )
        else:
            join_view = discord.ui.View()
            join_view.add_item(discord.ui.Button(
                label="👑 Join YouTube Membership Now",
                style=discord.ButtonStyle.link,
                url=YOUTUBE_JOIN_URL,
                emoji="🔴"
            ))
            await interaction.followup.send(
                "⚠️ **YouTube Membership Not Detected!**\n\n"
                "आपके अकाउंट पर अभी तक **`⭐ TECH YOU Member`** रोल नहीं मिला है।\n\n"
                "📌 **इसे एक्टिवेट करने के 2 आसान स्टेप्स:**\n"
                "1️⃣ **अगर मेंबरशिप नहीं ली है:** नीचे दिए गए लाल बटन पर क्लिक करके YouTube चैनल की मेंबरशिप लें।\n"
                "2️⃣ **अगर मेंबरशिप ले ली है:**\n"
                "   • Discord की **User Settings (⚙️) ➔ Connections** में जाएं।\n"
                "   • अपना **YouTube Account** लिंक करें (जिससे मेंबरशिप खरीदी है)।\n"
                "   • Discord 1 मिनट के अंदर आपको अपने आप VIP Member रोल दे देगा!\n\n"
                "रोल मिलते ही `#🔑-claim-mod-key` चैनल अपने आप खुल जाएगा!",
                view=join_view,
                ephemeral=True
            )

# ------------------------------------------------------------------------------
# STEP 1 VIEW: PUBLIC CHANNEL VERIFY-TO-UNLOCK PANEL
# ------------------------------------------------------------------------------
class Sub2UnlockStep1View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Subscribe on YouTube",
            style=discord.ButtonStyle.link,
            url=YOUTUBE_SUB_URL,
            emoji="▶️"
        ))

    @discord.ui.button(
        label="Verify to Unlock",
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

        # Find target role for Free / Verified access
        target_role = None
        for r_name in VERIFIED_ROLE_NAMES:
            r = discord.utils.get(guild.roles, name=r_name)
            if r:
                target_role = r
                break

        if not target_role:
            for r in guild.roles:
                if "verif" in r.name.lower():
                    target_role = r
                    break

        if target_role:
            try:
                await user.add_roles(target_role)
            except discord.errors.Forbidden:
                await interaction.followup.send(
                    "⚠️ **Discord Permission Error:** Bot का रोल Server Settings में 'Verified' रोल के नीचे है!\n"
                    "👉 एडमिन से कहें कि Discord Settings ➔ Roles में जाकर Bot के रोल को 'Verified' के ऊपर ड्रैग करें।",
                    ephemeral=True
                )
                return
            except Exception as e:
                await interaction.followup.send(f"⚠️ Error: {str(e)}", ephemeral=True)
                return

        # STEP 1 SUCCESS -> REVEALS STEP 2 (VIP OPTION) IN A CLEAN CARD
        step1_success_msg = (
            "🎉 **सत्यापन सफल (Step 1 Complete)!**\n\n"
            "✅ आपका सर्वर अनलॉक हो चुका है!\n"
            "• `#🎁-free-mods` ➔ फ्री मोड्स और सॉफ्टवेयर डाउनलोड करें\n"
            "• `#general-chat` ➔ कम्युनिटी चैट में बातचीत करें\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 **STEP 2: VIP MODS & REAL LIFE RP ACCESS**\n"
            "अगर आप **TECH YOU YouTube Member** हैं, तो VIP Real Life RP Mod और 30-Day Key अनलॉक करने के लिए नीचे दिए गए **'Step 2: Verify VIP'** बटन पर क्लिक करें!"
        )

        await interaction.followup.send(
            step1_success_msg,
            view=Step2VipView(),
            ephemeral=True
        )

# ------------------------------------------------------------------------------
# VIP MOD KEY CLAIM VIEW (#🔑-claim-mod-key)
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
                url=YOUTUBE_JOIN_URL,
                emoji="🔴"
            ))
            await interaction.followup.send(
                "❌ **Access Denied! (यह सुविधा केवल YouTube Members के लिए है)**\n\n"
                "यह Real Life RP Master Mod केवल हमारे **YouTube Channel Members** के लिए विशेष रूप से बनाई गई है!\n\n"
                "👉 नीचे दिए गए बटन पर क्लिक करके मेंबरशिप जॉइन करें और Discord Settings में अपना YouTube लिंक करें।",
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
        download_url = data.get("downloadUrl", "https://drive.google.com/file/d/13c2oYCD25p21DBFO3_dIW2r4ZfTM_0AI/view?usp=sharing")
        expiry_date = data.get("expiryDate", "30 Days from activation")

        # CASE 1: BRAND NEW KEY ISSUED
        if status == "SUCCESS":
            msg = (
                f"🎉 **बधाई हो {user.mention}! आपकी VIP Mod Key जारी कर दी गई है:**\n\n"
                f"🔑 **VIP Activation Key:** `{license_key}`\n\n"
                f"📥 **Mod Download Link:** [यहाँ से डाउनलोड करें (Google Drive)]({download_url})\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 **एक्टिवेशन गाइड:**\n"
                f"1. डाउनलोड की गई Zip फाइल को अनज़िप करके GTA 5 के मुख्य फ़ोल्डर में डालें।\n"
                f"2. गेम चालू करें और स्क्रीन पर ऑन-स्क्रीन कीबोर्ड दिखने पर यह Key टाइप करके Enter दबाएं।\n"
                f"*(या `RealLifeRPMaster.ini` फ़ाइल खोलकर `ActivationKey={license_key}` लिखकर सेव कर लें)*\n\n"
                f"⚠️ *ध्यान दें: यह Key केवल 1 PC के लिए मान्य है (HWID Bound)। इसे किसी के साथ साझा न करें!*"
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

        # CASE 2: USER ALREADY HAS ACTIVE KEY
        elif status == "ALREADY_HAS_KEY":
            await interaction.followup.send(
                f"ℹ️ **{user.mention}, आपके पास पहले से एक्टिव Key मौजूद है:**\n\n"
                f"🔑 **आपकी Active Key:** `{license_key}`\n"
                f"⏳ **Expiry Info:** `{expiry_date}`\n"
                f"📥 **Mod Download:** [Google Drive Download Link]({download_url})\n\n"
                f"🔒 **Single-Device Policy:** यह Key आपके PC (HWID) पर लॉक है और एक्टिव है। किसी नई Key की आवश्यकता नहीं है!",
                ephemeral=True
            )

        # CASE 3: EXPIRED KEY SUCCESSFULLY RENEWED (+30 DAYS)
        elif status == "RENEWED_KEY":
            await interaction.followup.send(
                f"🔄 **Welcome Back {user.mention}! आपकी VIP Key सफलतापूर्वक Renew हो गई है:**\n\n"
                f"🔑 **आपकी Key:** `{license_key}`\n"
                f"⏳ **नई Expiry Date:** `{expiry_date}` (+30 Days Added)\n"
                f"📥 **Mod Download:** [Google Drive Download Link]({download_url})\n\n"
                f"✅ आपकी सदस्यता वेरीफाई हो चुकी है। आपको गेम में नई Key डालने की ज़रूरत नहीं है, पुरानी Key ही एक्टिवेट रहेगी!",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ **Error:** Key जनरेट नहीं हो सकी।\nResponse: `{data.get('message', 'Unknown Error')}`",
                ephemeral=True
            )

# ------------------------------------------------------------------------------
# LEAVE EVENT (ANTI-PIRACY AUTO-REVOKE)
# ------------------------------------------------------------------------------
@bot.event
async def on_member_remove(member: discord.Member):
    print(f"⚠️ Member Left Server: {member.name} ({member.id})")
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
# AUTOMATIC YOUTUBE VIDEO ALERT CHECKER (EVERY 2 MINUTES)
# ------------------------------------------------------------------------------
async def youtube_feed_checker():
    global g_last_posted_video_id
    await bot.wait_until_ready()
    print("Started Automatic YouTube Video Checker (Checking every 2 mins)...", flush=True)
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
    
    while not bot.is_closed():
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: requests.get(rss_url, timeout=15))
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
                entry = root.find('atom:entry', ns)
                if entry is not None:
                    vid_elem = entry.find('yt:videoId', ns)
                    title_elem = entry.find('atom:title', ns)
                    if vid_elem is not None and title_elem is not None:
                        vid_id = vid_elem.text
                        vid_title = title_elem.text
                        if vid_id != g_last_posted_video_id:
                            print(f"New YouTube video detected: {vid_title} ({vid_id})!", flush=True)
                            g_last_posted_video_id = vid_id
                            video_url = f"https://www.youtube.com/watch?v={vid_id}"
                            content = (
                                f"@everyone 🚨 **TECH YOU KI BRAND NEW VIDEO IS LIVE!** 🔥🎬\n\n"
                                f"**{vid_title}**\n\n"
                                f"▶️ **Abhi Dekhein (Watch Now):** {video_url}\n\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"👑 **VIP Mod Kaise Download Karein:**\n"
                                f"1️⃣ Channel Join karein: https://youtube.com/@techuk7/join\n"
                                f"2️⃣ `#🔑-claim-mod-key` me jakar **[👑 Claim VIP Mod Key]** dabayein aur apni 1-PC Key lein!"
                            )
                            for guild in bot.guilds:
                                for ch in guild.text_channels:
                                    if "youtube" in ch.name.lower() or "video" in ch.name.lower():
                                        await ch.send(content)
                                        print(f"Posted new YouTube video alert to #{ch.name}!", flush=True)
                                        break
        except Exception as e:
            print(f"YouTube feed check error: {e}", flush=True)
            
        await asyncio.sleep(120)

# ------------------------------------------------------------------------------
# ADMIN COMMANDS (!setup_verify, !setup_claim, !check_roles)
# ------------------------------------------------------------------------------
@bot.command(name="setup_verify")
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    """Force posts the Step 1 Verification Panel in the current channel"""
    embed = discord.Embed(
        title="🔓 TECH YOU - VERIFY TO UNLOCK",
        description=(
            "**TECH YOU Official Discord Server** में आपका स्वागत है!\n\n"
            "हमारे सभी Free GTA 5 Mods, टूल्स और बातचीत अनलॉक करने के लिए:\n\n"
            "1️⃣ नीचे दिए गए **Subscribe on YouTube** बटन से हमारे चैनल को सब्सक्राइब करें।\n"
            "2️⃣ सब्सक्राइब करने के बाद **Verify to Unlock** बटन दबाएं।\n\n"
            "⚡ सर्वर तुरंत अनलॉक हो जाएगा और आप फ्री मोड्स डाउनलोड कर सकेंगे!"
        ),
        color=0x00e5ff
    )
    await ctx.send(embed=embed, view=Sub2UnlockStep1View())
    await ctx.message.delete()
    print(f"Admin {ctx.author.name} posted Step 1 Verification Panel in #{ctx.channel.name}!")

@bot.command(name="setup_claim")
@commands.has_permissions(administrator=True)
async def setup_claim(ctx):
    """Force posts the VIP Mod Claim Panel in the current channel"""
    embed = discord.Embed(
        title="👑 TECH YOU VIP - MOD ACTIVATION PANEL",
        description=(
            "हमारे सभी **YouTube Channel Members** के लिए एक्सक्लूसिव Real Life RP और कस्टम मोड्स का ऑफिशियल एक्टिवेशन हब!\n\n"
            "🔑 **अपनी VIP Mod Key प्राप्त / रीन्यू करने के लिए:**\n"
            "नीचे दिए गए **[👑 Claim VIP Mod Key]** बटन पर क्लिक करें।\n\n"
            "⚡ बॉट आपकी मेंबरशिप वेरीफाई करके आपको पर्सनल Activation Key और डायरेक्ट डाउनलोड लिंक प्रदान करेगा।\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "▶️ **मेंबरशिप जॉइन करें:** [Join YouTube Membership](https://youtube.com/@techuk7/join)\n"
            "🔒 **Strict Single-PC Policy:** 1 Member = 1 Key = 1 PC Binding (HWID Bound)."
        ),
        color=0x00ff88
    )
    await ctx.send(embed=embed, view=KeyClaimView())
    await ctx.message.delete()
    print(f"Admin {ctx.author.name} posted VIP Claim Panel in #{ctx.channel.name}!")

@bot.command(name="check_roles")
@commands.has_permissions(administrator=True)
async def check_roles(ctx):
    """Checks role hierarchy and permissions for debugging"""
    guild = ctx.guild
    bot_member = guild.get_member(bot.user.id)
    bot_top_role = bot_member.top_role

    lines = [f"🤖 **Bot Name:** `{bot.user.name}` | **Top Role:** `@{bot_top_role.name}` (Position: {bot_top_role.position})", ""]
    lines.append("📋 **Server Roles Hierarchy (Highest to Lowest):**")
    for r in sorted(guild.roles, key=lambda x: x.position, reverse=True)[:15]:
        can_manage = "✅" if bot_top_role.position > r.position else "❌ (Bot Cannot Assign)"
        lines.append(f"• `@{r.name}` (Pos: {r.position}) ➔ {can_manage}")

    await ctx.send("\n".join(lines))

# ------------------------------------------------------------------------------
# BOT ON_READY EVENT
# ------------------------------------------------------------------------------
@bot.event
async def on_ready():
    print("=" * 60, flush=True)
    print(f"TECH YOU MOD MANAGER ONLINE: {bot.user.name} (ID: {bot.user.id})", flush=True)
    print("=" * 60, flush=True)

    bot.add_view(KeyClaimView())
    bot.add_view(Sub2UnlockStep1View())
    bot.add_view(Step2VipView())

    if not hasattr(bot, "_yt_checker_started"):
        bot._yt_checker_started = True
        bot.loop.create_task(youtube_feed_checker())

    for guild in bot.guilds:
        print(f"Connected to Guild: {guild.name} (ID: {guild.id})", flush=True)

        # Auto-post or refresh VIP Panel in #claim-mod-key
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
                            "नीचे दिए गए **[👑 Claim VIP Mod Key]** बटन पर क्लिक करें।\n\n"
                            "⚡ बॉट आपकी मेंबरशिप वेरीफाई करके आपको पर्सनल Activation Key और डायरेक्ट डाउनलोड लिंक प्रदान करेगा।\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "▶️ **मेंबरशिप जॉइन करें:** [Join YouTube Membership](https://youtube.com/@techuk7/join)\n"
                            "🔒 **Strict Single-PC Policy:** 1 Member = 1 Key = 1 PC Binding (HWID Bound)."
                        ),
                        color=0x00ff88
                    )
                    await ch.send(embed=embed, view=KeyClaimView())
                    print(f"Posted VIP Panel in #{ch.name}!")

            # Auto-post or refresh Step 1 Panel in #verify
            if "verify" in ch.name.lower():
                has_panel = False
                async for msg in ch.history(limit=10):
                    if msg.author == bot.user and msg.embeds:
                        for emb in msg.embeds:
                            if "VERIFY TO UNLOCK" in str(emb.title):
                                has_panel = True
                                break
                    if has_panel:
                        break

                if not has_panel:
                    embed = discord.Embed(
                        title="🔓 TECH YOU - VERIFY TO UNLOCK",
                        description=(
                            "**TECH YOU Official Discord Server** में आपका स्वागत है!\n\n"
                            "हमारे सभी Free GTA 5 Mods, टूल्स और बातचीत अनलॉक करने के लिए:\n\n"
                            "1️⃣ नीचे दिए गए **Subscribe on YouTube** बटन से हमारे चैनल को सब्सक्राइब करें।\n"
                            "2️⃣ सब्सक्राइब करने के बाद **Verify to Unlock** बटन दबाएं।\n\n"
                            "⚡ सर्वर तुरंत अनलॉक हो जाएगा और आप फ्री मोड्स डाउनलोड कर सकेंगे!"
                        ),
                        color=0x00e5ff
                    )
                    await ch.send(embed=embed, view=Sub2UnlockStep1View())
                    print(f"Posted Step 1 Panel in #{ch.name}!")

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
