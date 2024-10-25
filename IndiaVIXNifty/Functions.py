from datetime import datetime, timedelta
from mibian import BS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io
import numpy as np

def GetNiftyLTP(fyers): # Returns LTP of Nifty
    data = {
    "symbols":"NSE:NIFTY50-INDEX",
    "ohlcv_flag" : 1
    }

    response = fyers.quotes(data=data)
    ltp = response['d'][0]['v']['lp']
    return ltp

def GetVIXLTP(fyers): # Returns LTP of India VIX
    data = {
    "symbols":"NSE:INDIAVIX-INDEX",
    "ohlcv_flag" : 1
    }

    response = fyers.quotes(data=data)
    ltp = response['d'][0]['v']['lp']
    return ltp

def VixBasedRange(NiftyLTP, IVIXLTP, n):
    expected_move = (IVIXLTP*np.sqrt(n)*NiftyLTP)/(100*np.sqrt(250))

    urange = NiftyLTP+expected_move
    lrange = NiftyLTP-expected_move
    
    return [lrange, urange]

def CalculateNandThursday(today, current_weekday):
    if current_weekday == 0: # Monday
        n = 4
        td = 3
        
    elif current_weekday == 1: # Tuesday
        n = 3
        td = 2
        
    elif current_weekday == 2: # Wednesay - rollover day
        n = 7
        td = 8
        
    elif current_weekday == 3: # Thursday - rollover day
        n = 8
        td = 7
        
    elif current_weekday == 4: # Friday
        n = 5
        td = 6
        
    if n >= 7:
        relevant_thurs_date = today + timedelta(td)
    else:
        relevant_thurs_date = today + timedelta(td)

    return [n, relevant_thurs_date]

def is_last_thursday(date_str):
    if date_str.weekday() == 3 and (date_str + timedelta(days=7)).month != date_str.month:
        return True
    else:
        return False

def GetOptionLTP(fyers, symbol): # Returns LTP of Nifty
    data = {
    "symbols":symbol,
    "ohlcv_flag" : 1
    }

    response = fyers.quotes(data=data)
    ltp = response['d'][0]['v']['lp']
    return ltp

def PlaceOrder(fyers, ticker, ltp):
    data = {"symbol":ticker,
            "qty":50,    # Multiple of lot size
            "type":1,  # Mkt Order
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