import os
import json
import hmac
import hashlib
from urllib.request import Request, urlopen
from urllib.error import HTTPError

def handler(request):
    """
    Vercel serverless function to handle Slack events and forward to Google Chat
    """
    
    # Only handle POST requests
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    # Get environment variables
    slack_signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
    slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
    gchat_announcements_url = os.environ.get('GOOGLE_CHAT_ANNOUNCEMENTS_WEBHOOK_URL')
    gchat_general_url = os.environ.get('GOOGLE_CHAT_GENERAL_WEBHOOK_URL')

    if not all([slack_signing_secret, slack_bot_token, gchat_announcements_url, gchat_general_url]):
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Missing required environment variables'})
        }
    
    try:
        # Get request body and headers
        body = request.get_data(as_text=True)
        timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
        signature = request.headers.get('X-Slack-Signature', '')
        
        # Verify Slack signature
        if not verify_slack_signature(slack_signing_secret, body, timestamp, signature):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid signature'})
            }
        
        # Parse the request body
        event_data = json.loads(body)
        
        # Handle URL verification challenge (required by Slack)
        if event_data.get('type') == 'url_verification':
            challenge = event_data.get('challenge', '')
            print(f"URL verification challenge received: {challenge}")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/plain'},
                'body': challenge
            }
        
        # Handle event callbacks
        if event_data.get('type') == 'event_callback':
            event = event_data.get('event', {})
            
            # Only process message events (not reactions, etc.)
            if event.get('type') == 'message' and event.get('subtype') is None:
                user_id = event.get('user')
                message_text = event.get('text', '')
                channel_id = event.get('channel')

                # Skip empty messages or bot messages
                if not message_text.strip() or not user_id:
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'status': 'skipped_empty_or_bot_message'})
                    }

                # Get channel name using Slack API
                channel_name = get_channel_name(channel_id, slack_bot_token)

                # Get user display name using Slack API
                user_name = get_user_display_name(user_id, slack_bot_token)

                # Log all messages for debugging
                print(f"Message from #{channel_name} ({channel_id}): {user_name}: {message_text[:50]}...")

                # Simple channel name based forwarding
                if channel_name == "general":
                    print("Forwarding to general Google Chat")
                    forward_to_gchat(gchat_general_url, user_name, message_text, "general")
                elif channel_name == "announcements":
                    print("Forwarding to announcements Google Chat")
                    forward_to_gchat(gchat_announcements_url, user_name, message_text, "announcements")
                else:
                    print(f"Message from #{channel_name}, not forwarding (only general and announcements are forwarded)")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def verify_slack_signature(signing_secret, body, timestamp, signature):
    """
    Verify that the request is from Slack using the signing secret
    """
    if not all([signing_secret, body, timestamp, signature]):
        return False
    
    # Create the signature base string
    sig_basestring = f"v0:{timestamp}:{body}"
    
    # Create the expected signature
    expected_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)





def get_channel_name(channel_id, slack_bot_token):
    """
    Get channel name using Slack Web API
    """
    try:
        url = f"https://slack.com/api/conversations.info?channel={channel_id}"
        headers = {
            'Authorization': f'Bearer {slack_bot_token}',
            'Content-Type': 'application/json'
        }

        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode())

        if data.get('ok'):
            return data.get('channel', {}).get('name', 'unknown')
        else:
            print(f"Error getting channel info: {data.get('error')}")
            return 'unknown'

    except Exception as e:
        print(f"Error fetching channel name: {e}")
        return 'unknown'


def get_user_display_name(user_id, slack_bot_token):
    """
    Get user display name using Slack Web API
    """
    try:
        url = f"https://slack.com/api/users.info?user={user_id}"
        headers = {
            'Authorization': f'Bearer {slack_bot_token}',
            'Content-Type': 'application/json'
        }

        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode())

        if data.get('ok'):
            user = data.get('user', {})
            # Try to get display name, real name, or fall back to username
            display_name = (user.get('profile', {}).get('display_name') or
                          user.get('real_name') or
                          user.get('name') or
                          f"User-{user_id[-4:]}")
            return display_name
        else:
            print(f"Error getting user info: {data.get('error')}")
            return f"User-{user_id[-4:]}"

    except Exception as e:
        print(f"Error fetching user name: {e}")
        return f"User-{user_id[-4:]}"


def forward_to_gchat(webhook_url, user_name, message_text, channel_name):
    """
    Forward the message to Google Chat using the webhook
    """
    # Create the message payload
    gchat_message = {
        "text": f"{user_name}: {message_text}",
        "cards": [
            {
                "header": {
                    "title": "Join Pinewood Robotics on Slack to join the conversation!",
                    "subtitle": f"This is a bridged message from #{channel_name} on Slack. You should join the Slack workspace below for future access. This bridge is only temporary for now.",
                    "imageUrl": "https://mp-cdn.elgato.com/media/01a11cf1-c0b5-46f0-9def-1dbb8d39d3e2/Slack-thumbnail-optimized-7a3bded9-c41e-4bdf-8ba0-5367c7dc310d.jpeg",
                    "imageStyle": "IMAGE",
                },
                "sections": [
                    {
                        "widgets": [
                            {
                                "buttons": [
                                    {
                                        "textButton": {
                                            "text": "Accept your Slack invite",
                                            "onClick": {
                                                "openLink": {
                                                    "url": "https://join.slack.com/t/pinewoodroboticsgroup/shared_invite/zt-3coxmq6ie-02eRfEGLq0uHFRNAhMpeZA"
                                                }
                                            },
                                        }
                                    }
                                ]
                            },
                        ]
                    }
                ],
            }
        ],
    }
    
    # Send to Google Chat
    try:
        req = Request(
            webhook_url,
            data=json.dumps(gchat_message).encode('utf-8'),
            headers={'Content-Type': 'application/json; charset=UTF-8'}
        )
        
        with urlopen(req) as response:
            print(f"Message forwarded to Google Chat. Status: {response.status}")
            
    except HTTPError as e:
        print(f"Error forwarding to Google Chat: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
