import discord
from discord.ext import commands
import random
import string
import asyncio

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="/", intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await self.tree.sync()  # Sync commands when bot is ready
        print("Commands synced!")

# Instantiate the bot
bot = MyBot()

# Store user verification attempts (in-memory, could be persisted in a DB if needed)
user_attempts = {}

def create_embed(title, description, color=discord.Color(0xaba0f1)):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

@bot.tree.command(name="verifysetup", description="Set up the verification system.")
async def verifysetup(interaction: discord.Interaction):
    """Sets up the verification system with a message and button."""
    channel_id = 1324427419993636984  # Verification channel ID
    channel = bot.get_channel(channel_id)

    # Check if the channel exists and log the result
    if not channel:
        print(f"Channel with ID {channel_id} not found.")
    else:
        print(f"Found channel: {channel.name}")
        
    if channel:
        message_content = "Please click the button below to start the verification process."
        # Create the button
        view = discord.ui.View()
        button = discord.ui.Button(label="Verify Me", emoji="✅", style=discord.ButtonStyle.green)
        button.callback = start_verification  # Set the button callback
        view.add_item(button)
        embed = create_embed("Verification Setup", message_content)
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("Verification setup complete! The message has been sent.", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find the verification channel. Please check the channel ID.", ephemeral=True)

async def start_verification(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    user_data = user_attempts.get(user_id)

    if user_data and user_data['attempts'] >= 3:
        time_since_last_attempt = discord.utils.utcnow() - user_data['cooldown_end_time']
        remaining_time = 300 - int(time_since_last_attempt.total_seconds())
        if remaining_time > 0:
            embed = create_embed("Verification Cooldown", f"You are on cooldown. Please wait {remaining_time} seconds.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        else:
            user_data['attempts'] = 0

    verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    user_attempts[user_id] = {
        'code': verification_code,
        'attempts': 0,
        'last_attempt_time': None,
        'cooldown_end_time': None
    }

    try:
        embed = create_embed("Verification", f"Your verification code: {verification_code}\nPlease type the code below.")
        await interaction.user.send(embed=embed)
        await interaction.followup.send("I have sent the verification code to your DMs. Please check your DMs.", ephemeral=True)
    except discord.errors.Forbidden:
        embed = create_embed(
            "Verification Failed",
            "I cannot send you a DM. Tutorial on how to fix: https://provocis.com/how-to-turn-on-direct-messages-on-discord.html"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id
        if user_id in user_attempts:
            user_data = user_attempts[user_id]
            correct_code = user_data['code']

            if user_data['attempts'] >= 3 and user_data['cooldown_end_time']:
                time_since_last_attempt = discord.utils.utcnow() - user_data['cooldown_end_time']
                remaining_time = 300 - int(time_since_last_attempt.total_seconds())
                if remaining_time > 0:
                    embed = create_embed("Verification Failed", f"Wait {remaining_time} seconds before trying again.")
                    await message.channel.send(embed=embed)
                    return
                else:
                    user_data['attempts'] = 0

            if message.content.strip() == correct_code:
                guild = bot.get_guild(1322627297320239155)
                role = guild.get_role(1324427582334042195)
                member = guild.get_member(user_id)
                if role and member:
                    await member.add_roles(role)
                    embed = create_embed("Verification Successful", "You've been given the verified role.")
                    await message.channel.send(embed=embed)
                    del user_attempts[user_id]
                else:
                    embed = create_embed("Role Assignment Failed", "Failed to assign the role. Contact an admin.")
                    await message.channel.send(embed=embed)
            else:
                user_data['attempts'] += 1
                user_data['cooldown_end_time'] = discord.utils.utcnow()
                if user_data['attempts'] < 3:
                    embed = create_embed("Incorrect Code", f"Incorrect code. {3 - user_data['attempts']} attempts left.")
                    await message.channel.send(embed=embed)
                else:
                    embed = create_embed("Retry Limit Reached", "Wait 5 minutes before trying again.")
                    await message.channel.send(embed=embed)
        else:
            embed = create_embed("Verification Not Started", "Click the button in the verification channel to begin.")
            await message.channel.send(embed=embed)

async def create_ticket(user, interaction):
    """Creates a ticket channel for the user."""
    guild_id = 1322627297320239155  # Replace with your guild ID
    category_id = 1324427172928290878  # Replace with your ticket category ID
    guild = bot.get_guild(guild_id)

    if not guild:
        await interaction.followup.send("Error: Guild not found. Check the guild ID.", ephemeral=True)
        return

    category = discord.utils.get(guild.categories, id=category_id)
    if not category:
        await interaction.followup.send("Error: Ticket category not found. Check the category ID.", ephemeral=True)
        return

    try:
        # Create the ticket channel
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True),
            }
        )

        embed = discord.Embed(
            title="Ticket Opened",
            description="Support will assist you shortly.",
            color=discord.Color(0xaba0f1)
        )
        view = discord.ui.View()
        close_button = discord.ui.Button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.red)

        # New Close Ticket Callback
        async def close_ticket_callback(close_interaction: discord.Interaction):
            """New close ticket logic."""
            await close_interaction.response.send_message("Are you sure you want to close the ticket?", ephemeral=True)

            # Create the confirmation buttons
            confirm_button = discord.ui.Button(label="Confirm", emoji="✅", style=discord.ButtonStyle.green)
            cancel_button = discord.ui.Button(label="Cancel", emoji="❌", style=discord.ButtonStyle.red)
            transcript_button = discord.ui.Button(label="Transcript", emoji="📜", style=discord.ButtonStyle.blurple)

            # Confirm close ticket logic
            async def confirm_close(interaction: discord.Interaction):
                log_channel = bot.get_channel(1324427238422089790)  # Channel for ticket logs
                await log_channel.send(f"Ticket for {user.name} has been closed.")
                await ticket_channel.delete(reason="Ticket closed by user.")
                await interaction.response.send_message("Ticket has been closed.", ephemeral=True)

            # Cancel close ticket logic (Delete the confirmation message, not the channel)
            async def cancel_close(interaction: discord.Interaction):
                # Delete the confirmation message only
                await interaction.message.delete()
                await interaction.response.send_message("Ticket closure has been canceled.", ephemeral=True)

            # Button logic for sending the transcript
            async def send_transcript(interaction: discord.Interaction):
                transcript_channel = bot.get_channel(1324427238422089790)  # Log channel for transcripts
                # Fetch all messages from the channel and create the transcript
                messages = [message async for message in ticket_channel.history(limit=100)]  # Fetch recent messages
                
                # Create a transcript embed
                transcript = "\n".join([f"{message.author}: {message.content}" for message in messages])
                embed = discord.Embed(
                    title=f"Transcript for {ticket_channel.name}",
                    description=transcript[:4096],  # Discord embed description max length is 4096 characters
                    color=discord.Color(0xaba0f1)
                )
                await transcript_channel.send(embed=embed)  # Send the embed to the log channel
                await interaction.response.send_message("Transcript sent!", ephemeral=True)


            confirm_button.callback = confirm_close
            cancel_button.callback = cancel_close
            transcript_button.callback = send_transcript

            view.clear_items()  # Remove the old close ticket button
            view.add_item(transcript_button)  # Add the new Transcript button
            view.add_item(confirm_button)
            view.add_item(cancel_button)

            await ticket_channel.send("Please confirm if you want to close the ticket.", view=view)

        close_button.callback = close_ticket_callback
        view.add_item(close_button)
        await ticket_channel.send(embed=embed, view=view)

    except discord.errors.Forbidden:
        print(f"Could not send DM to {user.name}.")

    await interaction.followup.send(f"Ticket created: <#{ticket_channel.id}>", ephemeral=True)

@bot.tree.command(name="ticketsetup", description="Set up the ticket system.")
async def ticketsetup(interaction: discord.Interaction):
    """Sets up the ticket system with a message and button."""
    channel_id = 1324427099968372920  # Replace with your ticket setup channel ID
    channel = bot.get_channel(channel_id)

    if not channel:
        await interaction.response.send_message("Error: Ticket setup channel not found.", ephemeral=True)
        return

    view = discord.ui.View()
    button = discord.ui.Button(label="Open Ticket", emoji="🎫", style=discord.ButtonStyle.green)

    async def button_callback(button_interaction: discord.Interaction):
        await button_interaction.response.defer(ephemeral=True)
        await create_ticket(button_interaction.user, button_interaction)

    button.callback = button_callback
    view.add_item(button)

    embed = discord.Embed(
        title="Ticket System",
        description="Click the button below to open a support ticket.",
        color=discord.Color(0xaba0f1)
    )
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message("Ticket system setup complete!", ephemeral=True)
    
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    
    while True:
        channel = bot.get_channel(1324543547835158579)
        
        if channel:
            # Send the message
            message = await channel.send("THE BOT IS WORKING")
            
            await asyncio.sleep(10)
            
            await message.delete()
        
        await asyncio.sleep(180)

TOKEN = "MTMyNDQxNjA3MjI0MTM4NTU5Mg.GL7Miu.PzVSu-pPKfrJedMGl__egT8B0EXYIHOU783oB4"  # Replace with your bot token
bot.run(TOKEN)

# MTMyNDQxNjA3MjI0MTM4NTU5Mg.GL7Miu.PzVSu-pPKfrJedMGl__egT8B0EXYIHOU783oB4