# Slack to Google Chat Bridge

A serverless bot that forwards messages from Slack channels (#general and #announcements) to Google Chat using webhooks. Built for deployment on Vercel.

## Features

- ✅ Forwards messages from Slack #general and #announcements channels to Google Chat
- ✅ Includes user display names in forwarded messages
- ✅ Adds informational cards with Slack invite links
- ✅ Verifies Slack signatures for security
- ✅ No database required - forwards messages on the fly
- ✅ Serverless deployment on Vercel

## Setup

### 1. Slack App Configuration

1. Create a new Slack app at https://api.slack.com/apps
2. Go to "Event Subscriptions" and enable events
3. Set the Request URL to: `https://your-vercel-app.vercel.app/api/events`
4. Subscribe to the following bot events:
   - `message.channels` (to receive messages from public channels)
5. Go to "OAuth & Permissions" and install the app to your workspace
6. Copy the "Bot User OAuth Token" and "Signing Secret"

### 2. Google Chat Webhooks

1. Create Google Chat webhooks for your spaces
2. Copy the webhook URLs for both #general and #announcements equivalent spaces

### 3. Environment Variables

Create a `.env` file (for local development) or set environment variables in Vercel:

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
GOOGLE_CHAT_GENERAL_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/...
GOOGLE_CHAT_ANNOUNCEMENTS_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/...
```

### 4. Deploy to Vercel

#### Option A: Using Vercel CLI
```bash
npm i -g vercel
vercel
```

#### Option B: Using GitHub Integration
1. Push this repository to GitHub
2. Connect your GitHub repo to Vercel
3. Set environment variables in Vercel dashboard
4. Deploy

### 5. Set Environment Variables in Vercel

In your Vercel dashboard, go to Settings > Environment Variables and add:

- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`
- `GOOGLE_CHAT_GENERAL_WEBHOOK_URL`
- `GOOGLE_CHAT_ANNOUNCEMENTS_WEBHOOK_URL`

### 6. Test the Bot

After deployment, send a test message in #general and #announcements on Slack. The bot will automatically:
- Fetch the channel name using the Slack API
- Get the user's display name
- Forward messages only from #general and #announcements channels to the respective Google Chat webhooks

## How It Works

1. Slack sends events to `/api/events` endpoint when messages are posted
2. The bot verifies the request signature for security
3. If the message is from #general or #announcements, it forwards to the appropriate Google Chat webhook
4. Messages are formatted as: "User Name: message content" with an informational card below

## File Structure

```
├── api/
│   └── events.py          # Main serverless function
├── .env                   # Environment variables (local only)
├── .gitignore            # Git ignore file
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── README.md            # This file
```

## Security

- Slack request signatures are verified using HMAC-SHA256
- Environment variables are used for all sensitive data
- No persistent storage or database required

## Limitations

- Only forwards text messages (not files, images, etc.)
- Only forwards from channels named exactly "general" and "announcements"

## Contributing

Feel free to submit issues and enhancement requests!
