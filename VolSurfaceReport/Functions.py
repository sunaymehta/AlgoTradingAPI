from datetime import datetime, timedelta
from mibian import BS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io


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


def is_weekday(date):
    return date.weekday() < 5 
def is_last_thursday(date_str):
    # Convert the input date string to a datetime object
    date_obj = datetime.strptime(date_str, '%y%m%d')

    # Check if the day is Thursday and it is the last week of the month
    if date_obj.weekday() == 3 and (date_obj + timedelta(days=7)).month != date_obj.month:
        return True
    else:
        return False
def reformat_date(date_str):
    # Convert the input date string to a datetime object
    date_obj = datetime.strptime(date_str, '%y%m%d')

    # Format the date as YYMM
    reformatted_date = date_obj.strftime('%y%m')
    month_dict = {'01':'JAN', '02':'FEB', '03':'MAR',
                    '04':'APR', '05':'MAY', '06':'JUN',
                    '07':'JUL', '08':'AUG', '09':'SEP',
                    '10':'OCT', '11':'NOV', '12':'DEC'}
    reformatted_date = reformatted_date[:2] + month_dict[reformatted_date[-2:]]
    return reformatted_date
def generate_upcoming_thursdays():
    # Get today's date
    today = datetime.now()

    # Calculate the difference between today and the next Thursday
    days_until_thursday = (3 - today.weekday() + 7) % 7
    next_thursday = today + timedelta(days=days_until_thursday)

    # Generate the next 6 Thursdays
    thursdays = [next_thursday + timedelta(weeks=i) for i in range(5)]
    formatted_thursdays = []
    working_days_left = []
    # Print in YYMDD format
    for thursday in thursdays:
        formatted_thursdays.append(thursday.strftime('%y%m%d'))
        working_days_left.append(sum(1 for single_day in range((thursday - today).days + 1) if is_weekday(today + timedelta(days=single_day))))
    
    reformatted_thursdays = []
    for i in range(len(formatted_thursdays)):
            if formatted_thursdays[i][2] == '0':
                reformatted_thursdays.append(formatted_thursdays[i][0:2]+formatted_thursdays[i][3:])
            else:
                pass
    
    for i in range(0,5):
        if is_last_thursday(formatted_thursdays[i]):
            reformatted_thursdays[i] = reformat_date(formatted_thursdays[i])
        else:
            pass
    
    return [reformatted_thursdays, working_days_left]

def GenerateAllSymbols(strikes_range, upcoming_thursdays, K_Atm):
    all_symbol_list = []
    first_week_symbol_list = []
    
    for expiry in upcoming_thursdays:
        for strike in strikes_range:
            if strike <= K_Atm: # OTM Puts and ATM Put
                all_symbol_list.append('NSE:NIFTY'+expiry+str(strike)+'PE')
            if strike > K_Atm: # OTM Calls
                all_symbol_list.append('NSE:NIFTY'+expiry+str(strike)+'CE')

    expiry1 = upcoming_thursdays[0]
    for strike in strikes_range:
            if strike <= K_Atm: # OTM Puts and ATM Put
                first_week_symbol_list.append('NSE:NIFTY'+expiry1+str(strike)+'PE')
            if strike > K_Atm: # OTM Calls
                first_week_symbol_list.append('NSE:NIFTY'+expiry1+str(strike)+'CE')
          
    return [all_symbol_list, first_week_symbol_list]

def implied_volatility(observed_price, spot, strike, dte, option_type, interest_rate=0.05):
    bs = BS([spot, strike, interest_rate * 100, dte], callPrice=observed_price) if option_type == 'call' else BS([spot, strike, interest_rate * 100, dte], putPrice=observed_price)
    implied_volatility_result = bs.impliedVolatility

    return implied_volatility_result

def send_email(to_email, subject, body, attachments):
    # Email configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'sunaymehta1999@gmail.com'
    smtp_password = 'ugio kefn ulpa hqxv'

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach text body
    msg.attach(MIMEText(body, 'plain'))

    # Attach Matplotlib plots as images
    for i, attachment in enumerate(attachments, start=1):
        image = MIMEImage(attachment.read(), name=f'matplotlib_plot_{i}.png', subtype='png')
        msg.attach(image)
    
    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_email, msg.as_string())


