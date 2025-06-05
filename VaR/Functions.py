from datetime import datetime, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta
import time
from fyers_apiv3 import fyersModel
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io
from mibian import BS

def DataRequest(fyers, asset, range_from, range_to):
    data = {
        "symbol":asset,
        "resolution":"D",
        "date_format":"1",
        "range_from":range_from,
        "range_to":range_to,
        "cont_flag":"1"
    }

    response = fyers.history(data=data)
    time.sleep(10)
    return response

def get_date_ranges(current_date_str, num_years):
    """
    Returns 'num_years' consecutive 1-year date ranges that end the day
    before the anniversary of the start date.
    
    For example, if current_date_str='2024-12-30' and num_years=2, the result is:
      [
        ['2022-12-30', '2023-12-29'],
        ['2023-12-30', '2024-12-29']
      ]
    """
    current_date = datetime.strptime(current_date_str, '%Y-%m-%d')
    start_date = current_date - relativedelta(years=num_years)
    ranges = []
    for i in range(num_years):
        # From date
        from_date = start_date + relativedelta(years=i)
        # To date = (from_date + 1 year) - 1 day
        to_date   = (from_date + relativedelta(years=1)) - timedelta(days=1)
        
        ranges.append([
            from_date.strftime('%Y-%m-%d'),
            to_date.strftime('%Y-%m-%d')
        ])
    
    return ranges

def GetHistoricalData(fyers, asset, ranges):
        
    candles = []
    for i in range(len(ranges)):
        candles += (DataRequest(fyers, asset, ranges[i][0], ranges[i][1]))['candles']

    data_5y = {'candles': candles}

    historical_data = pd.DataFrame(data_5y['candles'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # Convert the timestamp to a readable date format
    historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'], unit='s')

    return historical_data


def LogReturns_Shocks_SimReturns(data, mpor):
    data['LogReturns_'+str(mpor)+'D'] = np.log(data['close'] / data['close'].shift(mpor))
    last_close = data['close'].iloc[-1]
    data['Shocked_Close_'+str(mpor)+'D'] = last_close * np.exp(data['LogReturns_'+str(mpor)+'D'])
    data['SimReturns_'+str(mpor)+'D'] = data['Shocked_Close_'+str(mpor)+'D'] - last_close
    return data

def send_email(to_email, subject, body, hold_table, hold_var_table):
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
    msg.attach(MIMEText('Holdings Investment Summary', 'plain'))
    html_table_with_borders = hold_table.replace(
        '<table border="0" class="dataframe">',
        '<table style="border-collapse: collapse; width: 100%;">'
    ).replace(
        '<th>',
        '<th style="border: 1px solid black; padding: 8px; text-align: left;">'
    ).replace(
        '<td>',
        '<td style="border: 1px solid black; padding: 8px; text-align: left;">'
    )
    
    html_body = f"""
                <html>
                <body>
                    <p>
                    {html_table_with_borders}
                    </p>
                </body>
                </html>
                """
    msg.attach(MIMEText(html_body, "html"))
    msg.attach(MIMEText(body, 'plain'))

    html_table_with_borders = hold_var_table.replace(
        '<table border="0" class="dataframe">',
        '<table style="border-collapse: collapse; width: 100%;">'
    ).replace(
        '<th>',
        '<th style="border: 1px solid black; padding: 8px; text-align: left;">'
    ).replace(
        '<td>',
        '<td style="border: 1px solid black; padding: 8px; text-align: left;">'
    )
    
    html_body = f"""
                <html>
                <body>
                    <p>
                    {html_table_with_borders}
                    </p>
                </body>
                </html>
                """

    # Attach the HTML content
    msg.attach(MIMEText(html_body, "html"))
    
    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_email, msg.as_string())

import re
from datetime import date, timedelta
from calendar import monthrange

# ───────────────────────────────────────────────────────── helpers ──
_MONTH_ABBR = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT':10, 'NOV':11, 'DEC':12,
}

def _make_date(year_two: str, month: int, day: int) -> date:
    """Turn YY‑M‑D into a real date (assume years 2000‑2099)."""
    return date(2000 + int(year_two), month, day)

def _parse_numeric_date(chunk: str) -> tuple[date, int]:
    """Parse YYMMDD (6 chars) or YYMDD (5 chars)."""
    if len(chunk) >= 6:                      # YYMMDD
        try:
            return _make_date(chunk[:2], int(chunk[2:4]), int(chunk[4:6])), 6
        except ValueError:
            pass
    if len(chunk) >= 5:                      # YYMDD
        return _make_date(chunk[:2], int(chunk[2]), int(chunk[3:5])), 5
    raise ValueError

# ───── NEW: explicit‑month code → last Thursday ─────
def _parse_alpha_month(chunk: str) -> tuple[date, int]:
    """
    Parse YYMON (5 chars, e.g. 25APR) and return the **last Thursday**
    of that month as the expiry date.
    """
    m = re.match(r'^(\d{2})([A-Z]{3})', chunk)
    if not m or m.group(2) not in _MONTH_ABBR:
        raise ValueError

    yy, mon = m.groups()
    year, month = 2000 + int(yy), _MONTH_ABBR[mon]

    # find last day of the month, then walk back to Thursday (weekday 3)
    last_day = date(year, month, monthrange(year, month)[1])
    while last_day.weekday() != 3:           # Monday=0 … Thursday=3
        last_day -= timedelta(days=1)

    return last_day, 5
# ─────────────────────────────────────────────────────────────────────

def parse_option_ticker(ticker: str) -> dict:
    """
    Break an Indian‑style option symbol into logical parts.
    Handles numeric expiries (YYMMDD / YYMDD) **and** YYMON blocks
    that imply “last Thursday”.
    """
    exchange, raw = ticker.split(':', 1)

    opt_type, raw = raw[-2:], raw[:-2]               # CE / PE
    if opt_type not in {'CE', 'PE'}:
        raise ValueError("Ticker must end with CE or PE")

    m = re.match(r'^([A-Z]+)', raw)                  # underlying
    underlying, remainder = m.group(1), raw[m.end():]

    # expiry: try numeric first, then alpha‑month
    for parser in (_parse_numeric_date, _parse_alpha_month):
        try:
            expiry, used = parser(remainder)
            break
        except ValueError:
            continue
    else:
        raise ValueError("Unrecognised expiry code")

    strike_str = remainder[used:]
    if not strike_str.isdigit():
        raise ValueError("Strike must be numeric")

    return {
        'exchange'  : exchange,
        'underlying': underlying,
        'expiry'    : expiry,
        'strike'    : int(strike_str),
        'type'      : opt_type,
    }

# ─── tiny demo ───
if __name__ == "__main__":
    print(parse_option_ticker("NSE:INFY25APR1200CE"))
    # → {'exchange': 'NSE', 'underlying': 'INFY',
    #    'expiry': datetime.date(2025, 4, 24),  # last Thu of Apr‑25
    #    'strike': 1200, 'type': 'CE'}


### GREEKS FUNCTIONS

def implied_volatility(observed_price, spot, strike, dte, option_type, interest_rate=0.05):
    bs = BS([spot, strike, interest_rate * 100, dte], callPrice=observed_price) if option_type == 'call' else BS([spot, strike, interest_rate * 100, dte], putPrice=observed_price)
    implied_volatility_result = bs.impliedVolatility

    return implied_volatility_result

def delta(observed_price, spot, strike, dte, option_type, interest_rate=0.05):
    r_pct = interest_rate * 100

    # normalise option_type
    opt = option_type.lower()
    if opt not in {"call", "c", "put", "p"}:
        raise ValueError("option_type must be 'call'/'c' or 'put'/'p'")

    # --- 1) find the implied volatility from the market price -----------------
    if opt in {"call", "c"}:
        bs_iv = BS([spot, strike, r_pct, dte], callPrice=observed_price)
    else:  # put
        bs_iv = BS([spot, strike, r_pct, dte], putPrice=observed_price)

    implied_vol = bs_iv.impliedVolatility  # already in percent

    if implied_vol is None:  # mibian returns None if it cannot converge
        raise RuntimeError("Implied volatility could not be solved for this input.")

    # --- 2) plug the implied vol back in to get Greeks ------------------------
    bs = BS([spot, strike, r_pct, dte], implied_vol)

    delta = bs.callDelta if opt in {"call", "c"} else bs.putDelta
    return delta

def option_vega(
    observed_price: float,
    spot: float,
    strike: float,
    dte: int,
    option_type: str,
    interest_rate = 0.05,
) -> float:
    """
    Calculate Black‑Scholes Vega using the *mibian* BS module.

    Parameters
    ----------
    observed_price : float
        Market premium of the option.
    spot : float
        Current underlying (spot) price.
    strike : float
        Strike price of the option.
    dte : int
        Days to expiration (calendar days).
    option_type : str
        'call', 'c', 'put', or 'p' (case‑insensitive).
    interest_rate : float
        Annual risk‑free rate expressed *in decimal form* (e.g. 0.05 for 5 %).

    Returns
    -------
    float
        Vega in option‑price points **per 1 % change** in implied volatility.
        (mibian’s convention.)
    """
    # Convert rate to the percent format expected by mibian
    r_pct = interest_rate * 100.0

    opt = option_type.lower()
    if opt not in {"call", "c", "put", "p"}:
        raise ValueError("option_type must be 'call'/'c' or 'put'/'p'.")

    # --- Step 1: derive implied volatility from the observed market price -----
    if opt in {"call", "c"}:
        bs_iv = BS([spot, strike, r_pct, dte], callPrice=observed_price)
    else:  # put
        bs_iv = BS([spot, strike, r_pct, dte], putPrice=observed_price)

    iv = bs_iv.impliedVolatility  # percent

    if iv is None:  # convergence failure
        raise RuntimeError("Could not solve for implied volatility "
                           "with these inputs.")

    # --- Step 2: plug the IV back in to obtain Greeks -------------------------
    bs = BS([spot, strike, r_pct, dte], iv)

    return bs.vega


def option_theta(
    observed_price: float,
    spot: float,
    strike: float,
    dte: int,
    option_type: str,
    interest_rate = 0.05,
) -> float:
    """
    Compute the Black‑Scholes theta of an option via the *mibian* BS module.

    Parameters
    ----------
    observed_price : float
        Quoted market premium of the option.
    spot : float
        Current underlying (spot) price.
    strike : float
        Strike price of the option.
    dte : int
        Days to expiration (calendar days, as required by mibian).
    option_type : str
        'call', 'c', 'put', or 'p' (case‑insensitive).
    interest_rate : float
        Risk‑free annual rate **in decimal form** (e.g., 0.04 for 4 %).

    Returns
    -------
    float
        The option’s theta **per calendar day** in premium points.
        (mibian’s convention: negative for long positions in both calls and puts.)
    """
    # mibian expects the rate in *percent*
    r_pct = interest_rate * 100.0

    opt = option_type.lower()
    if opt not in {"call", "c", "put", "p"}:
        raise ValueError("option_type must be 'call'/'c' or 'put'/'p'.")

    # ---- 1) Compute implied volatility from the market price -----------------
    if opt in {"call", "c"}:
        bs_iv = BS([spot, strike, r_pct, dte], callPrice=observed_price)
    else:
        bs_iv = BS([spot, strike, r_pct, dte], putPrice=observed_price)

    iv = bs_iv.impliedVolatility  # percent

    if iv is None:
        raise RuntimeError("Could not solve for implied volatility with these inputs.")

    # ---- 2) Re‑instantiate with that IV to get Greeks ------------------------
    bs = BS([spot, strike, r_pct, dte], iv)

    theta = bs.callTheta if opt in {"call", "c"} else bs.putTheta
    return theta


from datetime import datetime, timedelta
from typing import Literal

def weekdays_between_str(
        start_str: str,
        end_str: str,
        inclusive: Literal[True, False] = True
    ) -> int:
    """
    Count weekdays (Mon–Fri) between two ISO date strings.

    Parameters
    ----------
    start_str, end_str : str
        Boundary dates in 'YYYY-MM-DD' format.
    inclusive : bool, default True
        • True  – include both boundary dates in the tally  
        • False – count only the days strictly *between* the dates

    Returns
    -------
    int
        Number of weekdays in the interval.
    """
    # Parse strings → date objects
    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    end   = datetime.strptime(end_str,   "%Y-%m-%d").date()

    # Ensure start <= end
    if start > end:
        start, end = end, start

    # Adjust boundaries if exclusive
    if not inclusive:
        start += timedelta(days=1)
        end   -= timedelta(days=1)
        if start > end:
            return 0

    delta_days = (end - start).days + 1          # calendar days
    full_weeks, extra = divmod(delta_days, 7)

    weekdays = full_weeks * 5                    # 5 weekdays per full week

    # Weekdays in the partial week at the end
    for i in range(extra):
        if (start.weekday() + i) % 7 < 5:        # 0–4 are Mon–Fri
            weekdays += 1

    return weekdays




