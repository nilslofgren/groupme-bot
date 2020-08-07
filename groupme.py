from groupy.client import Client
from groupy.api.messages import Leaderboard
from groupy.api.bots import Bots
from groupy.api.messages import Messages

import requests
import json
import sched
import time
import pandas as pd
import matplotlib.pyplot as plt
import os


def determine_target(message, botID):
    msgText = message.text.lower()
    msgList = msgText.split()
    if msgList[1] == 'get-news':
        get_news(msgList[2], botID)
    elif msgList[1] == 'get-summary':
        get_summary(botID)
    elif msgList[1] == 'get-trending':
        get_trending(botID)
    elif msgList[1] == 'get-chart':
        get_chart(msgList[2], msgList[3], msgList[4], botID)
    elif msgList[1] == 'help':
       Bots.post(bots, botID, 'The commands are:')
       Bots.post(bots, botID, '1. get-news <ticker>\n2. get-summary\n3. get-trending')
       Bots.post(bots, botID, '4. get-chart <ticker> <interval> <range>, where interval can be 1m|2m|5m|15m|60m|1d '
                              'and range can be 1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max')
    else:
        Bots.post(bots, botID, 'I dont recognize your command')
        Bots.post(bots, botID, 'Always start your command with @Stonks so I know you are talking to me.')


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


def get_chart(ticker, interval, range, botID):
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-chart"
    querystring = {"interval": interval, "region": "US", "symbol": ticker, "lang": "en", "range": range}
    response = requests.request("GET", url, headers=headers, params=querystring)
    jsonObj = json.loads(response.text)
    timestamp = jsonObj['chart']['result'][0]['timestamp']                          # x : over-time
    index = 0
    if interval == '1d':
        for ts in timestamp:
            timestamp[index] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
            timestamp[index] = timestamp[index][0:10]
            index = index + 1
    else:
        for ts in timestamp:
            timestamp[index] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
            timestamp[index] = timestamp[index][10:]
            index = index + 1
    openPrices = jsonObj['chart']['result'][0]['indicators']['quote'][0]['open']    # y : dollar value
    d = {'times': timestamp, 'prices': openPrices}
    df = pd.DataFrame(data=d)
    df.plot(x='times', y='prices')
    plt.title('Price trend of ' + ticker.upper() + ' over ' + range + ' every ' + interval)
    plt.xlabel('Time')
    plt.ylabel('Price in USD')
    t = str(time.time())
    plt.savefig(t + 'chart.png')
    path = '**' + t + 'chart.png'
    imgPath = open(path, 'rb').read()
    payload = {"X-Access-Token": token, "Content-Type": "image/png"}
    r = requests.post(url='https://image.groupme.com/pictures', data=imgPath, headers=payload)
    rJSON = json.loads(r.text)
    imgUrl = rJSON['payload']['url']
    post_params = {'bot_id': botID,
                   'text': 'attachment incoming',
                   'attachments': [
                       {
                           'type': 'image',
                           'picture-url': t + 'chart.png'
                       }
                   ]
                   }
    post_data = {'text': 'Here is your requested chart', 'picture_url': imgUrl}
    requests.post('https://api.groupme.com/v3/bots/post', params=post_params, data=post_data)
    if os.path.isfile(path):
        os.remove(path)


def check_mention():
    for message in messageList:
        # print(message)
        if message.text.find('@Stonks') == 0:
            determine_target(message, botID)


token = "**"

client = Client.from_token(token)
session = client.session
bots = Bots(session)
headers = {
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
    'x-rapidapi-key': "***"
}

# bot 1 = test
# bot 2 = real
# get_chart('TSLA', '5m', '1d', '1')
bot = 2
run = True
botIDs = ['**', '**']

if bot == 1:
    messageManager = Messages(session, '**')
    botID = botIDs[0]
else:
    messageManager = Messages(session, '**')
    botID = botIDs[1]

while run:
    messageList = messageManager.list(limit=1)
    if messageList[0].data['text'].find('@Stonks stop') == 0:
        run = False
        break
    else:
        check_mention()
    time.sleep(3)
