from groupy.client import Client
from groupy.api.messages import Leaderboard
from groupy.api.bots import Bots
from groupy.api.messages import Messages

import requests
import json
import sched
import time


def determine_target(message, botID):
    msgText = message.text.lower()
    msgList = msgText.split()
    if msgList[1] == 'get-news':
        get_news(msgList[2], botID)
    elif msgList[1] == 'get-summary':
        get_summary(botID)
    elif msgList[1] == 'get-trending':
        get_trending(botID)


def get_trending(botID):
    n = 0
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/get-trending-tickers"
    querystring = {"region": "US"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    jsonObj = json.loads(response.text)
    tickers = jsonObj['finance']['result'][0]['quotes']
    Bots.post(bots, botID, 'Top 5 trending stocks:', attachments=None)
    for ticker in tickers:
        if n < 5:
            ret = ticker['shortName'] + ' : $' + ticker['symbol'] + '\nOpen Price: $' + \
                  str(ticker['regularMarketPreviousClose']) + '\nCurrent Price: $' + str(ticker['regularMarketPrice']) \
                  + '\nPercent Change: ' + str(ticker['regularMarketChangePercent']) + '% '
            Bots.post(bots, botID, ret, attachments=None)
        else:
            break
        n = n + 1


def get_summary(botID):
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-summary"

    tickers = ["TSLA", "AMZN", "AAPL", "MSFT", "SAP", "JPM", "NKLA", "TWO", "BP", "DAL", "OMP", "DD"]

    for ticker in tickers:
        querystring = {"region": "US", "symbol": ticker}
        response = requests.request("GET", url, headers=headers, params=querystring)
        jsonObj = json.loads(response.text)
        openPrice = jsonObj['price']['regularMarketOpen']['fmt']
        closePrice = jsonObj['price']['regularMarketPreviousClose']['fmt']
        changePrice = jsonObj['price']['regularMarketChangePercent']['fmt']
        message = ticker + " Prev Close price: $" + openPrice + "\nCurrent price: $" + closePrice + "\nPercent Change: " + changePrice
        # print(message)
        Bots.post(bots, botID, message, attachments=None)


def get_news(ticker, botID):
    num = 0
    ticker = ticker.upper()
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/get-news"
    querystring = {"region": "US", "category": ticker}
    response = requests.request("GET", url, headers=headers, params=querystring)
    jsonObj = json.loads(response.text)
    result = jsonObj['items']['result']
    for item in result:
        if num < 3:
            Bots.post(bots, botID, item['title'] + '\n' + item['link'], attachments=None)
        else:
            break
        num = num + 1


def get_chart(ticker, botID):
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-chart"
    querystring = {"interval": "5m", "region": "US", "symbol": ticker, "lang": "en", "range": "1d"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    jsonObj = json.loads(response.text)
    closePrices = jsonObj['chart']['result'][0]['indicators']['quote'][0]['close']
    openPrices = jsonObj['chart']['result'][0]['indicators']['quote'][0]['open']


def check_mention():
    for message in messageList:
        # print(message)
        if message.text.find('@Stonks') == 0:
            determine_target(message, botID)


token = "*"

client = Client.from_token(token)
session = client.session
bots = Bots(session)
headers = {
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
    'x-rapidapi-key': "*"
}

# bot 1 = test
# bot 2 = real
bot = 1
run = True
botIDs = ['*', '**']
if bot == 1:
    messageManager = Messages(session, 'group-id')
    botID = botIDs[0]
else:
    messageManager = Messages(session, 'group-id')
    botID = botIDs[1]

while run:
    messageList = messageManager.list(limit=1)
    if messageList[0].data['text'].find('@Stonks stop') == 0:
        run = False
        break
    else:
        check_mention()
    time.sleep(3)
