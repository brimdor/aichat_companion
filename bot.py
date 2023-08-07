import discord
from discord import Button, ButtonStyle
from discord.ext import commands
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_TYPE = os.getenv('AI_TYPE')
AI_ROLE1 = os.getenv('AI_ROLE1')
AI_ROLE2 = os.getenv('AI_ROLE2')
AI_NAME = os.getenv('AI_NAME')
botname = os.getenv('botname')

# Set up Discord bot
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
client = commands.Bot(command_prefix=commands.when_mentioned_or('/'), intents=intents)

# OpenAI GPT-3.5 setup
openai.api_key = OPENAI_API_KEY

# File to store the allowed channel IDs
allowed_channels_file = "allowed_channels.txt"

# Create a set to store processed custom IDs
processed_custom_ids = set()

# Function to load the allowed channel IDs from the file
def load_allowed_channels():
    if os.path.exists(allowed_channels_file):
        with open(allowed_channels_file, "r") as f:
            return [int(channel_id.strip()) for channel_id in f.readlines()]
    else:
        return []

# Function to save the allowed channel IDs to the file
def save_allowed_channels():
    with open(allowed_channels_file, "w") as f:
        f.write('\n'.join(str(channel_id) for channel_id in target_channels))

# Function to generate AI response
def generate_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=[
            {"role": "system", "content": f"You are a helpful {AI_TYPE}."},
            {"role": "system", "content": f"Your name is {AI_NAME}."},
            {"role": "system", "content": f"{AI_ROLE1}"},
            {"role": "system", "content": f"{AI_ROLE2}"},
            {"role": "user", "content": f"{user_message}"}
        ],
        max_tokens=500,
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

@client.event
async def on_ready():
    global processed_custom_ids
    processed_custom_ids = set()
    print(f'Logged in as {client.user.name}')
    print('Bot is ready.')

@client.command(name='set_channel')
async def handle_set_channel(ctx):
    # Check if the user has the "BroBot_Admin" role
    if 'BroBot_Admin' in [role.name for role in ctx.author.roles]:
        try:
            if ctx.channel.id not in target_channels:
                # Store the target channel ID in the list
                target_channels.append(ctx.channel.id)
                save_allowed_channels()  # Save the updated allowed channels to the file
                await ctx.send(f"Bot target channel set to {ctx.channel.mention}")
            else:
                await ctx.send("Channel is already in the Allowed Channels List.")
        except discord.errors.NotFound:
            await ctx.send("Invalid channel ID. Please provide a valid channel ID.")
    else:
        await ctx.send("You do not have permission to use this command.")

# Function to generate delete buttons for allowed channels
def generate_delete_buttons(channel_list):
    buttons = []
    for channel_info in channel_list:
        channel_id = channel_info.split(' - ')[0]
        button = Button(style=ButtonStyle.red, label="🗑️", custom_id=f"remove_channel_{channel_id}")
        buttons.append(button)
    return buttons

# Function to list the current allowed channels with delete buttons
def list_allowed_channels():
    if not target_channels:
        return []

    channel_list = []
    for channel_id in target_channels:
        channel = client.get_channel(channel_id)
        if channel:
            channel_info = f"{channel_id} - {channel.mention}"
            button = Button(style=ButtonStyle.red, label="🗑️", custom_id=f"remove_channel_{channel_id}")
            channel_list.append((channel_info, button))

    return channel_list

# Function to list the current allowed channels with delete buttons
@client.command(name='list_channels')
async def handle_list_channels(ctx):
    # Check if the user has the "BroBot_Admin" role
    if 'BroBot_Admin' in [role.name for role in ctx.author.roles]:
        allowed_channels_list = list_allowed_channels()
        if allowed_channels_list:
            await ctx.send("Allowed Channels")
            for channel_info, button in allowed_channels_list:
                embed = discord.Embed(description=channel_info)
                await ctx.send(embed=embed, components=[button])
        else:
            await ctx.send("No channels are currently allowed.")
    else:
        await ctx.send("You do not have permission to use this command.")


# Function to handle AI responses when @BroBot is mentioned
@client.event
async def on_message(message):
    # Check if the message mentions the "@BroBot" role
    if any(role.name == botname for role in message.role_mentions):
        await handle_bot_mention(message)
    else:
        await client.process_commands(message)

# Event handler for button click
@client.event
async def on_button_click(interaction, button):
    custom_id = button.custom_id
    if custom_id.startswith("remove_channel_"):
        channel_id = int(custom_id[len("remove_channel_"):])

        if channel_id in target_channels:
            target_channels.remove(channel_id)
            save_allowed_channels()  # Save the updated allowed channels to the file
            # allowed_channels_list = list_allowed_channels()
            # if allowed_channels_list:
            #     embed = discord.Embed(title="Allowed Channels")
            #     for channel_info in allowed_channels_list:
            #         channel_id, channel_mention = channel_info.split(' - ')
            #         channel_id = int(channel_id)
            #         button = Button(style=ButtonStyle.red, label="🗑️", custom_id=f"remove_channel_{channel_id}")
            #         embed.add_field(name=channel_mention, value="Click the button to delete this channel", inline=False)
            #     await interaction.message.edit(embed=embed, components=[button])  # Send each button separately
            # else:
            #     await interaction.message.edit(content="No channels are currently allowed.", components=[])
        else:
            print("Error Adding Channel ID to Allowed Channels List.")  # Debugging print

# Function to handle AI responses when @BroBot is mentioned
async def handle_bot_mention(message):
    if message.channel.id in target_channels:
        # Generate and send AI response using the user's message as the prompt
        response = generate_response(message.content)
        await message.channel.send(response)

# Load the allowed channel IDs when the bot starts up
target_channels = load_allowed_channels()
load_allowed_channels()
# Run the bot
client.run(DISCORD_TOKEN)
