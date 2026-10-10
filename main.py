import discord
from discord.ext import commands
import os
import json
from datetime import datetime, timezone, timedelta
import asyncio
from flask import Flask, request, session
import threading

# ============================================================

# REMOTE WEB SERVER

# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get("WEB_SECRET_KEY", "change-this-secret")
WEB_PASSWORD = os.environ.get("WEB_PASSWORD", "change-this-password")

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        password = request.form.get("password")

        if password == WEB_PASSWORD:
            session["authenticated"] = True
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Remote Management</title>
            </head>
            <body>
                <h1>🔐 Remote Management</h1>
                <p>Login successful.</p>
                <a href="/panel">Continue to Panel →</a>
            </body>
            </html>
            """

        return "❌ Incorrect password. <a href='/'>Try again</a>"

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
    </head>
    <body>
        <h1>🔐 Remote Management</h1>

        <form method="POST">
            <input
                type="password"
                name="password"
                placeholder="Password"
                required
            >

            <button type="submit">
                🔓 Login
            </button>
        </form>
    </body>
    </html>
    """

@app.route("/panel")
def panel():
    if not session.get("authenticated"):
        return "❌ You must log in first. <a href='/'>Login</a>"

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Remote Management</title>
    </head>
    <body>
        <h1>🛠️ Remote Management</h1>

        <p>Enter a Discord User ID to remove their timeout.</p>

        <form method="POST" action="/untimeout">
            <input
                type="text"
                name="user_id"
                placeholder="Discord User ID"
                required
            >

            <button type="submit">
                🔓 Remove Timeout
            </button>
        </form>

        <br>

        <a href="/logout">🚪 Logout</a>
    </body>
    </html>
    """

@app.route("/logout")
def logout():
    session.clear()
    return "✅ Logged out. <a href='/'>Login again</a>"

@app.route("/untimeout", methods=["POST"])
def untimeout():
    if not session.get("authenticated"):
        return "❌ Unauthorized. <a href='/'>Login</a>"

    user_id = request.form.get("user_id")
    if not user_id:
        return "❌ No User ID provided."

    try:
        user_id = int(user_id)
    except:
        return "❌ Invalid User ID."

    member = None

    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if member:
            break

    if member is None:
        return "❌ User not found."

    future = asyncio.run_coroutine_threadsafe(
        member.timeout(
            None,
            reason="Remote Management Panel"
        ),
        bot.loop
    )

    try:
        future.result(timeout=10)
    except discord.Forbidden:
        return "❌ I don't have permission to remove this timeout."
    except Exception as e:
        return f"❌ Failed to remove timeout: {e}"

    return f"✅ Timeout removed from {member.display_name}!"
    
def run_web_server():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_web_server, daemon=True).start()
# ============================================================
# SETTINGS
# ============================================================

MANAGEMENT_ROLE_ID = 1555011189187027004
STAFF_TEAM_ROLE_ID = 1556077373781315655

STRIKE_I_ROLE_ID = 1541528707414364161
STRIKE_II_ROLE_ID = 1541528755283959890
STRIKE_III_ROLE_ID = 1541528758706770042
SUSPENDED_ROLE_ID = 1541528855062380614

SESSION_PING_ROLE_ID = 1557521800265474171
SESSION_CHANNEL_ID = 1556113127404208138
INFRACTION_LOG_CHANNEL_ID = 1557517735225860107
STAFF_FEEDBACK_CHANNEL_ID = 1556763072503222312
LOA_CHANNEL_ID = 1556763150529855599

SESSION_CODE = "THBR"

# Rainbow command role
RAINBOW_ROLE_ID = 1555015805685727312

# ============================================================
# PERSISTENT RAILWAY VOLUME
# ============================================================

DATA_DIRECTORY = "/app/data"
DATA_FILE = "/app/data/staff_hours.json"
RESTORE_BACKUP_FILE = "/app/data/staff_hours_before_restore.json"

# NEW: SAY BLACKLIST FILE
SAY_BLACKLIST_FILE = "/app/data/say_blacklist.json"

# NO PING SYSTEM FILE
NO_PING_FILE = "/app/data/no_ping.json"
NO_PING_TIMEOUT_MINUTES = 10

os.makedirs(DATA_DIRECTORY, exist_ok=False)

# ============================================================
# DISCORD SETUP
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=";",
    intents=intents
)

# ============================================================
# SSU VOTES
# ============================================================

ssu_votes = {}

# ============================================================
# SAY BLACKLIST
# ============================================================

def load_say_blacklist():

    if not os.path.exists(SAY_BLACKLIST_FILE):
        return set()

    try:

        with open(
            SAY_BLACKLIST_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, list):
            return set()

        return set(
            str(user_id)
            for user_id in data
        )

    except Exception as e:

        print(
            f"Could not load say blacklist: {e}"
        )

        return set()


def save_say_blacklist():

    try:

        with open(
            SAY_BLACKLIST_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                list(say_blacklist),
                file,
                indent=4
            )

        return True

    except Exception as e:

        print(
            f"Could not save say blacklist: {e}"
        )

        return False


say_blacklist = load_say_blacklist()

# ============================================================
# NO PING SYSTEM
# ============================================================

def load_no_ping_data():

    if not os.path.exists(NO_PING_FILE):
        return {
            "enabled_users": [],
            "violations": {}
        }

    try:

        with open(
            NO_PING_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            return {
                "enabled_users": [],
                "violations": {}
            }

        data.setdefault(
            "enabled_users",
            []
        )
        data.setdefault(
            "violations",
            {}
        )

        return data

    except Exception as e:

        print(
            f"Could not load no-ping data: {e}"
        )

        return {
            "enabled_users": [],
            "violations": {}
        }


def save_no_ping_data():

    try:

        with open(
            NO_PING_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                no_ping_data,
                file,
                indent=4
            )

        return True

    except Exception as e:

        print(
            f"Could not save no-ping data: {e}"
        )

        return False


no_ping_data = load_no_ping_data()

# ============================================================
# DATA
# ============================================================

def default_data():
    return {
        "weekly_hours": {},
        "clocked_in": {},
        "staff_hub": {}
    }


def load_data():

    if not os.path.exists(DATA_FILE):
        return default_data()

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            print(
                "WARNING: staff_hours.json is invalid."
            )

            return default_data()

        data.setdefault(
            "weekly_hours",
            {}
        )

        data.setdefault(
            "clocked_in",
            {}
        )

        data.setdefault(
            "staff_hub",
            {}
        )

        return data

    except json.JSONDecodeError:

        print(
            "ERROR: staff_hours.json contains invalid JSON."
        )

        return default_data()

    except Exception as e:

        print(
            f"Could not load data: {e}"
        )

        return default_data()


def save_data():

    try:

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                staff_data,
                file,
                indent=4
            )

        return True

    except Exception as e:

        print(
            f"Could not save data: {e}"
        )

        return False


staff_data = load_data()

# ============================================================
# PERMISSIONS
# ============================================================

def is_management(member):

    return any(
        role.id == MANAGEMENT_ROLE_ID
        for role in member.roles
    )


async def is_staff(member):

    try:

        fresh_member = await member.guild.fetch_member(
            member.id
        )

        return any(
            role.id == STAFF_TEAM_ROLE_ID
            for role in fresh_member.roles
        )

    except Exception as e:

        print(
            f"Staff role check failed: {e}"
        )

        return any(
            role.id == STAFF_TEAM_ROLE_ID
            for role in member.roles
        )

# ============================================================
# TIME HELPERS
# ============================================================

def format_duration(seconds):

    seconds = max(
        0,
        int(seconds)
    )

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return (
        f"{hours}h "
        f"{minutes:02d}m "
        f"{secs:02d}s"
    )


def get_current_shift_seconds(user_id):

    user_id = str(user_id)

    if user_id not in staff_data["clocked_in"]:
        return 0

    try:

        start = datetime.fromisoformat(
            staff_data["clocked_in"][user_id]
        )

        now = datetime.now(
            timezone.utc
        )

        return max(
            0,
            int(
                (now - start).total_seconds()
            )
        )

    except Exception:

        return 0


def get_weekly_seconds(user_id):

    return int(
        staff_data["weekly_hours"].get(
            str(user_id),
            0
        )
    )


def get_total_current_week_seconds(user_id):

    return (
        get_weekly_seconds(user_id)
        + get_current_shift_seconds(user_id)
    )

# ============================================================
# STAFF HUB EMBED
# ============================================================

def create_staff_hub_embed(guild):

    embed = discord.Embed(
        title="🛠️ Staff Hub",
        description=(
            "Welcome to the Staff Hub.\n\n"
            "Use the buttons below to manage your duty status."
        ),
        color=discord.Color.blurple()
    )

    on_duty = []

    for user_id in staff_data["clocked_in"]:

        member = guild.get_member(
            int(user_id)
        )

        if member is None:
            continue

        duration = get_current_shift_seconds(
            user_id
        )

        on_duty.append(
            f"🟢 {member.mention} — "
            f"**{format_duration(duration)}**"
        )

    if on_duty:

        duty_text = "\n".join(
            on_duty
        )

    else:

        duty_text = (
            "Nobody is currently on duty."
        )

    embed.add_field(
        name="👥 Currently On Duty",
        value=duty_text,
        inline=False
    )

    embed.add_field(
        name="📋 Weekly Requirement",
        value="**1h 00m 00s** per week",
        inline=False
    )

    embed.set_footer(
        text=(
            "Staff Team • "
            "Use ;weekly to view weekly hours"
        )
    )

    return embed


async def update_staff_hub(guild):

    hub_info = staff_data.get(
        "staff_hub",
        {}
    )

    channel_id = hub_info.get(
        "channel_id"
    )

    message_id = hub_info.get(
        "message_id"
    )

    if not channel_id or not message_id:
        return

    channel = guild.get_channel(
        int(channel_id)
    )

    if channel is None:
        return

    try:

        message = await channel.fetch_message(
            int(message_id)
        )

        await message.edit(
            embed=create_staff_hub_embed(
                guild
            ),
            view=StaffHubView()
        )

    except Exception as e:

        print(
            f"Could not update Staff Hub: {e}"
        )

# ============================================================
# STAFF TEAM BOLO SYSTEM
# ============================================================

BOLO_CHANNEL_ID = 1557903468629463061
BOLO_ADMIN_ROLE_ID = 1555015217774202950


class StaffBoloModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(
            title="🚨 Staff Team BOLO"
        )

        self.roblox_username = discord.ui.TextInput(
            label="Roblox Username",
            placeholder="Enter the Roblox username",
            required=True,
            max_length=50
        )

        self.reason = discord.ui.TextInput(
            label="Reason for BOLO",
            placeholder="Explain why this user should be banned",
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )

        self.add_item(self.roblox_username)
        self.add_item(self.reason)

    async def on_submit(self, interaction):

        if not await is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )
            return

        channel = interaction.guild.get_channel(
            BOLO_CHANNEL_ID
        )

        if channel is None:
            await interaction.response.send_message(
                "❌ I couldn't find the BOLO channel.",
                ephemeral=True
            )
            return

        timestamp = int(
            datetime.now(timezone.utc).timestamp()
        )

        embed = discord.Embed(
            title="🚨 STAFF TEAM BOLO",
            description=(
                "A Staff Team member has requested a ban "
                "for the following user."
            ),
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="🎮 Roblox Username",
            value=f"`{self.roblox_username.value}`",
            inline=False
        )

        embed.add_field(
            name="📝 Reason",
            value=self.reason.value,
            inline=False
        )

        embed.add_field(
            name="👤 Requested By",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="📊 Status",
            value="🟠 **Pending Admin Review**",
            inline=False
        )

        embed.add_field(
            name="🕒 Submitted",
            value=f"<t:{timestamp}:F>",
            inline=False
        )

        embed.set_footer(
            text="Staff Team BOLO • Awaiting Admin decision"
        )

        try:
            await channel.send(
                embed=embed,
                view=StaffBoloDecisionView()
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages "
                "in the BOLO channel.",
                ephemeral=True
            )
            return

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to submit the BOLO:\n```text\n{e}\n```",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "✅ **BOLO Submitted**\n\n"
            "Your ban request has been sent to the Admin Team "
            "for review.",
            ephemeral=True
        )


class StaffBoloDecisionView(discord.ui.View):

    def __init__(self):
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.danger,
        emoji="🔨",
        custom_id="staff_bolo_accept"
    )
    async def accept(
        self,
        interaction,
        button
    ):

        if not any(
            role.id == BOLO_ADMIN_ROLE_ID
            for role in interaction.user.roles
        ):
            await interaction.response.send_message(
                "❌ You must be an Admin to accept or deny BOLOs.",
                ephemeral=True
            )
            return

        embed = interaction.message.embeds[0]

        # Change status field
        for index, field in enumerate(embed.fields):

            if field.name == "📊 Status":

                embed.set_field_at(
                    index,
                    name="📊 Status",
                    value=(
                        f"🟢 **BOLO ACCEPTED**\n"
                        f"Accepted by {interaction.user.mention}"
                    ),
                    inline=False
                )

                break

        embed.color = discord.Color.green()

        embed.set_footer(
            text="Staff Team BOLO • Accepted"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.secondary,
        emoji="❌",
        custom_id="staff_bolo_deny"
    )
    async def deny(
        self,
        interaction,
        button
    ):

        if not any(
            role.id == BOLO_ADMIN_ROLE_ID
            for role in interaction.user.roles
        ):
            await interaction.response.send_message(
                "❌ You must be an Admin to accept or deny BOLOs.",
                ephemeral=True
            )
            return

        embed = interaction.message.embeds[0]

        for index, field in enumerate(embed.fields):

            if field.name == "📊 Status":

                embed.set_field_at(
                    index,
                    name="📊 Status",
                    value=(
                        f"🔴 **BOLO DENIED**\n"
                        f"Denied by {interaction.user.mention}"
                    ),
                    inline=False
                )

                break

        embed.color = discord.Color.red()

        embed.set_footer(
            text="Staff Team BOLO • Denied"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

# ============================================================
# STAFF HUB VIEW
# ============================================================

class StaffHubView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Clock In",
        style=discord.ButtonStyle.success,
        emoji="🟢",
        custom_id="staffhub_clockin"
    )
    async def clock_in(
        self,
        interaction,
        button
    ):

        if not await is_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )

            return

        user_id = str(
            interaction.user.id
        )

        if user_id in staff_data["clocked_in"]:

            current_shift = get_current_shift_seconds(
                user_id
            )

            await interaction.response.send_message(
                "⚠️ You are already clocked in.\n\n"
                f"**Current Shift:** "
                f"{format_duration(current_shift)}",
                ephemeral=True
            )

            return

        staff_data["clocked_in"][user_id] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        save_data()

        await interaction.response.send_message(
            "🟢 **Clocked In**\n\n"
            "You are now officially on duty.",
            ephemeral=True
        )

        await update_staff_hub(
            interaction.guild
        )

    @discord.ui.button(
        label="Clock Out",
        style=discord.ButtonStyle.danger,
        emoji="🔴",
        custom_id="staffhub_clockout"
    )
    async def clock_out(
        self,
        interaction,
        button
    ):

        if not await is_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )

            return

        user_id = str(
            interaction.user.id
        )

        if user_id not in staff_data["clocked_in"]:

            await interaction.response.send_message(
                "⚠️ You are not currently clocked in.",
                ephemeral=True
            )

            return

        shift_seconds = get_current_shift_seconds(
            user_id
        )

        old_weekly = get_weekly_seconds(
            user_id
        )

        new_weekly = (
            old_weekly
            + shift_seconds
        )

        staff_data["weekly_hours"][
            user_id
        ] = new_weekly

        del staff_data["clocked_in"][
            user_id
        ]

        save_data()

        await interaction.response.send_message(
            "🔴 **Clocked Out**\n\n"
            f"**Shift:** "
            f"{format_duration(shift_seconds)}\n"
            f"**Weekly Total:** "
            f"{format_duration(new_weekly)}",
            ephemeral=True
        )

        await update_staff_hub(
            interaction.guild
        )

    @discord.ui.button(
        label="Verbal Warn",
        style=discord.ButtonStyle.secondary,
        emoji="🗣️",
        row=1
    )
    async def verbal_warn(self, interaction, button):

        if not await is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            StaffInfractionModal(
                "Verbal Warning",
                "🗣️"
            )
        )

    @discord.ui.button(
        label="Warn",
        style=discord.ButtonStyle.danger,
        emoji="⚠️",
        row=1
    )
    async def warn(self, interaction, button):

        if not await is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            StaffInfractionModal(
                "Warning",
                "⚠️"
            )
        )

    @discord.ui.button(
        label="Kick",
        style=discord.ButtonStyle.danger,
        emoji="👢",
        row=1
    )
    async def kick(self, interaction, button):

        if not await is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            StaffInfractionModal(
                "Kick",
                "👢"
            )
        )

    @discord.ui.button(
        label="Ban",
        style=discord.ButtonStyle.danger,
        emoji="🔨",
        row=1
    )
    async def ban(self, interaction, button):

        if not await is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            StaffInfractionModal(
                "Ban",
                "🔨"
            )
        )

    @discord.ui.button(
        label="Staff BOLO",
        style=discord.ButtonStyle.primary,
        emoji="🚨",
        row=2
    )
    async def staff_bolo(
        self,
        interaction,
        button
    ):

        if not await is_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            StaffBoloModal()
        )

    @discord.ui.button(
        label="Staff Feedback",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        row=2
    )
    async def staff_feedback(
        self,
        interaction,
        button
    ):

        if not await is_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            StaffFeedbackModal()
        )

    @discord.ui.button(
        label="Refresh",
        style=discord.ButtonStyle.secondary,
        emoji="🔄",
        custom_id="staffhub_refresh"
    )
    async def refresh(
        self,
        interaction,
        button
    ):

        if not await is_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            embed=create_staff_hub_embed(
                interaction.guild
            ),
            view=StaffHubView()
        )

    @discord.ui.button(
        label="Request LOA",
        style=discord.ButtonStyle.primary,
        emoji="🏖️",
        row=2
    )
    async def request_loa(
        self,
        interaction,
        button
    ):

        if not await is_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            LOAModal()
        )

# ============================================================
# LOA SYSTEM
# ============================================================

class LOAModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="🏖️ Staff LOA Request"
        )

        self.start_date = discord.ui.TextInput(
            label="Start Date",
            placeholder="MM/DD/YYYY",
            required=True,
            max_length=10
        )

        self.end_date = discord.ui.TextInput(
            label="End Date",
            placeholder="MM/DD/YYYY",
            required=True,
            max_length=10
        )

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Why do you need an LOA?",
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )

        self.add_item(self.start_date)
        self.add_item(self.end_date)
        self.add_item(self.reason)

    async def on_submit(self, interaction):

        if not await is_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )

            return

        try:

            start = datetime.strptime(
                self.start_date.value,
                "%m/%d/%Y"
            )

            end = datetime.strptime(
                self.end_date.value,
                "%m/%d/%Y"
            )

            if end < start:

                await interaction.response.send_message(
                    "❌ The end date cannot be before the start date.",
                    ephemeral=True
                )

                return

        except ValueError:

            await interaction.response.send_message(
                "❌ Please use the date format **MM/DD/YYYY**.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            LOA_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ I couldn't find the LOA channel.",
                ephemeral=True
            )

            return

        timestamp = int(
            datetime.now(
                timezone.utc
            ).timestamp()
        )

        embed = discord.Embed(
            title="🏖️ Staff LOA Request",
            description="A staff member has submitted an LOA request.",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="👤 Staff Member",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="📅 Start Date",
            value=self.start_date.value,
            inline=True
        )

        embed.add_field(
            name="📅 End Date",
            value=self.end_date.value,
            inline=True
        )

        embed.add_field(
            name="📝 Reason",
            value=self.reason.value,
            inline=False
        )

        embed.add_field(
            name="📊 Status",
            value="🟡 **Pending Approval**",
            inline=False
        )

        embed.add_field(
            name="🕒 Submitted",
            value=f"<t:{timestamp}:F>",
            inline=False
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        try:

            await channel.send(
                embed=embed,
                view=LOAView(
                    interaction.user.id,
                    self.start_date.value,
                    self.end_date.value
                )
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I don't have permission to send messages in the LOA channel.",
                ephemeral=True
            )

            return

        except Exception as e:

            await interaction.response.send_message(
                f"❌ Failed to submit LOA: `{e}`",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ **LOA request submitted!**\n\n"
            "Management will review your request.",
            ephemeral=True
        )


# ============================================================
# LOA MANAGEMENT VIEW
# ============================================================

class LOAView(discord.ui.View):

    def __init__(
        self,
        staff_member_id,
        start_date,
        end_date
    ):

        super().__init__(
            timeout=None
        )

        self.staff_member_id = staff_member_id
        self.start_date = start_date
        self.end_date = end_date

    def is_management(self, member):

        return is_management(member)

    @discord.ui.button(
        label="Approve",
        style=discord.ButtonStyle.success,
        emoji="🟢"
    )
    async def approve(
        self,
        interaction,
        button
    ):

        if not self.is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Management+ only.",
                ephemeral=True
            )

            return

        # Acknowledge the interaction immediately
        await interaction.response.defer(
            ephemeral=True
        )

        embed = interaction.message.embeds[0]

        # Make sure this is still pending
        if len(embed.fields) <= 4 or "Pending" not in embed.fields[4].value:

            await interaction.followup.send(
                "❌ This LOA has already been processed.",
                ephemeral=True
            )

            return

        embed.set_field_at(
            4,
            name="📊 Status",
            value="🟢 **APPROVED**",
            inline=False
        )

        embed.add_field(
            name="✅ Approved By",
            value=interaction.user.mention,
            inline=False
        )

        # Only keep End LOA Early visible
        new_view = discord.ui.View(
            timeout=None
        )

        new_view.add_item(
            EndLOAEarlyButton(
                self.staff_member_id,
                self.start_date,
                self.end_date
            )
        )

        await interaction.message.edit(
            embed=embed,
            view=new_view
        )

        try:

            member = interaction.guild.get_member(
                self.staff_member_id
            )

            if member:

                await member.send(
                    "🏖️ **LOA Approved**\n\n"
                    f"Your LOA request from **{self.start_date}** "
                    f"to **{self.end_date}** has been approved by "
                    f"{interaction.user.mention}."
                )

        except Exception:

            pass

        await interaction.followup.send(
            "✅ LOA approved.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.danger,
        emoji="🔴"
    )
    async def deny(
        self,
        interaction,
        button
    ):

        if not self.is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Management+ only.",
                ephemeral=True
            )

            return

        # Acknowledge the interaction immediately
        await interaction.response.defer(
            ephemeral=True
        )

        embed = interaction.message.embeds[0]

        # Make sure this is still pending
        if len(embed.fields) <= 4 or "Pending" not in embed.fields[4].value:

            await interaction.followup.send(
                "❌ This LOA has already been processed.",
                ephemeral=True
            )

            return

        embed.set_field_at(
            4,
            name="📊 Status",
            value="🔴 **DENIED**",
            inline=False
        )

        embed.add_field(
            name="❌ Denied By",
            value=interaction.user.mention,
            inline=False
        )

        # Remove ALL buttons
        await interaction.message.edit(
            embed=embed,
            view=None
        )

        try:

            member = interaction.guild.get_member(
                self.staff_member_id
            )

            if member:

                await member.send(
                    "🏖️ **LOA Denied**\n\n"
                    f"Your LOA request from **{self.start_date}** "
                    f"to **{self.end_date}** has been denied by "
                    f"{interaction.user.mention}."
                )

        except Exception:

            pass

        await interaction.followup.send(
            "❌ LOA denied.",
            ephemeral=True
        )


# ============================================================
# END LOA EARLY BUTTON
# ============================================================

class EndLOAEarlyButton(
    discord.ui.Button
):

    def __init__(
        self,
        staff_member_id,
        start_date,
        end_date
    ):

        super().__init__(
            label="End LOA Early",
            style=discord.ButtonStyle.secondary,
            emoji="⏹️"
        )

        self.staff_member_id = staff_member_id
        self.start_date = start_date
        self.end_date = end_date

    async def callback(
        self,
        interaction
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Management+ only.",
                ephemeral=True
            )

            return

        # Acknowledge the interaction immediately
        await interaction.response.defer(
            ephemeral=True
        )

        embed = interaction.message.embeds[0]

        # Make sure LOA is still approved
        if len(embed.fields) <= 4 or "APPROVED" not in embed.fields[4].value:

            await interaction.followup.send(
                "❌ This LOA is no longer active.",
                ephemeral=True
            )

            return

        timestamp = int(
            datetime.now(
                timezone.utc
            ).timestamp()
        )

        embed.set_field_at(
            4,
            name="📊 Status",
            value="⏹️ **ENDED EARLY**",
            inline=False
        )

        embed.add_field(
            name="⏹️ Ended By",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="🕒 Ended",
            value=f"<t:{timestamp}:F>",
            inline=False
        )

        # Remove button completely
        await interaction.message.edit(
            embed=embed,
            view=None
        )

        try:

            member = interaction.guild.get_member(
                self.staff_member_id
            )

            if member:

                await member.send(
                    "⏹️ **LOA Ended Early**\n\n"
                    f"Your LOA has been ended early by "
                    f"{interaction.user.mention}."
                )

        except Exception:

            pass

        await interaction.followup.send(
            "⏹️ LOA ended early.",
            ephemeral=True
        )


# ============================================================
# STAFF HUB INFRACTION MODAL
# ============================================================

class StaffInfractionModal(discord.ui.Modal):

    def __init__(self, action_name, action_emoji):
        super().__init__(
            title=f"{action_emoji} {action_name}"
        )

        self.action_name = action_name
        self.action_emoji = action_emoji

        self.roblox_username = discord.ui.TextInput(
            label="Roblox Username",
            placeholder="Enter the Roblox username",
            required=True,
            max_length=50
        )

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Enter the reason",
            required=True,
            max_length=500,
            style=discord.TextStyle.paragraph
        )

        self.add_item(self.roblox_username)
        self.add_item(self.reason)

    async def on_submit(self, interaction):

        if not await is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )
            return

        channel = interaction.guild.get_channel(
            INFRACTION_LOG_CHANNEL_ID
        )

        if channel is None:
            await interaction.response.send_message(
                "❌ I couldn't find the infraction logs channel.",
                ephemeral=True
            )
            return

        timestamp = int(datetime.now(timezone.utc).timestamp())

        embed = discord.Embed(
            title=f"{self.action_emoji} {self.action_name}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="🎮 Roblox Username",
            value=f"`{self.roblox_username.value}`",
            inline=False
        )

        embed.add_field(
            name="📝 Reason",
            value=self.reason.value,
            inline=False
        )

        embed.add_field(
            name="👤 Issued By",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="🕒 Timestamp",
            value=f"<t:{timestamp}:F>",
            inline=False
        )

        try:
            await channel.send(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in the logs channel.",
                ephemeral=True
            )
            return

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to send the log: `{e}`",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ **{self.action_name}** logged successfully.",
            ephemeral=True
        )


# ============================================================
# STAFF FEEDBACK MODAL
# ============================================================

class StaffFeedbackModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="📝 Staff Feedback"
        )

        self.staff_member = discord.ui.TextInput(
            label="Staff Member",
            placeholder="Enter the staff member's Discord username",
            required=True,
            max_length=100
        )

        self.rating = discord.ui.TextInput(
            label="Rating",
            placeholder="1-5",
            required=True,
            max_length=1
        )

        self.feedback = discord.ui.TextInput(
            label="Feedback",
            placeholder="Tell Management your feedback...",
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )

        self.suggestions = discord.ui.TextInput(
            label="Suggestions",
            placeholder="Anything you'd like to see improved?",
            required=False,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )

        self.add_item(self.staff_member)
        self.add_item(self.rating)
        self.add_item(self.feedback)
        self.add_item(self.suggestions)

    async def on_submit(self, interaction):

        if not await is_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You must be a member of the Staff Team.",
                ephemeral=True
            )

            return

        try:

            rating = int(
                self.rating.value
            )

            if rating < 1 or rating > 5:

                raise ValueError

        except ValueError:

            await interaction.response.send_message(
                "❌ Rating must be a number from **1-5**.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            STAFF_FEEDBACK_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ I couldn't find the Staff Feedback channel.",
                ephemeral=True
            )

            return

        timestamp = int(
            datetime.now(
                timezone.utc
            ).timestamp()
        )

        stars = "⭐" * rating

        embed = discord.Embed(
            title="📝 Staff Feedback",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="👤 Staff Member",
            value=self.staff_member.value,
            inline=False
        )

        embed.add_field(
            name="📨 Submitted By",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="⭐ Rating",
            value=f"{stars} **({rating}/5)**",
            inline=False
        )

        embed.add_field(
            name="📝 Feedback",
            value=self.feedback.value,
            inline=False
        )

        embed.add_field(
            name="💡 Suggestions",
            value=(
                self.suggestions.value
                if self.suggestions.value
                else "No suggestions provided."
            ),
            inline=False
        )

        embed.add_field(
            name="🕒 Timestamp",
            value=f"<t:{timestamp}:F>",
            inline=False
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        try:

            await channel.send(
                embed=embed
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I don't have permission to send feedback to that channel.",
                ephemeral=True
            )

            return

        except Exception as e:

            await interaction.response.send_message(
                f"❌ Failed to submit feedback: `{e}`",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ **Feedback submitted!**\n\n"
            "Thank you for providing feedback to Management.",
            ephemeral=True
        )


# ============================================================
# ;STAFFHUB
# ============================================================

@bot.command()
async def staffhub(ctx):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ You must be Management+ "
            "to send the Staff Hub."
        )

        return

    message = await ctx.send(
        embed=create_staff_hub_embed(
            ctx.guild
        ),
        view=StaffHubView()
    )

    staff_data["staff_hub"] = {
        "channel_id": str(
            ctx.channel.id
        ),
        "message_id": str(
            message.id
        )
    }

    save_data()

# ============================================================
# ;CLOCKIN
# ============================================================

@bot.command()
async def clockin(ctx):

    if not await is_staff(
        ctx.author
    ):

        await ctx.send(
            "❌ You must be a member of the Staff Team."
        )

        return

    user_id = str(
        ctx.author.id
    )

    if user_id in staff_data["clocked_in"]:

        current_shift = get_current_shift_seconds(
            user_id
        )

        await ctx.send(
            "⚠️ You are already clocked in.\n\n"
            f"**Current Shift:** "
            f"{format_duration(current_shift)}"
        )

        return

    staff_data["clocked_in"][user_id] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    save_data()

    await ctx.send(
        "🟢 **Clocked In**\n\n"
        "You are now officially on duty."
    )

    await update_staff_hub(
        ctx.guild
    )

# ============================================================
# ;CLOCKOUT
# ============================================================

@bot.command()
async def clockout(ctx):

    if not await is_staff(
        ctx.author
    ):

        await ctx.send(
            "❌ You must be a member of the Staff Team."
        )

        return

    user_id = str(
        ctx.author.id
    )

    if user_id not in staff_data["clocked_in"]:

        await ctx.send(
            "⚠️ You are not currently clocked in."
        )

        return

    shift_seconds = get_current_shift_seconds(
        user_id
    )

    old_weekly = get_weekly_seconds(
        user_id
    )

    new_weekly = (
        old_weekly
        + shift_seconds
    )

    staff_data["weekly_hours"][
        user_id
    ] = new_weekly

    del staff_data["clocked_in"][
        user_id
    ]

    save_data()

    await ctx.send(
        "🔴 **Clocked Out**\n\n"
        f"**Shift:** "
        f"{format_duration(shift_seconds)}\n"
        f"**Weekly Total:** "
        f"{format_duration(new_weekly)}"
    )

    await update_staff_hub(
        ctx.guild
    )

# ============================================================
# ;OD
# ============================================================

@bot.command()
async def od(ctx):

    if not await is_staff(
        ctx.author
    ):

        await ctx.send(
            "❌ You must be a member of the Staff Team."
        )

        return

    lines = []

    for user_id in staff_data["clocked_in"]:

        member = ctx.guild.get_member(
            int(user_id)
        )

        if member is None:
            continue

        duration = get_current_shift_seconds(
            user_id
        )

        lines.append(
            f"🟢 {member.mention} — "
            f"**{format_duration(duration)}**"
        )

    embed = discord.Embed(
        title="🟢 Currently On Duty",
        color=discord.Color.green()
    )

    if lines:

        embed.description = (
            "Staff members currently on duty:"
        )

        embed.add_field(
            name="👥 Staff",
            value="\n".join(lines),
            inline=False
        )

    else:

        embed.description = (
            "No staff members are currently on duty."
        )

    await ctx.send(
        embed=embed
    )

# ============================================================
# ;WEEKLY
# ============================================================

@bot.command()
async def weekly(ctx):

    if not await is_staff(
        ctx.author
    ):

        await ctx.send(
            "❌ You must be a member of the Staff Team."
        )

        return

    embed = discord.Embed(
        title="📊 Weekly Staff Hours",
        description="**Weekly Requirement: 1h 00m 00s**",
        color=discord.Color.blurple()
    )

    staff_members = []

    # Use cached roles instead of fetching every member
    # individually. This makes ;weekly much faster.
    for member in ctx.guild.members:

        if any(
            role.id == STAFF_TEAM_ROLE_ID
            for role in member.roles
        ):

            staff_members.append(
                member
            )

    staff_members.sort(
        key=lambda member:
        get_total_current_week_seconds(
            member.id
        ),
        reverse=True
    )

    lines = []

    for member in staff_members:

        total = get_total_current_week_seconds(
            member.id
        )

        status = (
            "🟢"
            if total >= 3600
            else "🔴"
        )

        lines.append(
            f"{status} {member.mention} — "
            f"**{format_duration(total)}**"
        )

    if lines:

        hours_text = "\n".join(
            lines
        )

    else:

        hours_text = (
            "No Staff Team members found."
        )

    embed.add_field(
        name="👥 Staff Hours",
        value=hours_text,
        inline=False
    )

    embed.set_footer(
        text=(
            "🟢 Requirement met • "
            "🔴 Below requirement"
        )
    )

    await ctx.send(
        embed=embed
    )

# ============================================================
# SHIFT ADMIN VIEW
# ============================================================

class ShiftAdminView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Add Time",
        style=discord.ButtonStyle.success,
        emoji="➕"
    )
    async def add_time(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Management+ only.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            ShiftTimeModal("add")
        )

    @discord.ui.button(
        label="Remove Time",
        style=discord.ButtonStyle.danger,
        emoji="➖"
    )
    async def remove_time(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Management+ only.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            ShiftTimeModal("remove")
        )

    @discord.ui.button(
        label="Force Clock In",
        style=discord.ButtonStyle.success,
        emoji="🟢",
        row=1
    )
    async def force_clock_in(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Management+ only.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            ShiftUserModal("clockin")
        )

    @discord.ui.button(
        label="Force Clock Out",
        style=discord.ButtonStyle.danger,
        emoji="🔴",
        row=1
    )
    async def force_clock_out(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Management+ only.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            ShiftUserModal("clockout")
        )

# ============================================================
# SHIFT TIME MODAL
# ============================================================

class ShiftTimeModal(discord.ui.Modal):

    def __init__(
        self,
        action
    ):

        self.action = action

        title = (
            "➕ Add Time"
            if action == "add"
            else "➖ Remove Time"
        )

        super().__init__(
            title=title
        )

        self.user_id = discord.ui.TextInput(
            label="User ID",
            placeholder="Discord User ID",
            required=True
        )

        self.amount = discord.ui.TextInput(
            label="Amount",
            placeholder=(
                "Examples: 30m, 1h, "
                "1h 30m, 45s"
            ),
            required=True
        )

        self.add_item(
            self.user_id
        )

        self.add_item(
            self.amount
        )

    async def on_submit(
        self,
        interaction
    ):

        try:

            user_id = int(
                self.user_id.value
            )

        except:

            await interaction.response.send_message(
                "❌ Invalid User ID.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            user_id
        )

        if member is None:

            await interaction.response.send_message(
                "❌ User not found in this server.",
                ephemeral=True
            )

            return

        seconds = parse_duration(
            self.amount.value
        )

        if seconds is None or seconds <= 0:

            await interaction.response.send_message(
                "❌ Invalid time format.",
                ephemeral=True
            )

            return

        current = get_weekly_seconds(
            user_id
        )

        if self.action == "add":

            new_total = (
                current
                + seconds
            )

        else:

            new_total = max(
                0,
                current - seconds
            )

        staff_data["weekly_hours"][
            str(user_id)
        ] = new_total

        save_data()

        await interaction.response.send_message(
            "✅ **Shift Updated**\n\n"
            f"**User:** {member.mention}\n"
            f"**Amount:** "
            f"{format_duration(seconds)}\n"
            f"**New Total:** "
            f"{format_duration(new_total)}",
            ephemeral=True
        )

        await update_staff_hub(
            interaction.guild
        )

# ============================================================
# SHIFT USER MODAL
# ============================================================

class ShiftUserModal(discord.ui.Modal):

    def __init__(
        self,
        action
    ):

        self.action = action

        title = (
            "🟢 Force Clock In"
            if action == "clockin"
            else "🔴 Force Clock Out"
        )

        super().__init__(
            title=title
        )

        self.user_id = discord.ui.TextInput(
            label="User ID",
            placeholder="Discord User ID",
            required=True
        )

        self.add_item(
            self.user_id
        )

    async def on_submit(
        self,
        interaction
    ):

        try:

            user_id = int(
                self.user_id.value
            )

        except:

            await interaction.response.send_message(
                "❌ Invalid User ID.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            user_id
        )

        if member is None:

            await interaction.response.send_message(
                "❌ User not found in this server.",
                ephemeral=True
            )

            return

        user_id = str(
            user_id
        )

        if self.action == "clockin":

            if user_id in staff_data["clocked_in"]:

                await interaction.response.send_message(
                    "⚠️ That user is already clocked in.",
                    ephemeral=True
                )

                return

            staff_data["clocked_in"][
                user_id
            ] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            save_data()

            await interaction.response.send_message(
                f"🟢 {member.mention} "
                "has been force clocked in.",
                ephemeral=True
            )

        else:

            if user_id not in staff_data["clocked_in"]:

                await interaction.response.send_message(
                    "⚠️ That user is not currently clocked in.",
                    ephemeral=True
                )

                return

            shift_seconds = get_current_shift_seconds(
                user_id
            )

            new_total = (
                get_weekly_seconds(
                    user_id
                )
                + shift_seconds
            )

            staff_data["weekly_hours"][
                user_id
            ] = new_total

            del staff_data["clocked_in"][
                user_id
            ]

            save_data()

            await interaction.response.send_message(
                f"🔴 {member.mention} "
                "has been force clocked out.\n\n"
                f"**Shift:** "
                f"{format_duration(shift_seconds)}\n"
                f"**Weekly Total:** "
                f"{format_duration(new_total)}",
                ephemeral=True
            )

        await update_staff_hub(
            interaction.guild
        )

# ============================================================
# TIME PARSER
# ============================================================

def parse_duration(text):

    text = text.lower().strip()

    total = 0

    for part in text.replace(
        ",",
        " "
    ).split():

        try:

            if part.endswith("h"):

                total += (
                    float(part[:-1])
                    * 3600
                )

            elif part.endswith("m"):

                total += (
                    float(part[:-1])
                    * 60
                )

            elif part.endswith("s"):

                total += float(
                    part[:-1]
                )

            else:

                return None

        except:

            return None

    return int(
        total
    )

# ============================================================
# ;SHIFTADMIN
# ============================================================

@bot.command()
async def shiftadmin(ctx):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ You must be Management+ "
            "to use Shift Admin."
        )

        return

    embed = discord.Embed(
        title="🛠️ Shift Administration",
        description=(
            "Manage staff shifts using the controls below.\n\n"
            "➕ **Add Time**\n"
            "➖ **Remove Time**\n"
            "🟢 **Force Clock In**\n"
            "🔴 **Force Clock Out**"
        ),
        color=discord.Color.blurple()
    )

    await ctx.send(
        embed=embed,
        view=ShiftAdminView()
    )

# ============================================================
# ;FILES
# ============================================================

@bot.command()
async def files(ctx):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ Management+ only."
        )

        return

    try:

        if not os.path.exists(
            DATA_FILE
        ):

            await ctx.send(
                "❌ `staff_hours.json` "
                "does not exist yet."
            )

            return

        await ctx.send(
            "📁 **Staff Hours Backup**\n"
            "Here is the current "
            "`staff_hours.json` file:",
            file=discord.File(
                DATA_FILE,
                filename="staff_hours.json"
            )
        )

    except Exception as e:

        await ctx.send(
            "❌ Couldn't send the file:\n"
            f"```text\n{e}\n```"
        )

# ============================================================
# ;RESTORE
# ============================================================

@bot.command()
async def restore(ctx):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ Management+ only."
        )

        return

    if not ctx.message.attachments:

        await ctx.send(
            "❌ Please attach your backup "
            "`staff_hours.json` file to "
            "the `;restore` command."
        )

        return

    attachment = (
        ctx.message.attachments[0]
    )

    if not attachment.filename.lower().endswith(
        ".json"
    ):

        await ctx.send(
            "❌ The file must be a `.json` file."
        )

        return

    try:

        file_bytes = await attachment.read()

        file_text = file_bytes.decode(
            "utf-8"
        )

        restored_data = json.loads(
            file_text
        )

        if not isinstance(
            restored_data,
            dict
        ):

            await ctx.send(
                "❌ Invalid backup. "
                "The JSON must contain an object."
            )

            return

        required_sections = [
            "weekly_hours",
            "clocked_in",
            "staff_hub"
        ]

        for section in required_sections:

            if section not in restored_data:

                await ctx.send(
                    f"❌ Invalid backup. "
                    f"Missing `{section}`."
                )

                return

        if os.path.exists(
            DATA_FILE
        ):

            with open(
                DATA_FILE,
                "rb"
            ) as current_file:

                current_data = (
                    current_file.read()
                )

            with open(
                RESTORE_BACKUP_FILE,
                "wb"
            ) as backup_file:

                backup_file.write(
                    current_data
                )

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                restored_data,
                file,
                indent=4
            )

        staff_data.clear()

        staff_data.update(
            restored_data
        )

        staff_data.setdefault(
            "weekly_hours",
            {}
        )

        staff_data.setdefault(
            "clocked_in",
            {}
        )

        staff_data.setdefault(
            "staff_hub",
            {}
        )

        save_data()

        await update_staff_hub(
            ctx.guild
        )

        await ctx.send(
            "✅ **Staff Hours Restored Successfully!**\n\n"
            "💾 The backup was valid and has been restored.\n"
            "🛡️ The previous file was backed up as "
            "`staff_hours_before_restore.json`."
        )

    except json.JSONDecodeError:

        await ctx.send(
            "❌ **Restore failed.**\n\n"
            "The uploaded file contains invalid JSON.\n"
            "Your existing staff hours were **not changed**."
        )

    except UnicodeDecodeError:

        await ctx.send(
            "❌ **Restore failed.**\n\n"
            "The uploaded file could not be read as UTF-8.\n"
            "Your existing staff hours were **not changed**."
        )

    except Exception as e:

        await ctx.send(
            "❌ **Restore failed.**\n\n"
            "Your existing staff hours were **not changed**.\n\n"
            f"Error:\n```text\n{e}\n```"
        )

# ============================================================
# MANAGEMENT HUB
# ============================================================

class PrivateHubView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Infract",
        style=discord.ButtonStyle.danger,
        emoji="⚠️"
    )
    async def infract(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="⚠️ Infract",
            description=(
                "Select the type of infraction you want to issue."
            ),
            color=discord.Color.dark_red()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=InfractView()
        )

    @discord.ui.button(
        label="Sessions",
        style=discord.ButtonStyle.primary,
        emoji="📡"
    )
    async def sessions(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="📡 Session Management",
            description="Select a session action below.",
            color=discord.Color.blue()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=SessionView()
        )

# ============================================================
# PUBLIC MANAGEMENT HUB
# ============================================================

class PublicHubView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Open Management Hub",
        style=discord.ButtonStyle.primary,
        emoji="🛠️"
    )
    async def open_hub(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use the Management Hub.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="🛠️ Management Hub",
            description="Select a management action below.",
            color=discord.Color.dark_red()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PrivateHubView(),
            ephemeral=True
        )

# ============================================================
# ;HUB
# ============================================================

@bot.command()
async def hub(ctx):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ You don't have permission to use the Management Hub."
        )

        return

    embed = discord.Embed(
        title="🛠️ Management Hub",
        description=(
            "Welcome to the Management Hub.\n\n"
            "Click the button below to open the "
            "management controls."
        ),
        color=discord.Color.dark_red()
    )

    await ctx.send(
        embed=embed,
        view=PublicHubView()
    )

# ============================================================
# SAY
# ============================================================

@bot.command()
async def say(ctx, *, message):

    # ========================================================
    # SAY BLACKLIST COMMAND
    # ========================================================

    if message.lower().startswith(
        "blacklist"
    ):

        if not is_management(
            ctx.author
        ):

            await ctx.send(
                "❌ You don't have permission "
                "to use this."
            )

            return

        parts = message.split()

        if len(parts) < 2:

            await ctx.send(
                "❌ Usage: `;say blacklist @user`"
            )

            return

        target = None

        # Try to find a mentioned user
        if ctx.message.mentions:

            target = ctx.message.mentions[0]

        else:

            # Also allow a raw Discord user ID
            try:

                target_id = int(
                    parts[1]
                )

                target = ctx.guild.get_member(
                    target_id
                )

            except:

                target = None

        if target is None:

            await ctx.send(
                "❌ Please mention a valid "
                "server member or provide their User ID."
            )

            return

        user_id = str(
            target.id
        )

        if user_id in say_blacklist:

            await ctx.send(
                f"⚠️ {target.mention} is already "
                "blacklisted from `;say`."
            )

            return

        say_blacklist.add(
            user_id
        )

        save_say_blacklist()

        await ctx.send(
            f"🚫 {target.mention} has been "
            "blacklisted from using `;say`."
        )

        return

    # ========================================================
    # CHECK SAY BLACKLIST
    # ========================================================

    if str(ctx.author.id) in say_blacklist:

        await ctx.send(
            "❌ You are blacklisted from using `;say`."
        )

        return

    # ========================================================
    # MANAGEMENT CHECK
    # ========================================================

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ You don't have permission "
            "to use this."
        )

        return

    # ========================================================
    # DELETE ONLY THE USER'S SAY COMMAND
    # ========================================================

    try:

        await ctx.message.delete()

    except discord.Forbidden:

        pass

    except discord.NotFound:

        pass

    # ========================================================
    # SEND SAY MESSAGE
    # ========================================================

    await ctx.send(
        message
    )

# ============================================================
# ;UNBLACKLIST
# ============================================================

@bot.command()
async def unblacklist(ctx, member: discord.Member = None):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ You don't have permission "
            "to use this."
        )

        return

    if member is None:

        await ctx.send(
            "❌ Usage: `;unblacklist @user`"
        )

        return

    user_id = str(
        member.id
    )

    if user_id not in say_blacklist:

        await ctx.send(
            f"⚠️ {member.mention} is not "
            "blacklisted from `;say`."
        )

        return

    say_blacklist.remove(
        user_id
    )

    if not save_say_blacklist():

        await ctx.send(
            "❌ I couldn't save the updated "
            "say blacklist."
        )

        return

    await ctx.send(
        f"✅ {member.mention} has been "
        "unblacklisted from using `;say`."
    )

# ============================================================
# ;RAINBOW
# ============================================================

@bot.command()
async def rainbow(ctx, member: discord.Member = None):

    if not any(
        role.id == RAINBOW_ROLE_ID
        for role in ctx.author.roles
    ):

        await ctx.send(
            "❌ You don't have permission "
            "to use this."
        )

        return

    if member is None:

        await ctx.send(
            "❌ Usage: `;rainbow @user`"
        )

        return

    try:

        await member.timeout(
            timedelta(minutes=10),
            reason=f"Rainbow command used by {ctx.author}"
        )

        await ctx.send(
            "🌈 rainbows deployed!"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ I can't timeout that user. "
            "Make sure my bot role is above their role."
        )

    except Exception as e:

        await ctx.send(
            "❌ Failed to timeout the user:\n"
            f"```text\n{e}\n```"
        )

# ============================================================
# ;UNRAINBOW
# ============================================================

@bot.command()
async def unrainbow(ctx, member: discord.Member = None):

    if not any(
        role.id == RAINBOW_ROLE_ID
        for role in ctx.author.roles
    ):

        await ctx.send(
            "❌ You don't have permission "
            "to use this."
        )

        return

    if member is None:

        await ctx.send(
            "❌ Usage: `;unrainbow @user`"
        )

        return

    try:

        await member.timeout(
            None,
            reason=f"Unrainbow command used by {ctx.author}"
        )

        await ctx.send(
            "🌈 rainbows un-deployed!"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ I can't remove the timeout from that user."
        )

    except Exception as e:

        await ctx.send(
            "❌ Failed to remove the timeout:\n"
            f"```text\n{e}\n```"
        )

# ============================================================
# RESTART
# ============================================================

@bot.command()
async def restart(ctx):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ You don't have permission "
            "to restart the bot."
        )

        return

    await ctx.send(
        "🔄 **Restarting bot...**"
    )

    await bot.close()

    os.execv(
        os.sys.executable,
        [
            os.sys.executable
        ] + os.sys.argv
    )

# ============================================================
# ;NP - NO PING
# ============================================================

@bot.command()
async def np(ctx, member: discord.Member = None):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ You don't have permission to use this."
        )

        return

    if member is None:

        await ctx.send(
            "❌ Usage: `;np @user`"
        )

        return

    user_id = str(
        member.id
    )

    enabled_users = no_ping_data["enabled_users"]

    if user_id in enabled_users:

        enabled_users.remove(
            user_id
        )

        save_no_ping_data()

        await ctx.send(
            f"🔕 No Ping has been **disabled** for {member.mention}."
        )

        return

    enabled_users.append(
        user_id
    )

    save_no_ping_data()

    await ctx.send(
        f"🔕 No Ping has been **enabled** for {member.mention}.\n\n"
        "They should not be mentioned or replied to."
    )


# ============================================================
# PING
# ============================================================

@bot.command()
async def ping(ctx):

    await ctx.send(
        "Pong! 🏓"
    )

# ============================================================
# INFRACTION MODAL
# ============================================================

class InfractionModal(discord.ui.Modal):

    def __init__(
        self,
        role_id,
        role_name
    ):

        super().__init__(
            title=f"Issue {role_name}"
        )

        self.role_id = role_id
        self.role_name = role_name

        self.user_id = discord.ui.TextInput(
            label="User ID",
            placeholder="Enter the user's Discord ID",
            required=True,
            max_length=20
        )

        self.add_item(
            self.user_id
        )

    async def on_submit(
        self,
        interaction
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        try:

            member_id = int(
                self.user_id.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ That isn't a valid Discord user ID.",
                ephemeral=True
            )

            return

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ This can only be used inside a server.",
                ephemeral=True
            )

            return

        member = guild.get_member(
            member_id
        )

        if member is None:

            await interaction.response.send_message(
                "❌ I couldn't find that member in this server.",
                ephemeral=True
            )

            return

        role = guild.get_role(
            self.role_id
        )

        if role is None:

            await interaction.response.send_message(
                f"❌ I couldn't find the "
                f"**{self.role_name}** role.",
                ephemeral=True
            )

            return

        try:

            await member.add_roles(
                role
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I can't give that role.\n\n"
                "Make sure the bot's role is ABOVE the role "
                "it is trying to give.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="✅ Infraction Issued",
            description=(
                "The infraction was successfully issued."
            ),
            color=discord.Color.green()
        )

        embed.add_field(
            name="👤 User",
            value=member.mention,
            inline=False
        )

        embed.add_field(
            name="⚠️ Infraction",
            value=self.role_name,
            inline=False
        )

        embed.add_field(
            name="🏷️ Role Given",
            value=role.mention,
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=AfterInfractionView()
        )

# ============================================================
# AFTER INFRACTION
# ============================================================

class AfterInfractionView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Back to Infract",
        style=discord.ButtonStyle.secondary,
        emoji="⬅️"
    )
    async def back_to_infract(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="⚠️ Infract",
            description=(
                "Select the type of infraction you want to issue."
            ),
            color=discord.Color.dark_red()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=InfractView()
        )

# ============================================================
# INFRACT PAGE
# ============================================================

class InfractView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Strike I",
        style=discord.ButtonStyle.danger,
        emoji="⚠️"
    )
    async def strike_i(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            InfractionModal(
                STRIKE_I_ROLE_ID,
                "Strike I"
            )
        )

    @discord.ui.button(
        label="Strike II",
        style=discord.ButtonStyle.danger,
        emoji="⚠️"
    )
    async def strike_ii(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            InfractionModal(
                STRIKE_II_ROLE_ID,
                "Strike II"
            )
        )

    @discord.ui.button(
        label="Strike III",
        style=discord.ButtonStyle.danger,
        emoji="⚠️"
    )
    async def strike_iii(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            InfractionModal(
                STRIKE_III_ROLE_ID,
                "Strike III"
            )
        )

    @discord.ui.button(
        label="Suspended",
        style=discord.ButtonStyle.danger,
        emoji="⛔"
    )
    async def suspended(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            InfractionModal(
                SUSPENDED_ROLE_ID,
                "Suspended"
            )
        )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        emoji="⬅️"
    )
    async def back(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="🛠️ Management Hub",
            description="Select a management action below.",
            color=discord.Color.dark_red()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=PrivateHubView()
        )

# ============================================================
# SSU VOTE VIEW
# ============================================================

class SSUVoteView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.success,
        emoji="🟢"
    )
    async def yes(
        self,
        interaction,
        button
    ):

        current_vote = ssu_votes.get(
            interaction.user.id
        )

        if current_vote == "yes":

            await interaction.response.send_message(
                "⚠️ You have already voted **Yes**. "
                "If you need to change your vote, "
                "click the corresponding button.",
                ephemeral=True
            )

            return

        ssu_votes[
            interaction.user.id
        ] = "yes"

        await interaction.response.send_message(
            "🟢 Your vote has been recorded as **Yes**!",
            ephemeral=True
        )

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        emoji="🔴"
    )
    async def no(
        self,
        interaction,
        button
    ):

        current_vote = ssu_votes.get(
            interaction.user.id
        )

        if current_vote == "no":

            await interaction.response.send_message(
                "⚠️ You have already voted **No**. "
                "If you need to change your vote, "
                "click the corresponding button.",
                ephemeral=True
            )

            return

        ssu_votes[
            interaction.user.id
        ] = "no"

        await interaction.response.send_message(
            "🔴 Your vote has been changed to **No**.",
            ephemeral=True
        )

# ============================================================
# ;SSUVOTES
# ============================================================

@bot.command()
async def ssuvotes(ctx):

    if not is_management(
        ctx.author
    ):

        await ctx.send(
            "❌ You don't have permission to use this."
        )

        return

    yes_votes = []
    no_votes = []

    for user_id, vote in ssu_votes.items():

        member = ctx.guild.get_member(
            user_id
        )

        if member is None:
            continue

        if vote == "yes":

            yes_votes.append(
                member.mention
            )

        elif vote == "no":

            no_votes.append(
                member.mention
            )

    embed = discord.Embed(
        title="📊 SSU Vote Results",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name=f"🟢 Yes — {len(yes_votes)}",
        value=(
            "\n".join(yes_votes)
            if yes_votes
            else "Nobody has voted Yes yet."
        ),
        inline=False
    )

    embed.add_field(
        name=f"🔴 No — {len(no_votes)}",
        value=(
            "\n".join(no_votes)
            if no_votes
            else "Nobody has voted No yet."
        ),
        inline=False
    )

    total_votes = (
        len(yes_votes)
        + len(no_votes)
    )

    embed.set_footer(
        text=f"Total Votes: {total_votes}"
    )

    await ctx.send(
        embed=embed
    )

# ============================================================
# SESSION MANAGEMENT
# ============================================================

class SessionView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="SSU Votes",
        style=discord.ButtonStyle.primary,
        emoji="📊",
        row=0
    )
    async def ssu_votes_button(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            SESSION_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ I couldn't find the session announcement channel.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="📊 SSU VOTE",
            description=(
                "We're considering hosting a new session!\n\n"
                "Would you attend?\n\n"
                "🟢 **Yes** — I'm interested\n"
                "🔴 **No** — I won't be attending\n\n"
                "Cast your vote below!"
            ),
            color=discord.Color.blurple()
        )

        await channel.send(
            content=f"||<@&{SESSION_PING_ROLE_ID}>||",
            embed=embed,
            view=SSUVoteView(),
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ SSU Vote Sent",
                description=(
                    f"The SSU vote was sent to "
                    f"<#{SESSION_CHANNEL_ID}>."
                ),
                color=discord.Color.green()
            ),
            view=AfterSessionView()
        )

    @discord.ui.button(
        label="SSU",
        style=discord.ButtonStyle.success,
        emoji="📢",
        row=0
    )
    async def ssu(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            SESSION_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ I couldn't find the session announcement channel.",
                ephemeral=True
            )

            return

        ssu_votes.clear()

        embed = discord.Embed(
            title="📢 SESSION STARTING",
            description=(
                "A new session is now being hosted!\n\n"
                "Come join us in-game and be part of the action.\n\n"
                f"🎮 **In-Game Code:** `{SESSION_CODE}`\n\n"
                "We hope to see you there!"
            ),
            color=discord.Color.green()
        )

        await channel.send(
            content=f"||<@&{SESSION_PING_ROLE_ID}>||",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ SSU Sent",
                description=(
                    f"The SSU announcement was sent to "
                    f"<#{SESSION_CHANNEL_ID}>.\n\n"
                    "📊 All previous SSU votes have been reset."
                ),
                color=discord.Color.green()
            ),
            view=AfterSessionView()
        )

    @discord.ui.button(
        label="SSD",
        style=discord.ButtonStyle.danger,
        emoji="🔴",
        row=1
    )
    async def ssd(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            SESSION_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ I couldn't find the session announcement channel.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="🔴 SESSION CONCLUDED",
            description=(
                "The current session has officially come to an end.\n\n"
                "Thank you to everyone who participated!\n\n"
                "We appreciate your time and hope to see you "
                "at our next session."
            ),
            color=discord.Color.red()
        )

        await channel.send(
            embed=embed
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ SSD Sent",
                description=(
                    f"The SSD announcement was sent to "
                    f"<#{SESSION_CHANNEL_ID}>."
                ),
                color=discord.Color.green()
            ),
            view=AfterSessionView()
        )

    @discord.ui.button(
        label="Low Session Ping",
        style=discord.ButtonStyle.primary,
        emoji="📉",
        row=1
    )
    async def low_session(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            SESSION_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ I couldn't find the session announcement channel.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="📉 LOW SESSION",
            description=(
                "Our server population is starting to drop.\n\n"
                "If you're available, please join us in-game "
                "and help keep the session active!\n\n"
                "Every player counts — we hope to see you there! 🫡"
            ),
            color=discord.Color.orange()
        )

        await channel.send(
            content=f"||<@&{SESSION_PING_ROLE_ID}>||",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Low Session Ping Sent",
                description=(
                    f"The low session announcement was sent to "
                    f"<#{SESSION_CHANNEL_ID}>."
                ),
                color=discord.Color.green()
            ),
            view=AfterSessionView()
        )

# ============================================================
# AFTER SESSION
# ============================================================

class AfterSessionView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Back to Sessions",
        style=discord.ButtonStyle.secondary,
        emoji="⬅️"
    )
    async def back(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="📡 Session Management",
            description="Select a session action below.",
            color=discord.Color.blue()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=SessionView()
        )

    @discord.ui.button(
        label="Back to Hub",
        style=discord.ButtonStyle.secondary,
        emoji="🏠"
    )
    async def hub(
        self,
        interaction,
        button
    ):

        if not is_management(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ You don't have permission to use this.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="🛠️ Management Hub",
            description="Select a management action below.",
            color=discord.Color.dark_red()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=PrivateHubView()
        )

# ============================================================
# ;EXECUTE
# ============================================================

import random

@bot.command()
async def execute(ctx, member: discord.Member = None):

    if not is_management(ctx.author):

        await ctx.send(
            "❌ You don't have permission to use this."
        )

        return

    if member is None:

        await ctx.send(
            "❌ Usage: `;execute @user`"
        )

        return

    executions = [

        (
            "🔫 **NERF GUN EXECUTION**\n\n"
            f"{member.mention} has been sentenced to death by Nerf gun.\n\n"
            "*The firing squad raises their weapons...*\n"
            "🔫 **PEW PEW PEW!**\n\n"
            "💀 Target has been eliminated by foam darts."
        ),

        (
            "🍞 **BREAD EXECUTION**\n\n"
            f"{member.mention} has been found guilty of being silly.\n\n"
            "The legendary loaf has been retrieved...\n"
            "🍞 **BONK!**\n\n"
            "💀 Target has been defeated by bread."
        ),

        (
            "🐟 **FISH SLAP EXECUTION**\n\n"
            f"{member.mention} has been sentenced to the fish chamber.\n\n"
            "🐟 *A fish has entered the chat...*\n"
            "💥 **SLAP!**\n\n"
            "💀 Target has been fish-slapped into oblivion."
        ),

        (
            "🪑 **CHAIR EXECUTION**\n\n"
            f"{member.mention} was caught lacking.\n\n"
            "🪑 *A suspiciously heavy chair approaches...*\n"
            "💥 **BONK!**\n\n"
            "💀 Target has been defeated by furniture."
        ),

        (
            "🐌 **SNAIL EXECUTION**\n\n"
            f"{member.mention} has been sentenced to a race against a snail.\n\n"
            "🐌 The snail has been released...\n"
            "⏳ 47 years later...\n\n"
            "💀 Target lost."
        ),

        (
            "🧹 **CLEANING EXECUTION**\n\n"
            f"{member.mention} has been sentenced to server cleanup.\n\n"
            "🧹 The mop has been deployed.\n"
            "🪣 The bucket has been activated.\n\n"
            "💀 Target has been defeated by janitorial duties."
        ),

        (
            "🥄 **SPOON EXECUTION**\n\n"
            f"{member.mention} has been selected for the forbidden spoon ritual.\n\n"
            "🥄 *The spoon has been raised...*\n"
            "💥 **CLONK!**\n\n"
            "💀 Target has been spooned out of existence."
        ),

        (
            "🧦 **SOCK EXECUTION**\n\n"
            f"{member.mention} has been sentenced to 1,000 sock throws.\n\n"
            "🧦 **SOCK 1... SOCK 2... SOCK 3...**\n\n"
            "💀 Target has surrendered."
        ),

        (
            "🚪 **WINDOW YEETING**\n\n"
            f"{member.mention} has been dramatically escorted to the imaginary window.\n\n"
            "🚪 *Dramatic music intensifies...*\n"
            "💨 **YEET!**\n\n"
            "💀 Target has been launched into the shadow realm."
        ),

        (
            "💀 **CRINGE EXECUTION**\n\n"
            f"{member.mention} has been exposed for extreme levels of cringe.\n\n"
            "📸 Evidence has been reviewed.\n"
            "😬 Everyone has looked away in disappointment.\n\n"
            "💀 Target has died of secondhand embarrassment."
        ),

        (
            "🍳 **FRYING PAN EXECUTION**\n\n"
            f"{member.mention} has been sentenced to the frying pan.\n\n"
            "🍳 *PAN DEPLOYED.*\n"
            "💥 **BONK!**\n\n"
            "💀 Target has been seasoned and defeated."
        ),

        (
            "📦 **CARDBOARD BOX EXECUTION**\n\n"
            f"{member.mention} has been placed inside a cardboard box.\n\n"
            "📦 Box secured.\n"
            "🚚 Box has been shipped to Antarctica.\n\n"
            "💀 Target has been successfully relocated."
        )
    ]

    result = random.choice(executions)

    embed = discord.Embed(
        title="⚖️ EXECUTION NOTICE",
        description=result,
        color=discord.Color.dark_red()
    )

    embed.set_footer(
        text=f"Executed by {ctx.author.display_name}"
    )

    await ctx.send(
        embed=embed
    )

# ============================================================
# ;ID
# ============================================================

@bot.command()
async def id(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    await ctx.send(
        f"🆔 **{member.display_name}'s Discord User ID:**\n"
        f"`{member.id}`"
    )

# ============================================================
# MEMBER WELCOME SYSTEM
# ============================================================

WELCOME_CHANNEL_ID = 1541499305679126558


@bot.event
async def on_member_join(member):

    channel = member.guild.get_channel(
        WELCOME_CHANNEL_ID
    )

    if channel is None:
        print(
            "❌ Welcome channel could not be found."
        )
        return

    member_count = member.guild.member_count

    embed = discord.Embed(
        title="👋 Welcome!",
        description=(
            f"Welcome to **{member.guild.name}**, "
            f"{member.mention}!\n\n"
            f"🎉 We're now at **{member_count:,} members**!"
        ),
        color=discord.Color.green()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text=f"Member #{member_count:,}"
    )

    await channel.send(
        content=member.mention,
        embed=embed
    )

# ============================================================
# NO PING MESSAGE CHECK
# ============================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    protected_ids = set(
        str(user_id)
        for user_id in no_ping_data.get(
            "enabled_users",
            []
        )
    )

    if protected_ids:

        mentioned_protected = [
            member
            for member in message.mentions
            if str(member.id) in protected_ids
        ]

        replied_protected = None

        if message.reference is not None:

            referenced_message = message.reference.resolved

            if referenced_message is None and message.reference.message_id:
                try:
                    referenced_message = await message.channel.fetch_message(
                        message.reference.message_id
                    )
                except (
                    discord.NotFound,
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    referenced_message = None

            if (
                referenced_message is not None
                and referenced_message.author is not None
                and str(referenced_message.author.id) in protected_ids
            ):
                replied_protected = referenced_message.author

        protected_targets = {}

        for member in mentioned_protected:
            protected_targets[member.id] = member

        if replied_protected is not None:
            protected_targets[replied_protected.id] = replied_protected

        # Do not count the management ;np command itself as a violation.
        is_np_command = message.content.strip().lower().startswith(
            ";np"
        )

        if protected_targets and not is_np_command:

            offender_id = str(
                message.author.id
            )

            current_violations = int(
                no_ping_data["violations"].get(
                    offender_id,
                    0
                )
            )

            current_violations += 1

            if current_violations >= 3:

                no_ping_data["violations"][
                    offender_id
                ] = 0

                save_no_ping_data()

                try:
                    await message.author.timeout(
                        timedelta(
                            minutes=NO_PING_TIMEOUT_MINUTES
                        ),
                        reason="Third No Ping violation"
                    )

                    await message.channel.send(
                        f"🚫 {message.author.mention} has been timed out for "
                        f"**{NO_PING_TIMEOUT_MINUTES} minutes** for repeatedly "
                        "pinging a No Ping user."
                    )

                except discord.Forbidden:

                    await message.channel.send(
                        f"🚫 **Third No Ping violation.** {message.author.mention} "
                        "should have been timed out, but I don't have permission "
                        "to do so."
                    )

                except discord.HTTPException:

                    await message.channel.send(
                        f"🚫 **Third No Ping violation.** {message.author.mention} "
                        "could not be timed out due to a Discord error."
                    )

            else:

                no_ping_data["violations"][
                    offender_id
                ] = current_violations

                save_no_ping_data()

                warnings_remaining = 3 - current_violations

                await message.channel.send(
                    "🚫 **Do not ping this user.**\n\n"
                    f"You have **{warnings_remaining} warning"
                    f"{'s' if warnings_remaining != 1 else ''} remaining** "
                    "before you will be timed out."
                )

    await bot.process_commands(
        message
    )


# ============================================================
# TOKEN
# ============================================================

token = os.getenv(
    "DISCORD_TOKEN"
)

if not token:

    print(
        "ERROR: DISCORD_TOKEN is not set!"
    )

else:

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    bot.run(
        token
    )
