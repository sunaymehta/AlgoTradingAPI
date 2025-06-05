from fyers_apiv3 import fyersModel
import json
import time
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io
from datetime import datetime, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta
import Functions as F

# Opening JSON file
with open('../Instructions.json') as json_file:
    instructions = json.load(json_file)
# Opening JSON file
with open('../data.json') as json_file:
    data = json.load(json_file)

appId = instructions['tokens']['appId']
access_token = data['access_token']

fyers = fyersModel.FyersModel(client_id=appId, is_async=False, token=access_token, log_path="")

# DATA DUMPING CODE
# Define Data Dumping Params
with open('./DataDumpParams.json') as json_file:
    datadumpparams = json.load(json_file)

asset = datadumpparams['data']['asset']
today = datadumpparams['data']['today']
yearsofdata = datadumpparams['data']['yearsofdata']

# Override with latest market data and lookback = 1yr
# Comment out this code if manually market data date and lookback needs to be specified
today = datetime.now().strftime("%Y-%m-%d") # Latest market data
yearsofdata = 1 # Lookback variable override


#today = datetime.now().strftime('%Y-%m-%d')
ranges = F.get_date_ranges(today, yearsofdata)
print(ranges)

candles = []
for i in range(len(ranges)):
    candles += (F.DataRequest(fyers, asset, ranges[i][0], ranges[i][1]))['candles']

data_5y = {'candles': candles}

historical_data = pd.DataFrame(data_5y['candles'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
# Convert the timestamp to a readable date format
historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'], unit='s')

historical_data.to_csv('./HistoricalData/'+asset[4:] + '_'+ str(yearsofdata) + 'Y' + '.csv', index=False)

print ('Data dumped for ', asset, ' for ', yearsofdata, ' years in HistoricalData folder.')
print ('Data Range: ',ranges[0][0], ' to ', ranges[-1][-1])

