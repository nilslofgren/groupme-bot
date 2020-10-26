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


def determine_target(message):
    msgText = message.text.lower()
    msgList = msgText.split()
    if msgList[1] == 'get-news':
        get_news(msgList[2])
    elif msgList[1] == 'get-summary':
        get_summary(message)
    elif msgList[1] == 'get-trending':
        get_trending()
    elif msgList[1] == 'get-chart':
        get_chart(msgList[2], msgList[3], msgList[4])
    elif msgList[1] == 'add-ticker':
        if int(msgList[3]) >= 1:
            add_ticker(message, msgList[2], msgList[3])
    elif msgList[1] == 'remove-ticker':
        remove_ticker(message, msgList[2])
    elif msgList[1] == 'help':
        Bots.post(bots, botID, 'The commands are:')
        Bots.post(bots, botID, '1. get-news <ticker>\n2. get-summary\n3. get-trending')
        Bots.post(bots, botID, '4. get-chart <ticker> <interval> <range>, where interval can be 1m|2m|5m|15m|60m|1d '
                               'and range can be 1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max')
    else:
        Bots.post(bots, botID, 'I dont recognize your command')
        Bots.post(bots, botID, 'Use "@Stonks help" for a list of my commands.')


def get_trending():
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


def get_summary(msg):
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-summary"
    idx = indexDict.get(msg.name)
    tickers = memList[idx].get_stocks()
    price = 0.0

    for ticker in tickers:
        querystring = {"region": "US", "symbol": ticker}
        response = requests.request("GET", url, headers=headers, params=querystring)
        jsonObj = json.loads(response.text)
        marketPrice = jsonObj['price']['regularMarketPrice']['raw']
        localprice = float(marketPrice) * float(memList[idx].stockDict[ticker])
        price = price + localprice
        message = ticker + ' Stock price: $' + "{:.2f}".format(float(marketPrice)) + ' * Number of shares held: ' + "{:.2f}".format(float(memList[idx].stockDict[ticker])) + ' = $' + "{:.2f}".format(float(localprice))
        Bots.post(bots, botID, message, attachments=None)
    message = 'Total Portfolio Value: $' + "{:.2f}".format(float(price))
    memList[idx].set_value(price)
    Bots.post(bots, botID, message, attachments=None)


def get_news(ticker):
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


def get_chart(ticker, interval, over_time):
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-chart"
    querystring = {"interval": interval, "region": "US", "symbol": ticker, "lang": "en", "range": over_time}
    response = requests.request("GET", url, headers=headers, params=querystring)
    jsonObj = json.loads(response.text)
    timestamp = jsonObj['chart']['result'][0]['timestamp']  # x : over-time
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
    openPrices = jsonObj['chart']['result'][0]['indicators']['quote'][0]['open']  # y : dollar value
    d = {'times': timestamp, 'prices': openPrices}
    df = pd.DataFrame(data=d)
    df.plot(x='times', y='prices')
    plt.title('Price trend of ' + ticker.upper() + ' over ' + over_time + ' every ' + interval)
    plt.xlabel('Time')
    plt.ylabel('Price in USD')
    t = str(time.time())
    plt.savefig(t + 'chart.png')
    path = 'C:\\file-path-here' + t + 'chart.png'
    imgPath = open(path, 'rb').read()
    payload = {"X-Access-Token": token, "Content-Type": "image/png"}
    r = requests.post(url='https://image.groupme.com/pictures', data=imgPath, headers=payload)
    rJSON = json.loads(r.text)
    imgUrl = rJSON['payload']['url']
    post_params = {'bot_id': botID,
                   'text': '',
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
        if message.text.find('@Stonks') == 0:
            determine_target(message)


def add_ticker(msg, ticker, amt):
    idx = indexDict.get(msg.name)
    memList[idx].add_stock(ticker, amt)
    Bots.post(bots, botID, 'Ticker added successfully! Here is your updated portfolio:', attachments=None)
    for key in sorted(memList[idx].stockDict):
        port = 'Stock: ' + key.upper() + ' Number of shares held: ' + memList[idx].stockDict[key]
        Bots.post(bots, botID, port, attachments=None)


def remove_ticker(msg, ticker):
    idx = indexDict.get(msg.name)
    memList[idx].remove_stock(ticker)
    Bots.post(bots, botID, 'Ticker removed successfully! Here is your updated portfolio:', attachments=None)
    for key in sorted(memList[idx].stockDict):
        port = 'Stock: ' + key.upper() + ' Number of shares held: ' + memList[idx].stockDict[key]
        Bots.post(bots, botID, port, attachments=None)


class Portfolio:
    id = ''
    name = ''
    stocks = []
    stockDict = {}
    totalValue = 0

    def __init__(self, identity):
        self.id = identity

    def add_stock(self, ticker, amt):
        self.stocks.append(ticker)
        self.stockDict[ticker] = amt

    def remove_stock(self, ticker):
        self.stocks.remove(ticker)
        self.stockDict.pop(ticker)

    def change_stock(self, ticker, amt):
        self.stockDict[ticker] = amt

    def get_stocks(self):
        return self.stocks

    def get_stockDict(self):
        return self.stockDict

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_value(self):
        return self.totalValue

    def set_value(self, value):
        self.totalValue = value


token = "*"

client = Client.from_token(token)
session = client.session
bots = Bots(session)
headers = {
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
    'x-rapidapi-key': "*"
}

# bot 0 = test
# bot 1 = real
bot = 0
run = True
botIDs = ['*', '*']
groupIDs = ['*', '*']
index = 0
indexDict = {}

members = client.groups.get(groupIDs[bot]).members
messageManager = Messages(session, groupIDs[bot])
botID = botIDs[bot]

memList = list()
for member in members:
    memList.append(Portfolio(member.id))
    memList[index].name = member.nickname
    indexDict[member.nickname] = index
    index = index + 1

tickersDict = {}

while run:
    messageList = messageManager.list(limit=1)
    if messageList[0].data['text'].find('@Stonks stop') == 0:
        run = False
        break
    else:
        check_mention()
    time.sleep(3)
