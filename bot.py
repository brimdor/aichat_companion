import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import openai
import sqlite3

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
    print('Logged in as {}'.format(client.user.name))
    print('---')
    print('AI Model: {}'.format(AI_MODEL))
    print('AI Search Model: {}'.format(AI_SEARCH_MODEL))
    print('---')
    print('Bot is ready.')
    try:
        await client.tree.sync()
        print('Slash commands synced.')
        print('Bot is ready to interact...')
    except Exception as e:
        print('Error syncing slash commands: {}'.format(e))

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

@client.event
async def on_message(message):
    if message.guild:
        server_name = message.guild.name
        channel_name = message.channel.name if hasattr(message.channel, 'name') else str(message.channel)
        location = "{}:{}".format(server_name, channel_name)
    else:
        user_name = message.author.name if hasattr(message.author, 'name') else str(message.author)
        location = "DM:Direct Message with {}".format(user_name)
    print("Received message: {} in {}".format(message.content, location))
    if message.author == client.user:
        return
    if message.content.startswith('/'):
        return
    if client.user in message.mentions or isinstance(message.channel, discord.DMChannel):
        await handle_bot_mention(message)
    else:
        await client.process_commands(message)

async def handle_bot_mention(message):
    if message.guild:
        try:
            member = message.guild.get_member(message.author.id)
            if member is None:
                member = await message.guild.fetch_member(message.author.id)
        except Exception:
            member = None
        if not member:
            await message.channel.send(f"Sorry {message.author.mention}, you do not have permission to interact with the bot.")
            return
        is_admin = getattr(member.guild_permissions, 'administrator', False)
        has_access_role = any(role.name.strip().lower() == BOT_ACCESS_ROLE.strip().lower() for role in getattr(member, 'roles', []))
        print(f"[DEBUG] User: {message.author} | Admin: {is_admin} | Roles: {[role.name for role in getattr(member, 'roles', [])]} | BOT_ACCESS_ROLE: {BOT_ACCESS_ROLE}")
        if not (is_admin or has_access_role):
            await message.channel.send(f"Sorry {message.author.mention}, you do not have permission to interact with the bot.")
            return
    else:
        await message.channel.send(f"Sorry {message.author.mention}, you do not have permission to interact with the bot in DMs.")
        return
    response = generate_response(message.content)
    await message.channel.send(f"{message.author.mention} {response}")

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

@client.tree.command(name="forget", description="Remove a memory from the bot's context.")
async def forget(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator and not any(role.name == BOT_ACCESS_ROLE for role in getattr(interaction.user, 'roles', [])):
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

@client.tree.command(name="search", description="Perform a web search and get an answer relevant to the bot's current roles, with sources.")
@app_commands.describe(query="What do you want to search for?")
async def search(interaction: discord.Interaction, query: str):
    if not interaction.user.guild_permissions.administrator and not any(role.name == BOT_ACCESS_ROLE for role in getattr(interaction.user, 'roles', [])):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    try:
        await interaction.response.defer(thinking=True, ephemeral=True)
        deferred = True
    except Exception:
        deferred = False
    try:
        from openai import OpenAI
        import re
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        system_prompt = (
            "You are a helpful {0}. Your name is {1}. {2} {3} "
            "Always perform a web search for the latest information, regardless of the question phrasing. "
            "Do not rely solely on your core knowledge. "
            "Always consolidate your answer to fit within {4} tokens and {5} Discord message characters. "
            "If the answer is not relevant to your current roles, respond with: 'No relevant results found for my current roles.' "
            "When providing answers from web search, always include sources (short links or URLs) for any factual claims or summaries. "
        ).format(AI_TYPE, AI_NAME, AI_ROLE1, AI_ROLE2, TOKEN_LIMIT, MAX_DISCORD_MESSAGE_LENGTH)
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
            answer = f"{content}\n---\nSources:\n{sources_list}"
        else:
            if len(answer) > MAX_DISCORD_MESSAGE_LENGTH:
                answer = answer[:MAX_DISCORD_MESSAGE_LENGTH - 3] + "..."
        if len(answer) > MAX_DISCORD_MESSAGE_LENGTH:
            answer = answer[:MAX_DISCORD_MESSAGE_LENGTH - 3] + "..."
        if deferred:
            await interaction.followup.send(answer, ephemeral=True)
        else:
            await interaction.response.send_message(answer, ephemeral=True)
    except Exception as e:
        error_msg = f"Error during web search: {e}"
        if len(error_msg) > MAX_DISCORD_MESSAGE_LENGTH:
            error_msg = error_msg[:MAX_DISCORD_MESSAGE_LENGTH - 3] + "..."
        try:
            if deferred:
                await interaction.followup.send(error_msg, ephemeral=True)
            else:
                await interaction.response.send_message(error_msg, ephemeral=True)
        except Exception:
            pass

client.run(DISCORD_TOKEN)
