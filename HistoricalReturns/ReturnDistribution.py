import pandas as pd
import json

with open('./DataDumpParams.json') as json_file:
    datadumpparams = json.load(json_file)

df = pd.read_csv('./RawData/'+datadumpparams['returns']['asset'])



def compute_shifted_returns_single(df, price_col='close', shift_n=1, return_col_prefix='Return'):

    col_name = f"{return_col_prefix}_{shift_n}d_%"
    
    # Calculate shifted percentage return
    df[col_name] = (df[price_col] / df[price_col].shift(shift_n) - 1) * 100
    
    return df
