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

# Opening JSON file
with open('../Instructions.json') as json_file:
    instructions = json.load(json_file)
# Opening JSON file
with open('../data.json') as json_file:
    data = json.load(json_file)

appId = instructions['tokens']['appId']
access_token = data['access_token']

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=appId, token=access_token,is_async=False, log_path="")

date_from = [1381449600, 1412985600, 1444521600, 1476144000, 1507680000, 
 1539216000, 1570752000, 1602374400, 1633910400, 1665446400, 
 1696982400]

date_to = [1412899200, 1444435200, 1476057600, 1507593600, 1539129600, 
 1570665600, 1602288000, 1633824000, 1665360000, 1696896000, 
 1728518400]

x= 0
y= 0

fyers = fyersModel.FyersModel(client_id=appId, token=access_token)

for i in range(len(date_from)):
    data = {
    "symbol": "NSE:RELIANCE-EQ",
    "resolution": "1D",  # Weekly data
    "date_format": "0",
    "range_from": date_from[i],
    "range_to": date_to[i],
    "cont_flag": "1"
}

    response = fyers.history(data)
    print(response)

    # Checking if the response was successful
    if response['s'] == 'ok':
        # Convert the data to a DataFrame
        historical_data = pd.DataFrame(response['candles'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert the timestamp to a readable date format
        historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'], unit='s')
    else:
        print("Failed to fetch data:", response)
    
    # Save to CSV
    historical_data.to_csv('reliance_historical_data.csv', index=False)
    print("Data has been saved to reliance_historical_data.csv")
