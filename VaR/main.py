import pandas as pd
from fyers_apiv3 import fyersModel
import json
from datetime import datetime, timedelta, date
import Functions as F
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io


# Opening JSON file
with open('../Instructions.json') as json_file:
    instructions = json.load(json_file)
# Opening JSON file
with open('../data.json') as json_file:
    data = json.load(json_file)

appId = instructions['tokens']['appId']
access_token = data['access_token']

fyers = fyersModel.FyersModel(client_id=appId, is_async=False, token=access_token, log_path="")

positions = fyers.positions()
holdings = fyers.holdings()

today = (datetime.today()).strftime("%Y-%m-%d")
################## POSTIONS ###################

# Dump LivePositions
positions = positions['netPositions']
df_positions = pd.DataFrame(columns=['Exchange', 'Underlying', 'Strike', 'CallPut', 'Expiry', 'NetQty', 'EntryPrice', 'LTP', 'GrossPnL'])

for i in positions:
    try:
        symbol = i['symbol']
        exchange = (F.parse_option_ticker(symbol))['exchange']
        underlying = (F.parse_option_ticker(symbol))['underlying']
        strike = (F.parse_option_ticker(symbol))['strike']
        CallPut = (F.parse_option_ticker(symbol))['type']
        Expiry = (F.parse_option_ticker(symbol))['expiry']
        netQty = i['netQty']
        EntryPrice = i['netAvg']
        LTP = i['ltp']
        GrossPnL = (LTP - EntryPrice)*netQty
        row_list = [exchange, underlying, strike, CallPut, Expiry, netQty, EntryPrice, LTP, GrossPnL]
        df_positions.loc[len(df_positions)] = row_list
    except:
        print ('Position is potentially not an Option hence skipped. Details: ', i)

df_positions.to_csv('./Portfolio/LivePositions.csv', index=False)

print ('LivePositions CSV sheet dumped in Portfolio folder!')

# Greeks-based portfolio risk
print ('Calculating Greeks based Portfolio Risk...')
underlying_index_map = {'NIFTY': 'NIFTY50-INDEX',
                        'BANKNIFTY': 'NIFTYBANK-INDEX',
                        'FINNIFTY': 'FINNIFTY-INDEX',
                        'MIDCPNIFTY': 'MIDCPNIFTY-INDEX',
                        'NIFTYNXT50': 'NIFTYNXT50-INDEX',
                        'SENSEX': 'SENSEX-INDEX',
                        'BANKEX': 'BANKEX-INDEX'
}
df_delta = pd.DataFrame(columns=['Underlying', 'Spot', 'Delta Risk'])
df_vega = pd.DataFrame(columns=['Underlying', 'Vega Risk'])
df_theta = pd.DataFrame(columns=['Underlying', 'Theta Risk'])
underlying_unique = list(df_positions.Underlying.unique())
for uu in underlying_unique:
    if uu in underlying_index_map.keys():
        underlying_ticker = 'NSE:'+underlying_index_map[uu]
    else:
        underlying_ticker = 'NSE:'+uu+'-EQ'
    data = {"symbols":underlying_ticker}
    spot = (fyers.quotes(data=data))['d'][0]['v']['lp']
    df_positions_uu = df_positions[df_positions.Underlying == uu]
    net_delta = 0
    net_vega = 0
    net_theta = 0
    for ind, row in df_positions_uu.iterrows():
        dte = F.weekdays_between_str(str(row['Expiry']), today)
        op_type = 'c' if row['CallPut'] == 'CE' else 'p'
        delta = F.delta(row['LTP'], spot, row['Strike'], dte, op_type)
        vega = F.option_vega(row['LTP'], spot, row['Strike'], dte, op_type)
        theta = F.option_theta(row['LTP'], spot, row['Strike'], dte, op_type)

        net_delta += delta*row.NetQty
        net_vega += vega*row.NetQty
        net_theta += theta*row.NetQty


    delta_list = [uu, spot, net_delta]
    vega_list = [uu, net_vega]
    theta_list = [uu, net_theta]
    
    df_delta.loc[len(df_delta)] = delta_list
    df_vega.loc[len(df_vega)] = vega_list  
    df_theta.loc[len(df_vega)] = theta_list  


df_delta_html = df_delta.to_html(index=False, border=0)
df_vega_html = df_vega.to_html(index=False, border = 0)
df_theta_html = df_theta.to_html(index=False, border = 0)


to_email = ['sunaymehta1999@gmail.com']
to_email = ", ".join(to_email)
email_subject = 'VaR Report'
email_body = 'Holdings VaR Summary'

# Dump Historical Data for Positions
today = datetime.now().strftime("%Y-%m-%d")
yearsofdata = 1
ranges = F.get_date_ranges(today, yearsofdata)
MPOR_list =[1,2,5]

for i in positions:
    symbol = i['symbol']
    if symbol in underlying_index_map.keys():
        underlying = (F.parse_option_ticker(symbol))['underlying']
    else:
        underlying = 'NSE:'+F.parse_option_ticker(symbol)['underlying']
    if underlying in underlying_index_map.keys():
        underlying = 'NSE:'+underlying_index_map[underlying]

    historical_data = F.GetHistoricalData(fyers, underlying, ranges)
    historical_data.to_csv('./HistoricalData/'+underlying[4:] + '_'+ str(yearsofdata) + 'Y' + '.csv', index=False)
    print ('Historical Data for stock: ', underlying[4:], ' dumped with Lookback of 1 year.')
    for mpor in MPOR_list:
        data = F.LogReturns_Shocks_SimReturns(historical_data, mpor)
    simulated_returns = data.drop(columns=['open', 'high', 'low', 'volume'])
    simulated_returns.to_csv('./HistoricalData/SimulatedReturns_'+underlying[4:]+'.csv', index=False)
    print ('Simulated Returns for stock: ', underlying[4:], ' dumped with Lookback of 1 year.')

# VaR Computation for Positions
var_percentile = 99
cols = ['Instrument']
cols += ['VaR_'+str(var_percentile)+' '+str(i)+'D' for i in MPOR_list]
df_VaR = pd.DataFrame(columns=cols)
unique_underlying = list(df_positions.Underlying.unique())
for underlying in unique_underlying:
    df_simulated_returns = pd.read_csv('./HistoricalData/SimulatedReturns_'+underlying[4:]+'.csv'')

for i in df_positions:
    unique_underlying =
    simulated_returns = pd.read_csv('./HistoricalData/SimulatedReturns_'+i['symbol'][4:]+'.csv')
    row_list = [i['symbol'][4:]]
    for mpor in MPOR_list:
        percentile_99_loss = int((simulated_returns['SimReturns_'+str(mpor)+'D'].quantile((100-var_percentile)/100))*i['quantity'])
        row_list.append(percentile_99_loss)
    df_VaR.loc[len(df_VaR)] = row_list

df_VaR.to_csv('Holdings_VaR_Summary.csv', index = False)





################## HOLDINGS ###################

# Dump LiveHoldings
holdings = holdings['holdings']
df_holdings = pd.DataFrame(columns=['InstrumentName', 'LTP', 'BuyPrice', 'Qty'])
for i in holdings:
    InstrumentName = i['symbol']
    LTP = i['ltp']
    BuyPrice = i['costPrice']
    Qty = i['quantity']
    row_list = [InstrumentName, LTP, BuyPrice, Qty]
    df_holdings.loc[len(df_holdings)] = row_list

df_holdings.to_csv('./Portfolio/LiveHoldings.csv', index=False)

print ('LiveHoldings CSV sheet dumped in Portfolio folder!')

# Dump Historical Data for Holdings
today = datetime.now().strftime("%Y-%m-%d")
yearsofdata = 5
ranges = F.get_date_ranges(today, yearsofdata)
MPOR_list =[1,14,30]

for i in holdings:
    historical_data = F.GetHistoricalData(fyers, i['symbol'], ranges)
    historical_data.to_csv('./HistoricalData/'+i['symbol'][4:] + '_'+ str(yearsofdata) + 'Y' + '.csv', index=False)
    print ('Historical Data for stock: ', i['symbol'][4:], ' dumped with Lookback of 1 year.')
    for mpor in MPOR_list:
        data = F.LogReturns_Shocks_SimReturns(historical_data, mpor)
    simulated_returns = data.drop(columns=['open', 'high', 'low', 'volume'])
    simulated_returns.to_csv('./HistoricalData/SimulatedReturns_'+i['symbol'][4:]+'.csv', index=False)
    print ('Simulated Returns for stock: ', i['symbol'][4:], ' dumped with Lookback of 1 year.')

# VaR Computation for Holdings
var_percentile = 99
cols = ['Instrument']
cols += ['VaR_'+str(var_percentile)+' '+str(i)+'D' for i in MPOR_list]
df_VaR = pd.DataFrame(columns=cols)
for i in holdings:
    simulated_returns = pd.read_csv('./HistoricalData/SimulatedReturns_'+i['symbol'][4:]+'.csv')
    row_list = [i['symbol'][4:]]
    for mpor in MPOR_list:
        percentile_99_loss = int((simulated_returns['SimReturns_'+str(mpor)+'D'].quantile((100-var_percentile)/100))*i['quantity'])
        row_list.append(percentile_99_loss)
    df_VaR.loc[len(df_VaR)] = row_list

df_VaR.to_csv('Holdings_VaR_Summary.csv', index = False)


df_holdings = pd.read_csv('./Portfolio/LiveHoldings.csv')
df_VaR = pd.read_csv('Holdings_VaR_Summary.csv')

df_VaR_html = df_VaR.to_html(index=False, border=0)
df_holdings_html = df_holdings.to_html(index=False, border=0)

to_email = ['sunaymehta1999@gmail.com']
to_email = ", ".join(to_email)
email_subject = 'VaR Report'
email_body = 'Holdings VaR Summary'

F.send_email(to_email, email_subject, email_body, df_holdings_html, df_VaR_html)

