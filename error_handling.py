from urllib import request
from config import slack_tokens
import sys, traceback

import json

link_to_logs = "https://elk.maestro-technology.com/app/kibana#/discover?_g=(refreshInterval:(display:'5%20seconds',pause:!f,section:1,value:5000),time:(from:now-4h,mode:quick,to:now))&_a=(columns:!(message),index:'logstash-*',interval:auto,query:(query_string:(analyze_wildcard:!t,query:%22mk-tools_emailhooks%22)),sort:!('@timestamp',desc))";
#SLACK_TOKEN = "https://hooks.slack.com/services/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" # @jonathan




def send_slack_message(message, channel, testing):
    if not testing:
        print('Not testing')
        message['channel'] = channel
        print(message)
        try:
            json_data  = json.dumps(message)
            print()
            req = request.Request(slack_tokens['#mk_tech_errors'], data = json_data.encode('ascii'),headers={'Content-Type':'application/json'})
            resp = request.urlopen(req)
        except Exception as em:
            print("Exception: " + str(em))


def send_error_to_slack(error,error_route, testing=False):
    
    message =  {
                    "attachments": [
                        {
                            "fallback": "Erreur avec le Parser de commentaires de Facebook Ads . <{}>|Consulter les logs sur ELK>".format(link_to_logs),
                            "pretext": "Une erreur est survenue avec le Parser de commentaires de Facebook Ads cc <@jonathan>",
                            "color":"danger",
                            "author_name":"Cliquer pour consulter les logs sur ELK",
                            "author_link": link_to_logs,
                            "title":"Message de l'erreur",
                            "text":"{0} - <{1}>| Consulter les logs complets".format(error,link_to_logs),
                            "fields":[
                                {
                                    "title":"Route à l'origine du message",
                                    "value":"{}".format(error_route),
                                    "short":False,
                                },
                            ],
                            },
                            {
                                "color":"warning",
                                "fields":[
                                    {
                                        "title":"Informations supplémentaires",
                                        "value":"``` {} ```".format(error),
                                        "short":False,
                                    }
                                ]
                            }
                        ]
                    }
    send_slack_message(message,"#mk_tech_errors",testing)

def exception_catcher(route):

    print('Sending Exception to Slack')
    print('-'*50)
    type_, value_, traceback_ = sys.exc_info()
    ex = traceback.format_exception(type_, value_, traceback_)
    traceback.print_exc(file=sys.stdout)
    print('-'*50)
        
    send_error_to_slack(ex,route)