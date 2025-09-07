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
    gchat_announcements_url = os.environ.get('GOOGLE_CHAT_ANNOUNCEMENTS_WEBHOOK_URL')
    gchat_general_url = os.environ.get('GOOGLE_CHAT_GENERAL_WEBHOOK_URL')
    
    if not all([slack_signing_secret, gchat_announcements_url, gchat_general_url]):
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
        
        # Handle URL verification challenge
        if event_data.get('type') == 'url_verification':
            return {
                'statusCode': 200,
                'body': event_data.get('challenge', '')
            }
        
        # Handle event callbacks
        if event_data.get('type') == 'event_callback':
            event = event_data.get('event', {})
            
            # Only process message events (not reactions, etc.)
            if event.get('type') == 'message' and event.get('subtype') is None:
                # Get channel info
                channel_id = event.get('channel')
                channel_name = get_channel_name(channel_id, event_data)

                # Only forward messages from #general and #announcements
                # For initial setup, we'll forward from any channel and log the channel ID
                # so you can configure the channel mappings
                if channel_name in ['general', 'announcements'] or channel_name == 'unknown':
                    user_id = event.get('user')
                    message_text = event.get('text', '')

                    # Skip empty messages
                    if not message_text.strip():
                        return {
                            'statusCode': 200,
                            'body': json.dumps({'status': 'skipped_empty_message'})
                        }

                    # Get user display name
                    user_name = get_user_display_name(user_id, event_data)

                    # Log channel info for setup purposes
                    print(f"Message from channel {channel_id} ({channel_name}): {user_name}: {message_text[:50]}...")

                    # Determine which webhook to use
                    if channel_name == 'announcements':
                        webhook_url = gchat_announcements_url
                    elif channel_name == 'general':
                        webhook_url = gchat_general_url
                    else:
                        # For unknown channels, use general webhook and log
                        webhook_url = gchat_general_url
                        print(f"Unknown channel {channel_id}, using general webhook")

                    # Forward to Google Chat
                    forward_to_gchat(webhook_url, user_name, message_text, channel_name, channel_id)
        
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


def get_channel_name(channel_id, event_data):
    """
    Extract channel name from event data or return channel_id if not found
    """
    # Try to get from team_id and use Slack Web API (simplified approach)
    # For now, we'll use a mapping approach since we only care about 2 channels

    # You would typically store these mappings or use Slack Web API
    # For this implementation, we'll need to configure these channel IDs
    # after setting up the Slack app

    # Common channel names to IDs (you'll need to update these)
    channel_mappings = {
        # Add your actual channel IDs here after Slack app setup
        # 'C1234567890': 'general',
        # 'C0987654321': 'announcements'
    }

    return channel_mappings.get(channel_id, 'unknown')


def get_user_display_name(user_id, event_data):
    """
    Get user display name from event data or return user_id if not found
    """
    # Try to get user info from the event data first
    # Slack sometimes includes user info in the event

    # For now, return a formatted user ID
    # In production, you'd use Slack Web API: users.info
    return f"User-{user_id[-4:]}"  # Show last 4 chars of user ID


def forward_to_gchat(webhook_url, user_name, message_text, channel_name, channel_id=None):
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
