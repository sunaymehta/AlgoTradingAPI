from datetime import datetime, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta
import time
from fyers_apiv3 import fyersModel


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