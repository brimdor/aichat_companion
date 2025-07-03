---
applyTo: '**'
---
# Copilot Instructions: Python Discord Bot Development

## General Coding Standards
- Use Python 3.8+ syntax and typing where appropriate.
- Follow PEP8 for code style and formatting.
- Use clear, descriptive variable and function names.
- Write modular, reusable functions and classes.
- Add docstrings to all public functions and classes.
- Use async/await for all Discord event handlers and commands.
- Handle exceptions gracefully and log errors for debugging.

## Discord Bot Best Practices
- Use the latest stable `discord.py` (or maintained fork) and its `commands.Bot` and `app_commands` APIs.
- Register slash commands using `@client.tree.command` and sync them on startup with `await client.tree.sync()`.
- Use `discord.Intents` to enable only the required intents for your bot's features.
- Always check for permissions before sending or managing messages/channels.
- Use environment variables for sensitive data (tokens, API keys) and never hardcode them.
- Store persistent data (like allowed channels) in a database or file, and load it on startup.
- Use logging for important events, errors, and debugging.

## Slash Commands
- Prefer slash commands (`@client.tree.command`) over prefix commands for new features.
- Use type hints for command arguments (e.g., `channel: discord.TextChannel`).
- Provide helpful descriptions for all commands and arguments.
- Sync commands globally or per-guild as needed.

## Event Handling
- Always call `await client.process_commands(message)` in `on_message` unless you are intentionally blocking command processing.
- Use `on_ready` to sync commands and print bot status.
- Use `on_interaction` for button and component handling.

## Security & Permissions
- Never expose your bot token or API keys in code or logs.
- Check user roles and permissions before executing admin commands.
- Validate all user input to prevent abuse.

## Example Patterns
- Use `discord.ui.View` and `Button` for interactive components.
- Use `discord.Embed` for rich message formatting.
- Use `openai` or other APIs for AI-powered features, with error handling for API failures.

## Domain Knowledge
- Be familiar with Discord's API rate limits and error codes.
- Understand the difference between global and guild slash command registration.
- Know how to use Discord's permission system and intents.

## Preferences
- Prioritize user experience: clear feedback, helpful error messages, and responsive commands.
- Write code that is easy to maintain and extend.
- Document any non-obvious logic or design decisions in comments.

---