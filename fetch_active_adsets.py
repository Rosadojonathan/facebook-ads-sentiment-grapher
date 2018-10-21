import facebook
from facebookads.api import FacebookAdsApi
from facebookads.adobjects.adaccount import AdAccount
from facebookads.adobjects.campaign import Campaign
from facebookads.adobjects.adset import AdSet
from facebookads.adobjects.adcreative import AdCreative
from facebookads.adobjects.adcreativeobjectstoryspec import AdCreativeObjectStorySpec
from facebookads.adobjects.ad import Ad
from facebookads import adobjects
import dataset

import requests
import json
import datetime
import shelve
import pprint

from credentials import credentials
from config import pages_id, page_names, pages_actual_names, accounts_ids, slack_tokens, params, fields

from sentimentanalyzer import sentimentAnalyzer
from error_handling import exception_catcher
from send_message_to_slack import send_message_to_slack
#from sentiment_grapher import sentiment_grapher

pp = pprint.PrettyPrinter(indent=4)

slack_token =  slack_tokens['@jonathan']

app_id = credentials['app_id']
app_secret = credentials['app_secret']
access_token = credentials['access_token']
client_token= credentials['client_token']

FacebookAdsApi.init(app_id=app_id, app_secret=app_secret, access_token=access_token,api_version="v3.0")
#account = AdAccount(accounts_ids['live_booker'])
graph = facebook.GraphAPI(access_token=access_token, version = 3.0)

db = dataset.connect("sqlite:///adcomments.db")
table = db["adcomments"]

adset_name_ad_id = {}
def adset_comment_fetcher(account,params,fields):
    """
    fetches ad ids and corresponding adset name from active campaigns for the selected ad account
    """
    account = AdAccount(account)

    adset_insights = account.get_insights(fields=fields, params=params)        
    for insight in adset_insights:
       adset_name_ad_id[insight['adset_name']] = insight['ad_id']
    return adset_name_ad_id 

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

def insert_to_table(adset_name, number_neg_comments, number_pos_comments, number_neutral_comments, negative_messages_list, positive_messages_list):
    """
    checks if number of polarity comments doesn't already exist in db, and aggregates them 
    otherwise creates new row
    """
    sql_adset_name = adset_name.replace(' ', '_')
    db_comments = None
    try:
        db_comments = db.query(f"SELECT number_neg_comments, number_pos_comments, number_neutral_comments FROM adcomments WHERE adset_name = '{sql_adset_name}'")
    except Exception as e:
        print(e)

    db_neg_comments = db_pos_comments = db_neutral_comments = 0
    if db_comments:
        for i in db_comments:
            db_neg_comments = i['number_neg_comments']
            print(db_neg_comments)
            db_pos_comments = i['number_pos_comments']
            db_neutral_comments = i['number_neutral_comments']
    
    db_neg_messages_list = []
    db_pos_messages_list = []
    try:
        db_messages_list_query = db.query(f"SELECT negative_messages_list, positive_messages_list FROM adcomments WHERE adset_name = '{sql_adset_name}'")
        for i in db_messages_list_query:
            db_neg_messages_list.extend(i["negative_messages_list"])
            db_pos_messages_list.extend(i["positive_messages_list"])
    except Exception as e:
        print(e)
        

    negative_messages_list.extend(db_neg_messages_list)    
    positive_messages_list.extend(db_pos_messages_list)
    print(f'db_neg_comments = {db_neg_comments}')
    print(f'number_neg_comments = {number_neg_comments}')
    data = dict(adset_name = sql_adset_name, number_neg_comments= db_neg_comments + number_neg_comments, number_pos_comments=db_pos_comments + number_pos_comments, number_neutral_comments= db_neutral_comments + number_neutral_comments, negative_messages_list = str(negative_messages_list), positive_messages_list = str(positive_messages_list))
    table.upsert(data, ['adset_name'])



def ad_comments_sentiment_analyzer(account):
    """
    main function, gets ad comments and sends them through sentiment analysis to parse them and stores number of comments according to polarity in a database
    if they haven't been parsed already
    """
    already_parsed = shelve.open('already_parsed')

    adset_comment_fetcher(account,params,fields).values()
    number_of_comments = 0

    for adset_name, ad_id in adset_name_ad_id.items():
        number_neg_comments = 0
        number_pos_comments = 0
        number_neutral_comments = 0
        negative_messages_list = []
        positive_messages_list = []

        page_id_post_id = page_id_post_id_fetcher(ad_id)
        comments = comment_fetcher(page_id_post_id)
        for comment in comments['data']:
            number_of_comments += 1
            if comment['id'] not in already_parsed.keys():
                already_parsed[comment['id']] = True
                message = comment['message']

                snt = sentimentAnalyzer(message)
                if snt['compound'] < -0.2:
                    number_neg_comments += 1
                    negative_messages_list.append(message)

                if snt['compound'] > 0.2:
                    number_pos_comments += 1
                    positive_messages_list.append(message)
                else:
                    number_neutral_comments += 1
        print(negative_messages_list)
        insert_to_table(adset_name, number_neg_comments, number_pos_comments, number_neutral_comments,negative_messages_list,positive_messages_list)                
    print('Number of comments analyzed: ' + str(number_of_comments))
    already_parsed.close()


def fetch_ads_comments(list_of_ad_accounts):
    for account_iterated in list_of_ad_accounts:
        print(account_iterated)
        ad_comments_sentiment_analyzer(accounts_ids[account_iterated])

        
#fetch_ads_comments(['live_booker'])
