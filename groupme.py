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


token = "dc68b2d06ca50138d774127c6b6f91ba"

client = Client.from_token(token)
session = client.session
bots = Bots(session)
headers = {
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
    'x-rapidapi-key': "9d9995763fmsha7e1c3480b39eb4p1aa3dajsn05a7c3170e58"
}

# bot 1 = test
# bot 2 = real
bot = 1
run = True
botIDs = ['0fe8a6ce7269fcb58fc8be902a', '729b1b67487ce276aacb8d693d']
if bot == 1:
    messageManager = Messages(session, '60550508')
    botID = botIDs[0]
else:
    messageManager = Messages(session, '59433460')
    botID = botIDs[1]

while run:
    messageList = messageManager.list(limit=1)
    if messageList[0].data['text'].find('@Stonks stop') == 0:
        run = False
        break
    else:
        check_mention()
    time.sleep(3)
# get_trending()
# get_summary()

# print(messageText)
#
# for message in messageText:
#     if message.find('@Test') == 0:
#         Bots.post(bots, '0fe8a6ce7269fcb58fc8be902a', 'You mentioned Me!', attachments=None)

# line#s.append(line.split(" "))
# f = open("dream1line", "r")
# lines = []
# for line in f:
# line.strip()
# new_line = " ".join(line.splitlines())
#    lines += line.split(" ")

# for word in lines:
#    print(word)
#    chats.messages.DirectMessages(session, '28967374').create(word)

# Code to return top liked messages for the month
# group = '59433460'
# weekly_best = Leaderboard(session, group).list_day()
# print(weekly_best)
# for chat in client.chats.list_all():
#    print(chat.other_user['name'], " : ", chat.other_user['id'])

# groups = list(client.groups.list_all())

# for group in groups:
#    print(group.name, " : ", group.id)
