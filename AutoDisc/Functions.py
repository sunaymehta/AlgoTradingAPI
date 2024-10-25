from datetime import datetime, timedelta
from mibian import BS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io
import numpy as np
import pandas as pd

# Loading Input Order Book

def ReadingInputOrderBook(df_ip_ob):
    # Loading Input Order Book
    OrderDict = {}
    for ind, row in df_ip_ob.iterrows():
        OrderDict[ind] = [row.Index, row.Strike, row.CallPut, row.Qty, row.LimitPrice, row.BuySell]
            
    return OrderDict


def GetNiftyLTP(fyers): # Returns LTP of Nifty
    data = {
    "symbols":"NSE:NIFTY50-INDEX",
    "ohlcv_flag" : 1
    }

    response = fyers.quotes(data=data)
    ltp = response['d'][0]['v']['lp']
    return ltp

def GetOptionLTP(fyers, symbol): # Returns LTP of Nifty
    data = {
    "symbols":symbol,
    "ohlcv_flag" : 1
    }

    response = fyers.quotes(data=data)
    ltp = response['d'][0]['v']['lp']
    return ltp

def DateWeekday():
    df_dateweekday = pd.read_csv('DateWeekday.csv')
    df_dateweekday = df_dateweekday[(df_dateweekday.Weekday.isin([2,3,4,5,6]))]
    df_dateweekday.reset_index(inplace=True, drop=True)

    df_dateweekday['Index'] = ''
    df_dateweekday['ExpiryDayComments'] = ''
    df_dateweekday['ReformattedDate'] = ''

    holidaylist = ['1/22/2024', '1/26/2024', '3/8/2024', '3/25/2024', '3/29/2024',
                   '4/11/2024', '4/17/2024', '5/1/2024', '5/20/2024', '6/17/2024',
                   '7/17/2024', '8/15/2024', '10/2/2024', '11/1/2024', '11/15/2024',
                   '12/15/2024']
    expiryMap = {2: ['MIDCPNIFTY'],
                 3: ['FINNIFTY'],
                 4: ['BANKNIFTY'],
                 5: ['NIFTY'],
                 6: ['NIFTYNXT50']}
    for ind, row in df_dateweekday.iterrows():
        
        if row.Date in holidaylist:
            df_dateweekday.loc[ind, 'Date'] = df_dateweekday.loc[ind-1, 'Date']
            df_dateweekday.loc[ind, 'Index'] = expiryMap[row.Weekday][0]
            df_dateweekday.loc[ind, 'ExpiryDayComments'] = 'HolidayAdjusted'
            date_split = df_dateweekday.loc[ind, 'Date'].split('/')
            if len(date_split[1])==1:
                date_split[1] = '0'+date_split[1]
            df_dateweekday.loc[ind, 'ReformattedDate'] = date_split[2][-2:]+date_split[0]+date_split[1]
            
        else:
            df_dateweekday.loc[ind, 'Index'] = expiryMap[row.Weekday][0]
            df_dateweekday.loc[ind, 'ExpiryDayComments'] = 'NormalExpiry'
            date_split = df_dateweekday.loc[ind, 'Date'].split('/')
            if len(date_split[1])==1:
                date_split[1] = '0'+date_split[1]
            df_dateweekday.loc[ind, 'ReformattedDate'] = date_split[2][-2:]+date_split[0]+date_split[1]
         
    return df_dateweekday

def PlaceOrder(fyers, ticker, ltp, Qty):
    data = {"symbol":ticker,
            "qty":Qty,    # Multiple of lot size
            "type":1,  # Limit Order
            "side":-1,  # Sell
            "productType":"MARGIN",   # MARGIN VS INTRADAY
            "limitPrice":ltp+0.1,
            "validity":"DAY", 
            "offlineOrder":False,
                    }
    try:
        fyers.place_order(data)
        print ('Order punched as Sell for: ', ticker)
    except:
        print ('Order placement FAILED!!!')
    
    return None

