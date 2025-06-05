import pandas as pd
import numpy as np
import Functions as F
import json

# DATA DUMPING CODE
# Define Data Dumping Params
with open('./DataDumpParams.json') as json_file:
    datadumpparams = json.load(json_file)

filename = datadumpparams['returns']['asset']
data = pd.read_csv('./HistoricalData/'+filename)

data = data.drop(columns=['open', 'high', 'low', 'volume'])

MPOR_list = datadumpparams['returns']['MPOR_list']
for mpor in MPOR_list:
    data = F.LogReturns_Shocks_SimReturns(data, mpor)

data.to_csv('./HistoricalData/SimulatedReturns_'+datadumpparams['returns']['asset'], index=False)

print ('Simulated returns for Asset: ', filename[:-4], ' for the last ', datadumpparams['returns']['yearsofdata'], ' years with MPORs of ', MPOR_list, ' has been dumped as file name: SimulatedReturns_'+datadumpparams['returns']['asset'])



