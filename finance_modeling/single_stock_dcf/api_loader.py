import numpy as np
import pandas as pd
import requests
import json

# API urls for profit/loss, balance sheet, and cash flow statements
pl_url = 'https://financialmodelingprep.com/api/v3/financials/income-statement/AAPL'
bs_url = 'https://financialmodelingprep.com/api/v3/financials/balance-sheet-statement/AAPL'
cf_url = 'https://financialmodelingprep.com/api/v3/financials/cash-flow-statement/AAPL'

def df_loader():
    # fetching API data using urls
    pl = requests.get(pl_url).json()
    bs = requests.get(bs_url).json()
    cf = requests.get(cf_url).json()

    # converting json to dataframe and transposing

    # profit/loss
    pl_df = pd.DataFrame.from_dict(pl['financials'])
    pl_df = pl_df.T

    # balance sheet
    bs_df = pd.DataFrame.from_dict(bs['financials'])
    bs_df = bs_df.T

    # cash flow
    cf_df = pd.DataFrame.from_dict(cf['financials'])
    cf_df = cf_df.T

    # setting date as column header and dropping column
    dt = pl_df.loc['date']
    dt_str = dt.str.slice(stop=4)
    # profit/loss
    pl_df.columns = dt_str
    pl_df = pl_df[pl_df.columns[::-1]]
    pl_df.drop('date', axis=0, inplace=True)

    # balance sheet
    bs_df.columns = dt_str
    bs_df = bs_df[bs_df.columns[::-1]]
    bs_df.drop('date', axis=0, inplace=True)

    # cash flow
    cf_df.columns = dt_str
    cf_df = cf_df[cf_df.columns[::-1]]
    cf_df.drop('date', axis=0, inplace=True)

    # convert data type from string to float

    # profit/loss
    pl_df = pl_df.astype('float64')

    # balance sheet
    bs_df = bs_df.astype('float64')

    # cash flow
    cf_df = cf_df.astype('float64')

    # change value from real to value to number in millions

    # profit/loss
    pl_df = pl_df / 1000000

    # balance sheet
    bs_df = bs_df / 1000000

    # cash flow
    cf_df = cf_df / 1000000

    # round numbers to have no value after decimal

    # profit/loss
    pl_df = pl_df.round(1)

    # balance sheet
    bs_df = bs_df.round(1)

    # cash flow
    cf_df =cf_df.round(1)

    # save to pickle

    # profit/loss
    pl_df.to_pickle('aapl_pl.pickle')

    # balance sheet
    bs_df.to_pickle('aapl_bs.pickle')

    # cash flow
    cf_df.to_pickle('aapl_cf.pickle')

    return pl_df,bs_df,cf_df

df_loader()
