import json
import requests
from urllib import request, parse


def send_message_to_slack(slack_token,page_name, text,link):
    post = {
                "attachments": [
                    {
                        "text":"*{}* : {} \n *Lien*: {}\n\n".format(page_name, text,link),
                        "mrkdwn_in":["text"],
                        
                        }
                    ]
                }

    try:
        json_data  = json.dumps(post)
        req = request.Request(slack_token, data = json_data.encode('ascii'),headers={'Content-Type':'application/json'})
        resp = request.urlopen(req)
    except Exception as em:
        print("Exception: " + str(em))
