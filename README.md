# AI Chat Companion: Fully Customizable ChatGPT Discord Bot

Bot is a powerful, fully customizable Discord bot powered by OpenAI's GPT models (GPT-3.5, GPT-4, or compatible). It is designed for seamless, context-aware conversation and advanced server management, with all AI behavior and persona controlled via environment variables. The bot is production-ready, secure, and easy to deploy using Docker.

---

## Features & Capabilities

### AI-Powered Chat
- **Conversational AI**: Uses OpenAI's GPT models for intelligent, context-aware responses.
- **Customizable Persona**: All AI behavior, roles, and name are set via environment variables.
- **Memory System**: Remembers user-provided facts and context (with `/remember`, `/memories`, `/forget` commands).
- **Web Search**: (If enabled) Can answer questions with web search and sources using `/search`.

### Discord Integration
- **Slash Commands**: Modern Discord slash commands for all features (no prefix needed).
- **Allowed Channels**: Restrict bot interaction to specific channels using `/set_channel` and `/list_channels`.
- **Role & Permission Checks**: Only server admins or users with a specific role (configurable) can manage bot settings or interact with admin commands.
- **Interactive UI**: Uses Discord's UI components (buttons, selects) for memory management and other features.
- **Rich Embeds**: Uses Discord embeds for formatted responses (where appropriate).

### Security & Best Practices
- **Environment Variables**: All sensitive data (tokens, API keys, persona) is set via environment variables or a `.env` file. No secrets in code.
- **Database Storage**: Uses SQLite for persistent storage of allowed channels and memory.
- **Logging**: Logs important events and errors for debugging and monitoring.
- **Permissions**: Checks user roles and permissions before executing sensitive commands.
- **Extensible**: Modular code, easy to extend with new commands or AI features.

---

## Environment Variables

Set these in your `.env` file or as Docker environment variables:

| Variable             | Description                                                       | Required | Example                         |
|----------------------|-------------------------------------------------------------------|----------|---------------------------------|
| DISCORD_TOKEN        | Your Discord bot token                                            | Yes      | `DISCORD_TOKEN=...`             |
| OPENAI_API_KEY       | Your OpenAI API key                                               | Yes      | `OPENAI_API_KEY=...`            |
| AI_TYPE              | Short description of the AI's persona (default: "assistant")      | No       | `AI_TYPE=assistant`             |
| AI_ROLE1             | First role/behavior description for the AI                        | Yes      | `AI_ROLE1=Friendly helper`      |
| AI_ROLE2             | Second role/behavior description for the AI                       | Yes      | `AI_ROLE2=Expert coder`         |
| AI_NAME              | The name/persona of the AI (default: Sherlock)                    | No       | `AI_NAME=Sherlock`              |
| AI_MODEL             | OpenAI model to use (e.g. `gpt-3.5-turbo`, `gpt-4o`)              | Yes      | `AI_MODEL=gpt-4`                |
| AI_SEARCH_MODEL      | (Optional) Model for search, defaults to `AI_MODEL`               | No       | `AI_SEARCH_MODEL=gpt-3.5-turbo` |
| MEMORY_LIMIT         | Number of memories to keep (default: 10)                          | No       | `MEMORY_LIMIT=10`               |
| BOT_ACCESS_ROLE      | Role name allowed to manage bot (default: `Bot_Access`)           | No       | `BOT_ACCESS_ROLE=Bot_Admin`     |

---

## Slash Commands

- `/set_channel <#channel>`: Allow the bot to interact in a specific channel (admin or access role only).
- `/list_channels`: List all allowed channels for bot interaction.
- `/remember <text>`: Store a short memory for the bot to use as context.
- `/memories`: List the current memories used for AI context.
- `/forget`: Remove a memory from the bot's context (interactive UI).
- `/search <query>`: (If enabled) Perform a web search and get an answer with sources.

---

## How It Works

- **Persona & Behavior**: The bot's persona, name, and behavior are set entirely by environment variables. Change these to make the bot act as any character or assistant you want.
- **Memory**: Users can add, list, and remove memories that the AI will use as context for better, more relevant responses.
- **Channel Restriction**: Only allowed channels (set by admins or access role) can interact with the bot, preventing spam or abuse.
- **Permissions**: All admin commands require either Discord admin permissions or a custom role (set by `BOT_ACCESS_ROLE`).
- **Security**: No secrets are ever hardcoded. All sensitive data is loaded from environment variables or a `.env` file.

---

## Discord Bot Setup (Discord Developer Portal)

Before running the bot, you must register it with Discord and obtain a bot token:

1. **Go to the [Discord Developer Portal](https://discord.com/developers/applications)** and log in.
2. **Create a New Application**: Click "New Application" and give it a name (e.g., "SherlockBot").
3. **Add a Bot User**: Go to the "Bot" tab and click "Add Bot".
4. **Copy the Token**: Under the Bot section, click "Reset Token" and copy the token. This will be your `DISCORD_TOKEN`.
5. **Set Bot Permissions**: Under "Privileged Gateway Intents", enable:
   - PRESENCE INTENT
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT
6. **OAuth2 Settings**:
   - Go to the "OAuth2" > "URL Generator".
   - Select `bot` and `applications.commands` scopes.
   - Under "Bot Permissions", select:
     - `Send Messages`
     - `Read Message History`
     - `View Channels`
     - `Use Slash Commands`
     - `Manage Channels` (if you want the bot to manage channels)
     - `Embed Links`, `Attach Files`, `Add Reactions` (for richer interactions)
   - Copy the generated URL and use it to invite the bot to your server.

**Note:** Never share your bot token. Store it securely in your `.env` file or as an environment variable.

---

## Docker Deployment

### 1. Build the Docker Image

```bash
docker build -t <image_name> .
```

### 2. Prepare Your `.env` File

Create a `.env` file in the project root with all required environment variables (see above).

### 3. Run the Bot Container

```bash
docker run -d --env-file .env --name <container_name> <image_name>
```

- The bot will automatically create a persistent SQLite database in the container for channel and memory storage.
- To persist data outside the container, mount a volume to `/app/config`.

### 4. (Optional) Kubernetes Deployment

You can deploy Bot to Kubernetes using a deployment YAML and secrets for environment variables. See the example below:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bot-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bot
  template:
    metadata:
      labels:
        app: bot
    spec:
      containers:
      - name: bot
        image: bot:latest
        env:
        - name: DISCORD_TOKEN
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: DISCORD_TOKEN
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: OPENAI_API_KEY
        - name: AI_TYPE
          value: "assistant"
        - name: AI_ROLE1
          value: "Friendly helper"
        - name: AI_ROLE2
          value: "Expert coder"
        - name: AI_NAME
          value: "Sherlock"
```

Create secrets:

```bash
kubectl create secret generic bot-secrets \
  --from-literal=DISCORD_TOKEN=your_discord_bot_token \
  --from-literal=OPENAI_API_KEY=your_openai_api_key
```

Deploy:

```bash
kubectl apply -f bot-deployment.yaml
```

---

## Usage

- Mention the bot or use slash commands in allowed channels to interact.
- Use `/remember`, `/memories`, `/forget` to manage the bot's context memory.
- Only admins or users with the access role can change allowed channels or bot settings.

---

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements or new features.

---

## License

Have Fun!

