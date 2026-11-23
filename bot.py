import discord
from discord.ext import commands
import requests
import asyncio
import os
import csv
import io
import re
import xml.etree.ElementTree as ET
from aiohttp import web

# ==============================================================================
# TECH YOU DISCORD BOT - FULL AUTOMATION, 3-TIER ACCOUNTANT & KEY ENGINE
# Features:
# 1. 1-Click CSV Uploader & Accountant (!update_members):
#    - Sumit simply uploads YouTube Studio CSV in Discord
#    - Bot auto-populates Google Sheet, tracks 3 Tiers, and revokes cancelled members!
# 2. Live 3-Tier Growth Tracker (!stats / !members):
#    - ⚡ Tech You Legends ⚡, ⚡ Titans ⚡, ⚡ Supporters ⚡
#    - Joined vs Re-joined analytics
# 3. Smart Key Claim Modal (Direct Handle or Channel Link Entry)
# 4. Anti-Piracy Auto-Revoke & In-Game 1-PC HWID Lock
# 5. Automatic YouTube Video Alerts (Pings every 2 minutes)
# 6. 24/7 Cloud Web Keep-Alive (Compatible with Render)
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

MEMBER_ROLE_NAMES = ["⚡ Tech You Legends ⚡", "⚡ Titans ⚡", "⚡ Supporters ⚡", "⭐ TECH YOU Member", "TECH YOU Member", "VIP Member", "Member"]
VERIFIED_ROLE_NAMES = ["Verified", "verified", "Member", "member"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------------------------------------------------------------
# ERROR HANDLER (PREVENTS SILENT FAILS)
# ------------------------------------------------------------------------------
@bot.event
async def on_command_error(ctx, error):
    print(f"Command Error in #{ctx.channel.name}: {error}")
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⚠️ **Permission Denied:** यह कमांड केवल Server Owner / Admin के लिए है!")
    else:
        await ctx.send(f"⚠️ **Error:** `{str(error)}`")

# ------------------------------------------------------------------------------
# PING TEST COMMAND
# ------------------------------------------------------------------------------
@bot.command(name="ping")
async def ping(ctx):
    """Instant connectivity test"""
    await ctx.send(f"🏓 **Pong!** Bot 100% Online hai aur messages read kar raha hai! (Latency: {round(bot.latency * 1000)}ms)")

# ------------------------------------------------------------------------------
# HELPER: RESOLVE YOUTUBE HANDLE (@Mohit0306) TO CHANNEL ID (UCRTC...)
# ------------------------------------------------------------------------------
def resolve_youtube_handle_to_id(input_str: str) -> str:
    input_str = input_str.strip()
    m = re.search(r"UC[a-zA-Z0-9_-]{22}", input_str)
    if m:
        return m.group(0)

    handle = input_str
    if "youtube.com/@" in handle:
        handle = handle.split("youtube.com/@")[-1].split("/")[0].split("?")[0]
    elif handle.startswith("@"):
        handle = handle[1:]

    try:
        url = f"https://www.youtube.com/@{handle}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            m_id = re.search(r'"browseId":"(UC[a-zA-Z0-9_-]{22})"', resp.text)
            if m_id:
                return m_id.group(1)
            m_id2 = re.search(r'externalId":"(UC[a-zA-Z0-9_-]{22})"', resp.text)
            if m_id2:
                return m_id2.group(1)
    except Exception as e:
        print(f"Handle resolve error: {e}")

    return input_str

# ------------------------------------------------------------------------------
# MODAL: YOUTUBE HANDLE / CHANNEL INPUT FOR KEY CLAIM
# ------------------------------------------------------------------------------
class ClaimKeyModal(discord.ui.Modal, title="👑 Claim VIP Mod Key"):
    channel_input = discord.ui.TextInput(
        label="YouTube Handle or Channel Link",
        placeholder="e.g. @Mohit0306 or youtube.com/channel/UC...",
        required=True,
        max_length=150
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        raw_val = self.channel_input.value.strip()

        loop = asyncio.get_event_loop()
        channel_id = await loop.run_in_executor(None, lambda: resolve_youtube_handle_to_id(raw_val))

        params = {
            "action": "generate_key",
            "secret": BOT_API_SECRET,
            "discord_id": str(user.id),
            "discord_name": f"{user.name}",
            "channel_input": channel_id
        }

        try:
            res = await loop.run_in_executor(None, lambda: requests.get(WEB_APP_URL, params=params, timeout=25))
            data = res.json()
        except Exception as e:
            await interaction.followup.send(f"⚠️ **Server Busy:** Google Sheet API error: `{str(e)}`", ephemeral=True)
            return

        status = data.get("status")
        license_key = data.get("key", "N/A")
        tier = data.get("tier", "⚡ VIP Member ⚡")
        download_url = data.get("downloadUrl", "https://drive.google.com/file/d/13c2oYCD25p21DBFO3_dIW2r4ZfTM_0AI/view?usp=sharing")
        expiry_date = data.get("expiryDate", "30 Days from activation")

        if status == "SUCCESS":
            msg = (
                f"🎉 **बधाई हो {user.mention}! आपकी VIP Mod Key जारी कर दी गई है:**\n\n"
                f"🏆 **Membership Tier:** `{tier}`\n"
                f"🔑 **VIP Activation Key:** `{license_key}`\n\n"
                f"📥 **Mod Download Link:** [यहाँ से डाउनलोड करें (Google Drive)]({download_url})\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 **एक्टिवेशन गाइड:**\n"
                f"1. डाउनलोड की गई Zip फाइल को अनज़िप करके GTA 5 के मुख्य फ़ोल्डर में डालें।\n"
                f"2. `RealLifeRPMaster.ini` फ़ाइल खोलें और `ActivationKey={license_key}` लिखकर सेव कर लें।\n"
                f"3. गेम चालू करें — आपका 30-Day License तुरंत एक्टिव हो जाएगा!\n\n"
                f"🔒 *Strict Single-PC Policy: यह Key केवल 1 PC के लिए सुरक्षित है (HWID Bound)।*"
            )
            await interaction.followup.send(msg, ephemeral=True)
            try:
                await user.send(f"👑 **TECH YOU VIP MOD ACCESS ({tier})**\nआपकी Key: `{license_key}`\nडाउनलोड: {download_url}")
            except Exception:
                pass

        elif status == "ALREADY_HAS_KEY":
            await interaction.followup.send(
                f"ℹ️ **{user.mention}, आपके पास पहले से एक्टिव Key मौजूद है:**\n\n"
                f"🏆 **Tier:** `{tier}`\n"
                f"🔑 **आपकी Active Key:** `{license_key}`\n"
                f"⏳ **Expiry:** `{expiry_date}`\n"
                f"📥 **Mod Download:** [Google Drive Download Link]({download_url})\n\n"
                f"🔒 यह Key आपके PC पर लॉक है और एक्टिव है।",
                ephemeral=True
            )

        elif status == "RENEWED_KEY":
            await interaction.followup.send(
                f"🔄 **Welcome Back {user.mention}! आपकी VIP Key Renew हो गई है:**\n\n"
                f"🏆 **Tier:** `{tier}`\n"
                f"🔑 **आपकी Key:** `{license_key}`\n"
                f"⏳ **नई Expiry:** `{expiry_date}` (+30 Days Added)\n"
                f"📥 **Mod Download:** [Google Drive Download Link]({download_url})\n\n"
                f"✅ आपकी सदस्यता वेरीफाई हो चुकी है। पुरानी Key ही गेम में काम करती रहेगी!",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ **Verification Failed:**\n"
                f"यह YouTube Account (`{raw_val}`) हमारे एक्टिव मेंबर्स रिकॉर्ड में नहीं मिला।\n\n"
                f"👉 कृपया वही Handle या Channel Link डालें जिससे आपने **TECH YOU** चैनल की मेंबरशिप ली है!\n"
                f"मेंबरशिप लेने के लिए: https://youtube.com/@techuk7/join",
                ephemeral=True
            )

# ------------------------------------------------------------------------------
# VIP KEY CLAIM VIEW (#🔑-claim-mod-key)
# ------------------------------------------------------------------------------
class KeyClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="👑 Claim / Renew VIP Mod Key",
        style=discord.ButtonStyle.success,
        custom_id="claim_vip_mod_key_button",
        emoji="🔑"
    )
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ClaimKeyModal())

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
            except Exception as e:
                pass

        step1_success_msg = (
            "🎉 **सत्यापन सफल (Step 1 Complete)!**\n\n"
            "✅ आपका सर्वर अनलॉक हो चुका है!\n"
            "• `#🎁-free-mods` ➔ फ्री मोड्स और सॉफ्टवेयर डाउनलोड करें\n"
            "• `#general-chat` ➔ कम्युनिटी चैट में बातचीत करें\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 **STEP 2: VIP MODS & REAL LIFE RP ACCESS**\n"
            "अगर आप **TECH YOU YouTube Member** हैं, तो VIP Real Life RP Mod और Key अनलॉक करने के लिए `#🔑-claim-mod-key` में जाएं!"
        )
        await interaction.followup.send(step1_success_msg, ephemeral=True)

# ------------------------------------------------------------------------------
# ADMIN COMMAND: 1-CLICK CSV FILE UPLOAD & ACCOUNTANT SYNC
# ------------------------------------------------------------------------------
@bot.command(name="update_members", aliases=["import_members", "sync_csv"])
async def update_members(ctx):
    """Parses YouTube Studio CSV, updates 3 Tiers, and syncs Google Sheet"""
    # Permission check (Admin or Server Owner)
    if not (ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner):
        await ctx.send("⚠️ **Permission Denied:** यह कमांड केवल Sumit (Admin) के लिए है!")
        return

    if not ctx.message.attachments:
        await ctx.send(
            "⚠️ **CSV File Not Found!**\n\n"
            "👉 कृपया YouTube Studio से डाउनलोड की गई **Members CSV** फाइल को Discord में अटैच (अपलोड) करके लिखें:\n"
            "`!update_members`\n\n"
            "*(Accountant Bot अपने आप फाइल पढ़कर Google Sheet को 3 Tiers में व्यवस्थित कर देगा!)*"
        )
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.lower().endswith(".csv"):
        await ctx.send("❌ **गलत फाइल:** कृपया सिर्फ `.csv` फाइल अपलोड करें!")
        return

    status_msg = await ctx.send("⏳ **Accountant Bot:** YouTube Studio CSV फाइल को प्रोसेस किया जा रहा है...")

    try:
        content_bytes = await attachment.read()
        content_str = content_bytes.decode("utf-8-sig", errors="ignore")
        reader = csv.DictReader(io.StringIO(content_str))

        members_list = []
        for row in reader:
            member_name = row.get("Member", "").strip()
            profile_url = row.get("Link to profile", "").strip()
            tier = row.get("Current level", "").strip() or "⚡ Supporters ⚡"
            status_type = row.get("Last update", "").strip() or "Joined"
            months = row.get("Total time as member (months)", "1").strip()

            if member_name or profile_url:
                members_list.append({
                    "name": member_name,
                    "profile_url": profile_url,
                    "tier": tier,
                    "status_type": status_type,
                    "months": months
                })

        if not members_list:
            await status_msg.edit(content="❌ CSV फाइल में कोई मेंबर डेटा नहीं मिला!")
            return

        payload = {
            "action": "sync_csv",
            "secret": BOT_API_SECRET,
            "members": members_list
        }

        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: requests.post(WEB_APP_URL, json=payload, timeout=40))
        data = res.json()

        if data.get("status") == "SUCCESS":
            total = data.get("totalMembers", len(members_list))
            legends = data.get("tierLegends", 0)
            titans = data.get("tierTitans", 0)
            supporters = data.get("tierSupporters", 0)
            joined = data.get("newJoined", 0)
            rejoined = data.get("reJoined", 0)
            maintained = data.get("keysMaintained", 0)
            revoked = data.get("keysRevoked", 0)

            report_embed = discord.Embed(
                title="📊 TECH YOU ACCOUNTANT - MEMBERSHIP & TIER REPORT",
                description=(
                    f"✅ **Google Sheet 100% सिंक्रोनाइज़ और व्यवस्थित हो चुकी है!**\n\n"
                    f"👥 **कुल एक्टिव मेंबर्स (Total Members):** `{total}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏆 **3-TIER LIVE BREAKDOWN:**\n"
                    f"• 🥇 **⚡ Tech You Legends ⚡ :** `{legends}`\n"
                    f"• 🥈 **⚡ Titans ⚡          :** `{titans}`\n"
                    f"• 🥉 **⚡ Supporters ⚡      :** `{supporters}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📈 **GROWTH & ACTIVITY ANALYTICS:**\n"
                    f"• 🟢 **Fresh Joined (New) :** `{joined}`\n"
                    f"• 🔄 **Re-joined (Loyal)   :** `{rejoined}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔒 **SECURITY & LICENSE AUDIT:**\n"
                    f"• 🔑 **Active Keys In-Game :** `{maintained}`\n"
                    f"• 🛑 **Cancelled Members Revoked :** `{revoked}`\n"
                    f"*(जिन लोगों ने मेंबरशिप छोड़ी, उनका GTA 5 Mod तुरंत ब्लॉक कर दिया गया!)*"
                ),
                color=0x00ff88
            )
            report_embed.set_footer(text=f"Last Synced: {data.get('timestamp')}")
            await status_msg.edit(content=None, embed=report_embed)
        else:
            await status_msg.edit(content=f"❌ Sync Error: `{data.get('message', 'Unknown Error')}`")

    except Exception as e:
        await status_msg.edit(content=f"⚠️ **Accountant Processing Error:** `{str(e)}`")

# ------------------------------------------------------------------------------
# ADMIN COMMAND: LIVE 3-TIER STATS (!stats / !members)
# ------------------------------------------------------------------------------
@bot.command(name="stats", aliases=["members", "tiers"])
async def stats(ctx):
    """Displays real-time Tier counts and growth stats"""
    if not (ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner):
        await ctx.send("⚠️ **Permission Denied:** यह केवल Admin के लिए है!")
        return

    params = {"action": "get_stats", "secret": BOT_API_SECRET}
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: requests.get(WEB_APP_URL, params=params, timeout=15))
        d = res.json()
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching stats: `{e}`")
        return

    embed = discord.Embed(
        title="👑 TECH YOU - REAL-TIME MEMBERSHIP DASHBOARD",
        description=(
            f"👥 **Total Active Members:** `{d.get('totalMembers', 0)}`\n\n"
            f"🏆 **3-TIER STATUS:**\n"
            f"• 🥇 **⚡ Tech You Legends ⚡ :** `{d.get('tierLegends', 0)}`\n"
            f"• 🥈 **⚡ Titans ⚡          :** `{d.get('tierTitans', 0)}`\n"
            f"• 🥉 **⚡ Supporters ⚡      :** `{d.get('tierSupporters', 0)}`\n\n"
            f"📈 **GROWTH METRICS:**\n"
            f"• 🟢 Fresh Joined : `{d.get('newJoined', 0)}`\n"
            f"• 🔄 Re-joined     : `{d.get('reJoined', 0)}`\n\n"
            f"🔒 **IN-GAME LICENSES:**\n"
            f"• 🔑 Active In-Game : `{d.get('inGameActive', 0)}`\n"
            f"• 🛑 Revoked / Left : `{d.get('inGameRevoked', 0)}`"
        ),
        color=0x00e5ff
    )
    await ctx.send(embed=embed)

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
        print(f"Revoke response: {res.text}")
    except Exception as e:
        print(f"Revoke error: {e}")

# ------------------------------------------------------------------------------
# AUTOMATIC YOUTUBE VIDEO ALERT CHECKER (EVERY 2 MINUTES)
# ------------------------------------------------------------------------------
async def youtube_feed_checker():
    global g_last_posted_video_id
    await bot.wait_until_ready()
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
                                        break
        except Exception:
            pass
            
        await asyncio.sleep(120)

# ------------------------------------------------------------------------------
# ADMIN COMMANDS (!setup_verify, !setup_claim)
# ------------------------------------------------------------------------------
@bot.command(name="setup_verify")
async def setup_verify(ctx):
    if not (ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner):
        return
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

@bot.command(name="setup_claim")
async def setup_claim(ctx):
    if not (ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner):
        return
    embed = discord.Embed(
        title="👑 TECH YOU VIP - MOD ACTIVATION PANEL",
        description=(
            "हमारे सभी **YouTube Channel Members** के लिए एक्सक्लूसिव Real Life RP और कस्टम मोड्स का ऑफिशियल एक्टिवेशन हब!\n\n"
            "🏆 **3 Tiers Supported:**\n"
            "• ⚡ Tech You Legends ⚡\n"
            "• ⚡ Titans ⚡\n"
            "• ⚡ Supporters ⚡\n\n"
            "🔑 **अपनी VIP Mod Key प्राप्त / रीन्यू करने के लिए:**\n"
            "नीचे दिए गए **[👑 Claim / Renew VIP Mod Key]** बटन पर क्लिक करें और अपना YouTube Handle / Channel Link दर्ज करें।\n\n"
            "⚡ हमारा ऑटोमेटेड एकाउंटेंट आपकी मेंबरशिप वेरीफाई करके आपको 30-Day Key और डाउनलोड लिंक प्रदान करेगा!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "▶️ **मेंबरशिप जॉइन करें:** [Join YouTube Membership](https://youtube.com/@techuk7/join)\n"
            "🔒 **Strict Single-PC Policy:** 1 Member = 1 Key = 1 PC Binding (HWID Bound)."
        ),
        color=0x00ff88
    )
    await ctx.send(embed=embed, view=KeyClaimView())
    await ctx.message.delete()

# ------------------------------------------------------------------------------
# BOT ON_READY EVENT
# ------------------------------------------------------------------------------
@bot.event
async def on_ready():
    print("=" * 60, flush=True)
    print(f"TECH YOU MOD ACCOUNTANT ONLINE: {bot.user.name} (ID: {bot.user.id})", flush=True)
    print("=" * 60, flush=True)

    bot.add_view(KeyClaimView())
    bot.add_view(Sub2UnlockStep1View())

    if not hasattr(bot, "_yt_checker_started"):
        bot._yt_checker_started = True
        bot.loop.create_task(youtube_feed_checker())

    for guild in bot.guilds:
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
                            "🏆 **3 Tiers Supported:**\n"
                            "• ⚡ Tech You Legends ⚡\n"
                            "• ⚡ Titans ⚡\n"
                            "• ⚡ Supporters ⚡\n\n"
                            "🔑 **अपनी VIP Mod Key प्राप्त करने के लिए:**\n"
                            "नीचे दिए गए **[👑 Claim / Renew VIP Mod Key]** बटन पर क्लिक करें।\n\n"
                            "⚡ बॉट आपकी मेंबरशिप वेरीफाई करके आपको पर्सनल Activation Key और डायरेक्ट डाउनलोड लिंक प्रदान करेगा।\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "▶️ **मेंबरशिप जॉइन करें:** [Join YouTube Membership](https://youtube.com/@techuk7/join)\n"
                            "🔒 **Strict Single-PC Policy:** 1 Member = 1 Key = 1 PC Binding (HWID Bound)."
                        ),
                        color=0x00ff88
                    )
                    await ch.send(embed=embed, view=KeyClaimView())

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
