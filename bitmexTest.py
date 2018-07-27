from bitmex_websocket import BitMEXWebsocket
import bitmex

API_key = 'Hb2iBFvluRqRCFs9g7e50Qxw'
API_secret = 'TTb6xMNzxTITAkyPp7TqnhM-y8sHIuhSuxvN7uSdYJcrM6mX'

# ws = BitMEXWebsocket(endpoint="https://testnet.bitmex.com/api/v1", symbol="XBTUSD", api_key=None, api_secret=None)
# print(ws.data['instrument'][0]['tickSize'])
# print(ws.get_ticker())

api = bitmex.bitmex(test=False, config=None, api_key=API_key, api_secret=API_secret)

# price = api.Quote.Quote_get(symbol="XBTUSD", reverse=True, count=1).result()
stats = api.Stats.Stats_get().result()
execHist = api.Execution.Execution_getTradeHistory().result()
position = api.Position.Position_get().result()

resources = dir(api.Position.resource)
print(resources)

print(position[0][0])

for trade in position[0][0]:
    print(trade)


print(position[0][0].get('openingQty'))


# pipeline
#   CSV -> data Object



