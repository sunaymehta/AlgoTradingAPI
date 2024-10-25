from fyers_apiv3 import fyersModel
import json
import Functions as F
import time
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io
from datetime import datetime, timedelta


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

# Get Nifty LTP
NiftyLTP = F.GetNiftyLTP(fyers)
time.sleep(5) # Sleep time between 2 API calls to avoid crash

# Get India VIX LTP
IVIXLTP = F.GetVIXLTP(fyers)
# Range for Nifty as per VIX
NiftyRange = F.VixBasedRange(NiftyLTP, IVIXLTP, 5)

# Calculate Put and Call Strikes
putstrike = round(NiftyRange[0] / 100) * 100
callstrike = round(NiftyRange[1] / 100) * 100

# Calculate n
today = datetime.now()
current_weekday = today.weekday()
n = F.CalculateNandThursday(today, current_weekday)[0]
relevant_thurs_date = F.CalculateNandThursday(today, current_weekday)[1]

# Variable defined for monthly expiry
month_dict = {'1':'JAN', '2':'FEB', '3':'MAR',
                    '4':'APR', '5':'MAY', '6':'JUN',
                    '7':'JUL', '8':'AUG', '9':'SEP',
                    '10':'OCT', '11':'NOV', '12':'DEC'}

# Generate tickers
if F.is_last_thursday(relevant_thurs_date):
    year = str(relevant_thurs_date.year)[-2:]
    month = str(relevant_thurs_date.month)
    putsymbol = 'NSE:NIFTY'+year+month_dict[month]+str(putstrike)+'PE'
    callsymbol = 'NSE:NIFTY'+year+month_dict[month]+str(callstrike)+'CE'
    # Write code for generating last thurs of month ticker
else:
    year = str(relevant_thurs_date.year)[-2:]
    month = str(relevant_thurs_date.month)
    day = str(relevant_thurs_date.day)
    if len(day) == 1:
        day = '0'+day
    else:
        pass
    putsymbol = 'NSE:NIFTY'+year+month+day+str(putstrike)+'PE'
    callsymbol = 'NSE:NIFTY'+year+month+day+str(callstrike)+'CE'
    # Write code for generating weekly ticker

PutLTP = F.GetOptionLTP(fyers, putsymbol)
time.sleep(5) # Sleep time between 2 API calls to avoid crash
CallLTP = F.GetOptionLTP(fyers, callsymbol)

basket = [[putsymbol, PutLTP], [callsymbol, CallLTP]]

print ('ORDER PLACEMENT STARTS')

for i in basket:
    F.PlaceOrder(fyers, i[0], i[1])
    time.sleep(2) # 2 second rest between orders


print ('ORDER PLACEMENT COMPLETE')

print ('Current Position Details: ')
print(fyers.positions()['netPositions'])