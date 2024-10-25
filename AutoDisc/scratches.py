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
import pandas as pd

df_ip_ob = pd.read_csv('InputOrderBook.csv')

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

OrderDict = F.ReadingInputOrderBook(df_ip_ob)

expiryCalendar = F.DateWeekday()

# Forward Expiry Calendar
expiryCalendar['Date'] = pd.to_datetime(expiryCalendar['Date'])
expiryCalendar.set_index('Date', inplace=True)

today = datetime.now()
expiryCalendar = expiryCalendar[(expiryCalendar.index >= today-timedelta(1))]

allIndex = list(expiryCalendar.Index.unique())
allMonth = [i for i in range(1,13)]
month_dict = {'1':'JAN', '2':'FEB', '3':'MAR',
                    '4':'APR', '5':'MAY', '6':'JUN',
                    '7':'JUL', '8':'AUG', '9':'SEP',
                    '10':'OCT', '11':'NOV', '12':'DEC'}

df_ip_ob['InstrumentCode'] = ''
df_ip_ob['LTP'] = ''

for key in OrderDict:
    # Load upcoming 5 expiries
    upcoming10expiries = expiryCalendar[(expiryCalendar.Index == OrderDict[key][0])].head(10)
    unique_months = upcoming10expiries.index.month.unique()
    for m in unique_months:
        monthlies = upcoming10expiries[(upcoming10expiries.index.month == m)]
        last_row_index = monthlies.index[-1]
        year = str(last_row_index.year)[-2:]
        month = month_dict[str(last_row_index.month)]
        upcoming10expiries.at[last_row_index, 'ReformattedDate'] = year+month

    upcoming5expiries = upcoming10expiries.head()
    upcoming5expiries['InstrumentCode'] = 'NSE:' + upcoming5expiries['Index']+upcoming5expiries['ReformattedDate']+str(OrderDict[key][1])+str(OrderDict[key][2])
    
    # Use Instrument Code to get LTP of Option Prices and use LTP based filter
    # to place orders
    #print(upcoming5expiries)


    LTPs = {}
    for ind, row in upcoming5expiries.iterrows():
        LTPs[row.InstrumentCode] = F.GetOptionLTP(fyers, row.InstrumentCode)
        time.sleep(5)

    thresholdPrice = OrderDict[key][4]
    
    for ICode, Price in LTPs.items():
        if Price > thresholdPrice:
            df_ip_ob.loc[key, 'InstrumentCode'] = ICode
            df_ip_ob.loc[key, 'LTP'] = Price
            break
        else:
            pass
    
for ind, row in df_ip_ob.iterrows():
    try:
        F.PlaceOrder(fyers, row.InstrumentCode, int(row.LTP) - 2, row.Qty)
        time.sleep(5)
    except:
        pass

