import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, Event
import pandas as pd
import sqlite3
from functools import reduce
import ast


from fetch_active_adsets import fetch_ads_comments



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

conn = sqlite3.connect('adcomments.db',check_same_thread=False)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


df = pd.read_sql_query('SELECT * FROM adcomments', conn)

def fetch_latest_comments():
    print('fetching latest comments')
    conn = sqlite3.connect('adcomments.db',check_same_thread=False)
    fetch_ads_comments(['live_booker'])
    df = pd.read_sql_query('SELECT * FROM adcomments', conn)
    print('latest comments fetched')

dropdown_list = []
i = 1 
def get_dropdown_list(df):
    for index, row in df.iterrows():
        dropdown_list.append({'label':row['adset_name'].replace('_',' '),'value':index + 1})
    print(dropdown_list)
    return dropdown_list

polarity_counts_list = []
def get_polarity_counts(df):
    for index, row in df.iterrows():
        polarity_counts_list.append([row['number_neg_comments'], row['number_pos_comments'], row['number_neutral_comments']])
    print(polarity_counts_list)
    return polarity_counts_list

def fetch_negative_comments(df, value):
    sentences = df.iloc[value -1]["negative_messages_list"]
    print(sentences)
    neg_comments_list = ast.literal_eval(sentences)
    return neg_comments_list

def fetch_positive_comments(df, value):
    sentences = df.iloc[value -1]['positive_messages_list']
    pos_comments_list = ast.literal_eval(sentences)
    return pos_comments_list


"""
App layout
"""
# html.Button('Fetch latest comments', id='fetch-comments-button',type='submit',style={"background-color":"rgb(119,136,153)", "color":"white", "margin-top":"15px",}),



app.layout = html.Div(children=[
    html.Div(id='target',
    className='container'),
    html.H1(children="Ads Sentiment Analyzer",className='container',style={"margin-top":"25px", "margin-bottom":"25px"}),
    html.Div(
        dcc.Dropdown(
        id='ad-dropdown',
        options=get_dropdown_list(df),
        style={'margin-bottom':'35px',"margin-left":"auto","margin-right":"auto","width":"1000px"},
        value=1)),  
    html.Div(id='output',className='container'),
    
    ])


"""
App callbacks
"""

@app.callback(
    Output(component_id='output', component_property='children'), 
    [Input(component_id='ad-dropdown', component_property='value')])
def update_graph(value):
    data = [
        {
            'values': get_polarity_counts(df)[int(value)-1],
            'type':'pie',
            "marker": {
                "colors": ['rgb(178,34,34)','rgb(107,142,35)','rgb(119,136,153)']
            },
            "hole": .5,
            "labels":['Negative comments','Positive comments','Neutral comments'],
            "textfont": {
                "size":18
            },
            'textposition':'inside',

        },
    ]

    graphs = []

    graphs.append(html.Div([
        dcc.Graph(
            id='graph',
            figure={
                'data': data,
                'layout': {
                    'margin': {
                        'l': 30,
                        'r': 0,
                        'b': 30,
                        't': 0
                    },
                "annotations": [
                    {
                        "font": {
                            "size": 20
                        },
                        "showarrow": False,
                        "text": str(reduce(lambda x, y: x + y, get_polarity_counts(df)[int(value)-1])) + " Comments",
                        }
                    ]
                    }
                    }
                )
    ]))

    for i in range(len(fetch_negative_comments(df, value)[:3])):
        graphs.append(html.Div(children=[
            html.P(
                id="text-area-neg",
                children=fetch_negative_comments(df,value)[i],
                style={ 
                "color":"rgb(178,34,34)"     
                    },

            )
        ]))
    for i in range(len(fetch_positive_comments(df, value)[:3])):
            graphs.append(html.Div(children=[
                html.P(
                    id="text-area-pos",
                    children=fetch_positive_comments(df,value)[i],
                    style={ 
                    "color":"rgb(107,142,35)"     
                        },

                )
            ]))

   
    return html.Div(graphs)


# @app.callback(Output('target', 'children'), [Input('fetch-comments-button','n_clicks')], [State('fetch-comments-button', 'value')], [Event('fetch-comments-button', 'click')])
# def on_click(n_clicks,input1):
#     if n_clicks is None:
#         nclicks_bt1 = 0
#     else:
#         return fetch_latest_comments()


if __name__ == '__main__':
    app.run_server(debug=True)
