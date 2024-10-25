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
K_Atm = int(round(NiftyLTP, -2))

strikes_range = [i for i in range(K_Atm-1000, K_Atm+1100, 100)]
upcoming_thursdays = F.generate_upcoming_thursdays()[0]
all_symbol_list = (F.GenerateAllSymbols(strikes_range, upcoming_thursdays, K_Atm))[0]
first_week_symbol_list = (F.GenerateAllSymbols(strikes_range, upcoming_thursdays, K_Atm))[1]
op_ltp_week1 = []
print ('Generated Nifty LTP\nGenerated Relevant Strikes')

for i in first_week_symbol_list:
    op_ltp_week1.append(F.GetOptionLTP(fyers, i))
    time.sleep(3)
print ('Obtained LTP for all Options in the first week')

IVs_Week1 = []
for i in first_week_symbol_list:
    observed_price = F.GetOptionLTP(fyers, i)
    spot = NiftyLTP
    strike = i[-7:-2]
    dte = F.generate_upcoming_thursdays()[1][0]
    option_type = 'call' if i[-2] == 'C' else 'put'
    interest_rate= 0.065 # Always keep RBI Repo Rate
    IVs_Week1.append(F.implied_volatility(observed_price, spot, strike, dte, option_type, interest_rate))
    time.sleep(3)
print ('Obtained IVs for all Options in the first week')

K_Atm_Symbols = [i for i in all_symbol_list if str(K_Atm) in i]
K_Atm_IVs = []
counter = 0
failure_flags = []
index_count = 0
for i in K_Atm_Symbols:    
    try:
        observed_price = F.GetOptionLTP(fyers, i)
        spot = NiftyLTP
        strike = i[-7:-2]
        dte = F.generate_upcoming_thursdays()[1][counter]
        option_type = 'call' if i[-2] == 'C' else 'put'
        interest_rate= 0.065 # Always keep RBI Repo Rate
        K_Atm_IVs.append(F.implied_volatility(observed_price, spot, strike, dte, option_type, interest_rate))
        counter+=1
        print (observed_price, spot, strike, dte, option_type, interest_rate)
        time.sleep(3)
    except:
        failure_flags.append(index_count)
    index_count += 1
print ('Obtained Options Prices and IV for ATM Strike for Next 3 expiries')

if len(failure_flags)>0:
    for i in failure_flags:
        del K_Atm_Symbols[i]
        del upcoming_thursdays[i]


# Make Plot for Option Price vs Strike Price
plt.plot(strikes_range, op_ltp_week1, marker='o', linestyle='-', color='b', label='Line Plot')
# Add labels and title
plt.xlabel('Strike Prices')
plt.ylabel('Options Prices')
plt.title('NIFTY: Option Price vs Strike Price for Immediate Weekly expiry.\nPuts for Strikes till '+str(K_Atm)+'; Calls thereafter.')
plt.grid(True)
# Save the plot to a BytesIO object
graph1 = io.BytesIO()
plt.savefig(graph1, format='png')
graph1.seek(0)
# Add a legend
plt.legend()
# Display the plot
#plt.show()
plt.close()


# Make Plot for IV vs Strike
plt.plot(strikes_range, IVs_Week1, marker='o', linestyle='-', color='b', label='Line Plot')
# Add labels and title
plt.xlabel('Strike Prices')
plt.ylabel('Options IVs')
plt.title('NIFTY: IV vs Strike Price for Immediate Weekly expiry.\nPuts for Strikes till '+str(K_Atm)+'; Calls thereafter.')
plt.grid(True)
# Save the plot to a BytesIO object
graph2 = io.BytesIO()
plt.savefig(graph2, format='png')
graph2.seek(0)
# Add a legend
plt.legend()
# Display the plot
#plt.show()
plt.close()

# Make Plot for IV vs Expiry
plt.plot(upcoming_thursdays, K_Atm_IVs, marker='o', linestyle='-', color='b', label='Line Plot')
# Add labels and title
plt.xlabel('Strike Prices')
plt.ylabel('Options IVs')
plt.title('NIFTY: IV vs Expiry Date for Immediate Weekly expiry.\nAll IVs for Puts at Strikes '+str(K_Atm))
plt.grid(True)
# Save the plot to a BytesIO object
graph3 = io.BytesIO()
plt.savefig(graph3, format='png')
graph3.seek(0)
# Add a legend
plt.legend()
# Display the plot
#plt.show()
plt.close()

# Generate the Matplotlib plot
plot_buffer = [graph1, graph2, graph3]
# Send the email with the Matplotlib plot as an attachment
to_email = 'sunaymehta1999@gmail.com'
email_subject = 'Volatility Surface Report'
email_body = 'Please find the attached Matplotlib plot.\nNote Nifty LTP: '+str(NiftyLTP)

F.send_email(to_email, email_subject, email_body, plot_buffer)

print ('Email Sent to ', to_email)
