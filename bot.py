import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import openai
import sqlite3

# Load environment variables conditionally
if not os.getenv('DISCORD_TOKEN') and os.path.exists('.env'):
    load_dotenv(override=True)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_TYPE = os.getenv('AI_TYPE')
AI_ROLE1 = os.getenv('AI_ROLE1')
AI_ROLE2 = os.getenv('AI_ROLE2')
AI_NAME = os.getenv('AI_NAME')
MEMORY_LIMIT = int(os.getenv('MEMORY_LIMIT', 10))

# Set up Discord bot
intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.message_content = True
client = commands.Bot(command_prefix=commands.when_mentioned_or('/'), intents=intents)

# OpenAI GPT-3.5 setup
openai.api_key = OPENAI_API_KEY

# Ensure the config directory exists
if not os.path.exists('config'):
    os.makedirs('config')

# Initialize SQLite database
conn = sqlite3.connect('config/allowed_channels.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS allowed_channels (channel_id INTEGER PRIMARY KEY)''')
conn.commit()

# Initialize memory table
cursor.execute('''CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)''')
conn.commit()

def generate_response(user_message):
    memories = get_memories()
    memory_context = '\n'.join(["Memory {}: {}".format(i+1, mem[1]) for i, mem in enumerate(memories)])
    system_messages = [
        {"role": "system", "content": "You are a helpful {}.".format(AI_TYPE)},
        {"role": "system", "content": "Your name is {}.".format(AI_NAME)},
        {"role": "system", "content": "{}".format(AI_ROLE1)},
        {"role": "system", "content": "{}".format(AI_ROLE2)},
    ]
    if memory_context:
        system_messages.append({"role": "system", "content": "Context memories: {}".format(memory_context)})
    system_messages.append({"role": "user", "content": "{}".format(user_message)})
    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=system_messages,
        max_tokens=5000,
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user.name))
    print('Bot is ready.')
    try:
        await client.tree.sync()
        print('Slash commands synced.')
        print('Bot is ready to interact...')
    except Exception as e:
        print('Error syncing slash commands: {}'.format(e))

# Load allowed channels at startup

target_channels = []

def load_allowed_channels():
    cursor.execute('SELECT channel_id FROM allowed_channels')
    return [row[0] for row in cursor.fetchall()]

def save_allowed_channels():
    cursor.execute('DELETE FROM allowed_channels')
    cursor.executemany('INSERT INTO allowed_channels (channel_id) VALUES (?)', [(channel_id,) for channel_id in target_channels])
    conn.commit()

target_channels = load_allowed_channels()

@client.tree.command(name="set_channel", description="Sets a channel to allow the Bot to interact.")
@app_commands.describe(channel="The channel to allow the bot to interact in.")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    # Check if the user has the "Bot_Admin" role
    if not interaction.user.guild_permissions.administrator and not any(role.name == 'Bot_Admin' for role in getattr(interaction.user, 'roles', [])):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    if channel.id not in target_channels:
        target_channels.append(channel.id)
        save_allowed_channels()
        await interaction.response.send_message("Bot target channel set to {}".format(channel.mention))
    else:
        await interaction.response.send_message("Channel is already in the Allowed Channels List.")

@client.tree.command(name="list_channels", description="Lists all channels where the bot is allowed to interact.")
async def list_channels(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator and not any(role.name == 'Bot_Admin' for role in getattr(interaction.user, 'roles', [])):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    if not target_channels:
        await interaction.response.send_message("No channels are currently set for bot interaction.", ephemeral=True)
        return
    channel_mentions = [interaction.guild.get_channel(channel_id).mention for channel_id in target_channels if interaction.guild.get_channel(channel_id)]
    channels_str = "\n".join(channel_mentions)
    await interaction.response.send_message("Allowed channels for bot interaction:\n{}".format(channels_str), ephemeral=True)

@client.event
async def on_message(message):
    print("Received message: {} in {}".format(message.content, message.channel.id))
    if message.author == client.user:
        return
    # Ignore slash command invocations as messages
    if message.content.startswith('/'):
        return
    if client.user in message.mentions or isinstance(message.channel, discord.DMChannel):
        await handle_bot_mention(message)
    else:
        await client.process_commands(message)

async def handle_bot_mention(message):
    response = generate_response(message.content)
    await message.channel.send("{} {}".format(message.author.mention, response))

def get_memories():
    cursor.execute('SELECT id, content FROM memory ORDER BY id ASC')
    return cursor.fetchall()

def add_memory(content):
    cursor.execute('INSERT INTO memory (content) VALUES (?)', (content,))
    conn.commit()
    # Enforce memory limit
    cursor.execute('SELECT COUNT(*) FROM memory')
    count = cursor.fetchone()[0]
    if count > MEMORY_LIMIT:
        cursor.execute('DELETE FROM memory WHERE id IN (SELECT id FROM memory ORDER BY id ASC LIMIT ?)', (count - MEMORY_LIMIT,))
        conn.commit()

def delete_memory(memory_id):
    cursor.execute('DELETE FROM memory WHERE id = ?', (memory_id,))
    conn.commit()

@client.tree.command(name="remember", description="Store a short memory for the bot to use as context.")
@app_commands.describe(text="The information to remember.")
async def remember(interaction: discord.Interaction, text: str):
    if not interaction.user.guild_permissions.administrator and not any(role.name == 'Bot_Admin' for role in getattr(interaction.user, 'roles', [])):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    add_memory(text)
    await interaction.response.send_message("Memory added! Current memory count: {}/{}".format(len(get_memories()), MEMORY_LIMIT), ephemeral=True)

@client.tree.command(name="forget", description="Remove a memory from the bot's context.")
async def forget(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator and not any(role.name == 'Bot_Admin' for role in getattr(interaction.user, 'roles', [])):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    memories = get_memories()
    if not memories:
        await interaction.response.send_message("No memories to forget.", ephemeral=True)
        return
    memory_list = '\n'.join(["{}. {}".format(i+1, mem[1]) for i, mem in enumerate(memories)])
    await interaction.response.send_message("Current memories:\n{}\nReply with the number to forget.".format(memory_list), ephemeral=True)

    def check(m):
        return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
    try:
        msg = await client.wait_for('message', check=check, timeout=60)
        idx = int(msg.content.strip()) - 1
        if 0 <= idx < len(memories):
            delete_memory(memories[idx][0])
            await interaction.followup.send("Memory {} deleted.".format(idx+1), ephemeral=True)
        else:
            await interaction.followup.send("Invalid number.", ephemeral=True)
    except Exception:
        await interaction.followup.send("No valid response received. Forget cancelled.", ephemeral=True)

client.run(DISCORD_TOKEN)
