# BroBot

BroBot is a Discord bot integrated with OpenAI's GPT-3.5 or GPT-4 model, designed to interact with users through Discord channels and direct messages. It provides intelligent, context-aware responses based on user input.

## Features

- Responds intelligently to user messages using OpenAI GPT-3.5 or GPT-4.
- Allows administrators to specify channels where the bot can interact.
- Provides slash commands to manage allowed channels.
- Interactive buttons to manage channel permissions.

## Slash Commands

- `/set_channel <#channel>`: Allows administrators or users with the "Bot_Admin" role to set a channel as an allowed interaction channel. You select the channel from a dropdown in Discord.
- `/list_channels`: Lists all allowed channels for bot interaction.

## Setup

### Prerequisites

- Docker
- Kubernetes
- Discord Bot Token
- OpenAI API Key

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
AI_TYPE=your_ai_type
AI_ROLE1=your_ai_role_description_1
AI_ROLE2=your_ai_role_description_2
AI_NAME=your_ai_name
```

### Docker Setup

Build the Docker image:

```bash
docker build -t brobot .
```

Run the Docker container:

```bash
docker run -d --env-file .env --name brobot_container brobot
```

### Kubernetes Setup

Create a Kubernetes deployment file (`brobot-deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: brobot-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: brobot
  template:
    metadata:
      labels:
        app: brobot
    spec:
      containers:
      - name: brobot
        image: brobot:latest
        env:
        - name: DISCORD_TOKEN
          valueFrom:
            secretKeyRef:
              name: brobot-secrets
              key: DISCORD_TOKEN
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: brobot-secrets
              key: OPENAI_API_KEY
        - name: AI_TYPE
          value: "your_ai_type"
        - name: AI_ROLE1
          value: "your_ai_role_description_1"
        - name: AI_ROLE2
          value: "your_ai_role_description_2"
        - name: AI_NAME
          value: "your_ai_name"
```

Create Kubernetes secrets:

```bash
kubectl create secret generic brobot-secrets \
  --from-literal=DISCORD_TOKEN=your_discord_bot_token \
  --from-literal=OPENAI_API_KEY=your_openai_api_key
```

Deploy to Kubernetes:

```bash
kubectl apply -f brobot-deployment.yaml
```

## Usage

- Mention the bot by name or send a direct message to interact.
- Use provided slash commands to manage allowed channels.

## Contributing

Feel free to contribute by opening issues or submitting pull requests.

## License

This project is licensed under the MIT License.

