import facebook
from facebookads.api import FacebookAdsApi
from facebookads.adobjects.adaccount import AdAccount
from facebookads.adobjects.campaign import Campaign
from facebookads.adobjects.adset import AdSet
from facebookads.adobjects.adcreative import AdCreative
from facebookads.adobjects.adcreativeobjectstoryspec import AdCreativeObjectStorySpec
from facebookads.adobjects.ad import Ad
from facebookads import adobjects

import requests
import json
import datetime
import shelve

from credentials import credentials
from config import pages_id, page_names, pages_actual_names, accounts_ids, slack_tokens, params, fields

from sentimentanalyzer import sentimentAnalyzer
from error_handling import exception_catcher
from send_message_to_slack import send_message_to_slack


slack_token =  slack_tokens['@jonathan']

app_id = credentials['app_id']
app_secret = credentials['app_secret']
access_token = credentials['access_token']
client_token= credentials['client_token']

FacebookAdsApi.init(app_id=app_id, app_secret=app_secret, access_token=access_token,api_version="v3.0")
account = AdAccount(accounts_ids['live_booker'])
graph = facebook.GraphAPI(access_token=access_token, version = 3.0)




ad_ids_list = []
def ad_ids_fetcher(account,params,fields):
    """
    fetches ad ids from active campaigns for the selected ad account

    """
    account = AdAccount(account)
    try:
        adset_insights = account.get_insights(fields=fields, params=params)
    except Exception:
        exception_catcher('/facebook_ads_comments_analyzer/')
        
    ad_ids_list = [insight['ad_id'] for insight in adset_insights]

    return ad_ids_list


def page_id_post_id_fetcher(ad_id):
    """
    pass ad_id to fetch page_id_post_id which is needed to fetch the comments from a Facebook post or ad
    """
    try:
        s = requests.get('https://graph.facebook.com/v3.1/'+ ad_id + '?fields=creative{effective_object_story_id}&access_token=' + access_token)
    except Exception:
        exception_catcher('/facebook_ads_comments_analyzer/')
    s = s.json()
    print(s)
    print(s['creative']['effective_object_story_id'])
    return s['creative']['effective_object_story_id']


def comment_fetcher(page_id_post_id):
    """
    pass page-id_post-id to fetch comments
    """
    try:
        comments = graph.get_connections(id=page_id_post_id,connection_name='comments')
    except Exception:
        exception_catcher('/facebook_ads_comments_analyzer/')

    return comments

def ad_comments_sentiment_analyzer(account):
    """
    main function, gets ad comments and sends them through sentiment analysis to parse them and check if they're 
    negative comments if they haven't been parsed already
    """
    already_parsed = shelve.open('already_parsed')

    ad_ids = ad_ids_fetcher(account=account,params=params,fields=fields)
    number_of_comments = 0

    for ad in ad_ids:
        page_id_post_id = page_id_post_id_fetcher(ad)
        comments = comment_fetcher(page_id_post_id)
        for comment in comments['data']:
            number_of_comments += 1
            if comment['id'] not in already_parsed.keys():
                already_parsed[comment['id']] = True
                message = comment['message']
                try:
                    snt = sentimentAnalyzer(message)
                    if snt['compound'] < 0:
                        print(message)
                        print(snt)
                        post_id = page_id_post_id.split('_')[1]
                        comment_id = comment['id'].split('_')[1]
                        link_to_comment = 'https://www.facebook.com/' + page_names[account] + '/posts/' + post_id + '?comment_id=' + comment_id
                        page_name = pages_actual_names[account]
                        send_message_to_slack(slack_token, page_name, message,link_to_comment)
                except Exception:
                    exception_catcher('/facebook_ads_comments_analyzer/')
    print('Number of comments analyzed: ' + str(number_of_comments))
    already_parsed.close()

def fetch_ads_comments(list_of_ad_accounts):
    for account_iterated in list_of_ad_accounts:
        ad_comments_sentiment_analyzer(accounts_ids[account_iterated])
