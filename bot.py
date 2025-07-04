import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import openai
import sqlite3
import logging
from discord import ui
import re

if not os.getenv('DISCORD_TOKEN') and os.path.exists('.env'):
    load_dotenv(override=True)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_TYPE = os.getenv('AI_TYPE')
AI_ROLE1 = os.getenv('AI_ROLE1')
AI_ROLE2 = os.getenv('AI_ROLE2')
AI_NAME = os.getenv('AI_NAME')
MEMORY_LIMIT = int(os.getenv('MEMORY_LIMIT', 10))
AI_MODEL = os.getenv('AI_MODEL')
AI_SEARCH_MODEL = os.getenv('AI_SEARCH_MODEL') or AI_MODEL
TOKEN_LIMIT = 3000
MAX_DISCORD_MESSAGE_LENGTH = 1995
BOT_ACCESS_ROLE = os.getenv('BOT_ACCESS_ROLE', 'Bot_Access')

intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.message_content = True
client = commands.Bot(command_prefix=commands.when_mentioned_or('/'), intents=intents)

openai.api_key = OPENAI_API_KEY

if not os.path.exists('config'):
    os.makedirs('config')

conn = sqlite3.connect('config/allowed_channels.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS allowed_channels (channel_id INTEGER PRIMARY KEY)''')
conn.commit()
cursor.execute('''CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)''')
conn.commit()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('AI_BOT')

def generate_response(user_message):
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
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
    response = openai_client.chat.completions.create(
        model=AI_MODEL,
        messages=system_messages,
        max_tokens=5000,
        temperature=0.7
    )
    return response.choices[0].message.content

@client.event
async def on_ready():
    logger.info('Logged in as %s', client.user.name)
    logger.info('---')
    logger.info('AI Model: %s', AI_MODEL)
    logger.info('AI Search Model: %s', AI_SEARCH_MODEL)
    logger.info('---')
    logger.info('Bot is ready.')
    try:
        await client.tree.sync()
        logger.info('Slash commands synced.')
        logger.info('Bot is ready to interact...')
    except Exception as e:
        logger.error('Error syncing slash commands: %s', e)

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
    if not interaction.user.guild_permissions.administrator and not any(role.name == BOT_ACCESS_ROLE for role in getattr(interaction.user, 'roles', [])):
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
    if not interaction.user.guild_permissions.administrator and not any(role.name == BOT_ACCESS_ROLE for role in getattr(interaction.user, 'roles', [])):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    if not target_channels:
        await interaction.response.send_message("No channels are currently set for bot interaction.", ephemeral=True)
        return
    channel_mentions = [interaction.guild.get_channel(channel_id).mention for channel_id in target_channels if interaction.guild.get_channel(channel_id)]
    channels_str = "\n".join(channel_mentions)
    await interaction.response.send_message("Allowed channels for bot interaction:\n{}".format(channels_str), ephemeral=True)

def is_allowed_channel(message):
    if not message.guild:
        return False
    return message.channel.id in target_channels

@client.event
async def on_message(message):
    if message.guild:
        server_name = message.guild.name
        channel_name = message.channel.name if hasattr(message.channel, 'name') else str(message.channel)
        location = f"{server_name}:{channel_name}"
    else:
        user_name = message.author.name if hasattr(message.author, 'name') else str(message.author)
        location = f"DM:Direct Message with {user_name}"
    logger.debug("Received message: '%s' in %s (author: %s, id: %s)", message.content, location, message.author, message.author.id)
    if message.author == client.user:
        return
    if message.type != discord.MessageType.default:
        return
    if not message.guild or not is_allowed_channel(message):
        logger.warning("Message ignored: not in allowed channel or is DM.")
        return
    if message.content.startswith('/'):
        return
    if client.user in message.mentions:
        await handle_bot_mention(message)
    else:
        pass  # Do not call process_commands for slash commands

async def handle_bot_mention(message):
    if not message.guild:
        logger.warning("Bot mention in DM ignored.")
        return
    try:
        member = message.guild.get_member(message.author.id)
        if member is None:
            member = await message.guild.fetch_member(message.author.id)
    except Exception:
        member = None
    if not member:
        await message.channel.send("Sorry {}, you do not have permission to interact with the bot.".format(message.author.mention))
        logger.warning("Permission denied: member not found.")
        return
    is_admin = getattr(member.guild_permissions, 'administrator', False)
    has_access_role = any(role.name.strip().lower() == BOT_ACCESS_ROLE.strip().lower() for role in getattr(member, 'roles', []))
    logger.debug("[DEBUG] User: %s | Admin: %s | Roles: %s | BOT_ACCESS_ROLE: %s", message.author, is_admin, [role.name for role in getattr(member, 'roles', [])], BOT_ACCESS_ROLE)
    if not (is_admin or has_access_role):
        await message.channel.send("Sorry {}, you do not have permission to interact with the bot.".format(message.author.mention))
        logger.warning("Permission denied: user %s is not admin and lacks role %s", message.author, BOT_ACCESS_ROLE)
        return
    response = generate_response(message.content)
    await message.channel.send("{} {}".format(message.author.mention, response))
    logger.debug("Responded to %s in %s", message.author, message.channel)

def get_memories():
    cursor.execute('SELECT id, content FROM memory ORDER BY id ASC')
    return cursor.fetchall()

def add_memory(content):
    cursor.execute('INSERT INTO memory (content) VALUES (?)', (content,))
    conn.commit()
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
    if not interaction.user.guild_permissions.administrator and not any(role.name == BOT_ACCESS_ROLE for role in getattr(interaction.user, 'roles', [])):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    add_memory(text)
    await interaction.response.send_message("Memory added! Current memory count: {}/{}".format(len(get_memories()), MEMORY_LIMIT), ephemeral=True)

class ForgetMemoryView(ui.View):
    def __init__(self, memories, timeout=60):
        super().__init__(timeout=timeout)
        self.memories = memories
        self.selected_id = None
        options = [
            discord.SelectOption(label="{}. {}".format(i+1, mem[1]), value=str(mem[0]))
            for i, mem in enumerate(memories)
        ]
        self.select = ui.Select(placeholder="Select a memory to forget...", options=options, min_values=1, max_values=1)
        self.select.callback = self.select_callback
        self.add_item(self.select)
        self.forget_button = ui.Button(label="Forget", style=discord.ButtonStyle.danger)
        self.forget_button.callback = self.forget_callback
        self.add_item(self.forget_button)

    async def select_callback(self, interaction: discord.Interaction):
        self.selected_id = int(self.select.values[0])
        await interaction.response.defer()  # Acknowledge the selection silently

    async def forget_callback(self, interaction: discord.Interaction):
        if self.selected_id is None:
            await interaction.response.send_message("Please select a memory first.", ephemeral=True)
            return
        delete_memory(self.selected_id)
        await interaction.response.send_message("Memory deleted.", ephemeral=True)
        self.stop()

@client.tree.command(name="forget", description="Remove a memory from the bot's context.")
async def forget(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator and not any(role.name == BOT_ACCESS_ROLE for role in getattr(interaction.user, 'roles', [])):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    memories = get_memories()
    if not memories:
        await interaction.response.send_message("No memories to forget.", ephemeral=True)
        return
    view = ForgetMemoryView(memories)
    await interaction.response.send_message("Select a memory to forget:", view=view, ephemeral=True)

@client.tree.command(name="search", description="Perform a web search and get an answer relevant to the bot's current roles, with sources.")
@app_commands.describe(query="What do you want to search for?")
async def search(interaction: discord.Interaction, query: str):
    try:
        await interaction.response.defer(ephemeral=True)
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        memories = get_memories()
        memory_context = '\n'.join(["Memory {}: {}".format(i+1, mem[1]) for i, mem in enumerate(memories)])
        system_prompt = (
            "You are a helpful {}. Your name is {}. {} {} "
            "Always perform a web search for the latest information, regardless of the question phrasing. "
            "Do not rely solely on your core knowledge. "
            "Always consolidate your answer to fit within {} tokens and {} Discord message characters. "
            "If the answer is not relevant to your current roles, respond with: 'No relevant results found for my current roles.' "
            "When providing answers from web search, always include sources (short links or URLs) for any factual claims or summaries. "
        ).format(AI_TYPE, AI_NAME, AI_ROLE1, AI_ROLE2, TOKEN_LIMIT, MAX_DISCORD_MESSAGE_LENGTH)
        if memory_context:
            system_prompt += " Context memories: {}".format(memory_context)
        search_input = (
            "[ALWAYS USE WEB SEARCH TOOL] Please search the web for the latest information to answer the following question, regardless of your core knowledge: {}\n\nSystem: {}"
        ).format(query, system_prompt)
        search_model = AI_SEARCH_MODEL
        response = openai_client.responses.create(
            model=search_model,
            tools=[{"type": "web_search_preview"}],
            input=search_input
        )
        answer = getattr(response, 'output_text', str(response))
        if not answer:
            answer = "No relevant results found for my current roles."
        sources = set()
        for match in re.findall(r'\((https?://[^)]+|[\w.-]+\.[a-z]{2,})\)', answer):
            sources.add(match.strip())
        content = re.sub(r'\((https?://[^)]+|[\w.-]+\.[a-z]{2,})\)', '', answer)
        if sources:
            sources_list = '\n'.join(sorted(sources))
            content = content.strip()
            max_content_len = MAX_DISCORD_MESSAGE_LENGTH - len(sources_list) - 8
            if len(content) > max_content_len:
                content = content[:max_content_len - 3] + '...'
            answer = "{}\n---\nSources:\n{}".format(content, sources_list)
        else:
            if len(answer) > MAX_DISCORD_MESSAGE_LENGTH:
                answer = answer[:MAX_DISCORD_MESSAGE_LENGTH - 3] + "..."
        if len(answer) > MAX_DISCORD_MESSAGE_LENGTH:
            answer = answer[:MAX_DISCORD_MESSAGE_LENGTH - 3] + "..."
        await interaction.followup.send(answer, ephemeral=True)
    except Exception as e:
        logger.error("Error in /search: %s", e)
        try:
            await interaction.followup.send("An error occurred while searching.", ephemeral=True)
        except Exception:
            pass

client.run(DISCORD_TOKEN)
