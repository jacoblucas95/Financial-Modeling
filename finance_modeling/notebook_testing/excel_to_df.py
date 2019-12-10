import numpy as np
import pandas as pd

def excel_to_df(file_name):
    '''
    Reads excel file and converts to large dataframe. Splits large dataframe into smaller profit/loss, cashflow, and
    balance sheet dataframes.
    '''
    df = pd.read_excel(file_name)
    df.dropna(how='all',inplace=True)

    index_pl = df.loc[df['Data provided by SimFin'] == 'Profit & Loss statement'].index[0]
    index_cf = df.loc[df['Data provided by SimFin'] == 'Cash Flow statement'].index[0]
    index_bs = df.loc[df['Data provided by SimFin'] == 'Balance Sheet'].index[0]

    df_pl = df.iloc[index_pl:index_bs-2, 1:]
    df_cf = df.iloc[index_cf-2:, 1:]
    df_bs = df.iloc[index_bs-1:index_cf-3, 1:]

    return clean_df(df_pl,df_cf,df_bs)

def clean_df(df_pl,df_cf,df_bs):
    # Profit & Loss DF
    df_pl.columns = df_pl.iloc[0]
    df_pl.set_index('in million USD',inplace=True)
    df_pl.fillna(0, inplace=True)
    df_pl.drop(df_pl.index[0], inplace=True)
    df_pl = df_pl.astype('float64')
    # df_pl = df_pl.T

    # Cash Flow Statement DF
    df_cf.columns = df_cf.iloc[0]
    df_cf.set_index('in million USD', inplace=True)
    df_cf.fillna(0, inplace=True)
    df_cf.drop(df_cf.index[0], inplace=True)
    df_cf = df_cf.astype('float64')
    # df_cf = df_cf.T

    # Balance Sheet DF
    df_bs.columns = df_bs.iloc[0]
    df_bs.set_index('in million USD', inplace=True)
    df_bs.fillna(0, inplace=True)
    df_bs.drop(df_bs.index[0], inplace=True)
    df_bs = df_bs.astype('float64')
    # df_bs = df_bs.T

    return df_pl, df_cf, df_bs

excel_to_df('nvda-y.xlsx')
