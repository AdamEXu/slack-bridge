from json import dumps
from httplib2 import Http
import time

url = "GOOGLE_CHAT_WEBHOOK_URL"
app_message = {
    "text": "Message",
    "cards": [
        {
            "header": {
                "title": "Join Pinewood Robotics on Slack to join the conversation!",
                "subtitle": "This is a bridged message from Slack. You should join the Slack workspace below for future access. This bridge is only temporary for now.",
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
message_headers = {"Content-Type": "application/json; charset=UTF-8"}
http_obj = Http()
response = http_obj.request(
    uri=url,
    method="POST",
    headers=message_headers,
    body=dumps(app_message),
)
print(response.status)
