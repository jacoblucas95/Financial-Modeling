import numpy as np
import pandas as pd
import requests
import loader

df_ls = loader.excel_to_df('apple-y.xlsx')

class DCF:
    def __init__(self):
        self.df_pl = df_ls[0]
        self.df_cf = df_ls[1]
        self.df_bs = df_ls[2]

    def yahoo_financial_statement(self):
        '''
        Fetches financial statement using Yahoo Finance API
        '''
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-financials"

        querystring = {"symbol":"AAPL"}

        headers = {
            'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
            'x-rapidapi-key': "ee394341bbmsh8c35e24e6eb2c23p1f49fcjsn8cf1179e5bce"
            }

        response = requests.request("GET", url, headers=headers, params=querystring)
        financials = response.json()

        return financials

    def free_cash_flow_calc(self):
        '''
        Calculates free cash flow and free cash flow to net income ratio
        '''
        self.df_cf.loc['Free Cash Flow'] = self.df_cf.loc['Cash from Operating Activities'] + self.df_cf.loc['Change in Fixed Assets & Intangibles']
        self.df_cf = self.df_cf.reindex(columns=[*self.df_cf.columns.tolist()], fill_value=0)
        self.df_cf.loc["FCFE/Net Income(%)"] = (self.df_cf.loc['Free Cash Flow'] / self.df_cf.loc['Net Income/Starting Line']) * 100
        self.df_cf = self.df_cf.round(1)

    def revenue_calc(self):
        '''
        Uses analyst 2 year projection for revenue to estimate 4 years of revenue to be used in income statement model
        '''
        cur_rev = self.df_pl.loc["Revenue"]
        rev_est = pd.Series([274860.0, 295930.0], index=["FY '20","FY '21"])
        rev = cur_rev.append(rev_est)
        pct_change = rev.pct_change()
        pct_change[-2:].mean()
        fy22 = rev[-1] * (1 + pct_change[-2:].mean())
        fy23 = fy22 * (1 + pct_change[-2:].mean())
        rev_proj = pd.Series([fy22, fy23], index=["FY '22","FY '23"])
        rev_new = rev.append(rev_proj)
        d = {'Revenue':rev_new, 'Net Income': self.df_cf.loc['Net Income/Starting Line']}
        proj_df = pd.DataFrame(d)
        income_statement_df = proj_df.T
        return income_statement_df

    def income_statement_projections(self):
        '''
        Projected income statement cash flow
        '''
        self.free_cash_flow_calc()
        income_statement_df = self.revenue_calc()
        income_statement_df.loc['Net Income Margins'] = income_statement_df.loc['Net Income'] / income_statement_df.loc['Revenue']
        income_statement_df.loc['Net Income Margins'].fillna(income_statement_df.loc['Net Income Margins'].mean(), inplace=True)
        income_statement_df.loc['Net Income'].fillna(income_statement_df.loc['Revenue']*income_statement_df.loc['Net Income Margins'], inplace=True)
        income_statement_df = income_statement_df.round(3)
        income_statement_df.loc['Free Cash Flow'] = self.df_cf.loc['Free Cash Flow']
        fcf_pct = self.df_cf.loc['FCFE/Net Income(%)'].mean()
        income_statement_df.loc['Free Cash Flow'].fillna(income_statement_df.loc['Net Income'] * fcf_pct/100, inplace=True)
        income_statement_df = income_statement_df.round(3)

        return income_statement_df

    def cost_debt(self):
        '''
        Finds the tax adjusted cost of debt for WACC
        '''
        financials = self.yahoo_financial_statement()
        income_statement = financials['incomeStatementHistory']['incomeStatementHistory']
        interest_expense = income_statement[0]['interestExpense']['longFmt']
        interest_expense = int(interest_expense.replace(',',''))
        adj_int_exp = interest_expense / 1000000

        total_debt = (self.df_bs.loc['Long Term Debt'] + self.df_bs.loc['Short Term Debt'])[-1]
        total_debt

        interest_debt_rate = abs(adj_int_exp) / total_debt
        interest_debt_rate

        income_before_tax = financials['incomeStatementHistory']['incomeStatementHistory'][0]['incomeBeforeTax']['longFmt']
        income_before_tax = int(income_before_tax.replace(',',''))
        adj_inc_bef_tax = income_before_tax / 1000000
        adj_inc_bef_tax

        income_tax_expense = financials['incomeStatementHistory']['incomeStatementHistory'][0]['incomeTaxExpense']['longFmt']
        income_tax_expense = int(income_tax_expense.replace(',',''))
        adj_inc_tax_exp = income_tax_expense / 1000000

        effective_tax_rate = adj_inc_tax_exp / adj_inc_bef_tax

        tax_adjusted_cost_debt = (1 - effective_tax_rate) * interest_debt_rate
        return tax_adjusted_cost_debt

    def risk_free_rate(self):
        '''
        Finds rate of 10 year bond to use as risk free rate
        '''
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/get-summary"

        querystring = {"region":"US","lang":"en"}

        headers = {
            'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
            'x-rapidapi-key': "ee394341bbmsh8c35e24e6eb2c23p1f49fcjsn8cf1179e5bce"
            }

        response = requests.request("GET", url, headers=headers, params=querystring)

        ten_yr_bond = response.json()

        risk_free_rate = float(ten_yr_bond['marketSummaryResponse']['result'][8]['regularMarketPrice']['fmt'])
        return risk_free_rate

    def td_ameritrade_api(self):
        url = 'https://api.tdameritrade.com/v1/instruments'
        params = {
            'apikey': 'KZECOOGWTHECBHB4PNZZM3S1GHKLNQS1',
            'symbol': 'AAPL',
            'projection': 'fundamental'
        }

        content = requests.get(url=url, params=params)
        fundamentals = content.json()
        return fundamentals

    def beta_underlying(self):
        '''
        Finds beta of underlying with API call
        '''
        fundamentals = self.td_ameritrade_api()
        beta = fundamentals['AAPL']['fundamental']['beta']
        return beta

    def cost_equity(self):
        '''
        Finds cost of equity for underlying
        '''
        beta = self.beta_underlying()
        tax_adjusted_cost_debt = self.cost_debt()
        cap_asset_pm = tax_adjusted_cost_debt + beta * (0.10 - tax_adjusted_cost_debt)
        return cap_asset_pm

    def equity_debt_market_value(self):
        '''
        Debt and equity market value
        '''
        fundamentals = self.td_ameritrade_api()
        total_debt = (self.df_bs.loc['Long Term Debt'] + self.df_bs.loc['Short Term Debt'])[-1]
        market_cap = fundamentals['AAPL']['fundamental']['marketCap']
        total = market_cap + total_debt

        # weight of debt & equity
        wd = total_debt / total
        we = market_cap / total
        return wd, we

    def weighted_avg_cost_capital(self):
        '''
        Calculates weighted average cost of capital(WACC)
        '''
        wd, we = self.equity_debt_market_value()
        tax_adjusted_cost_debt = self.cost_debt()
        cap_asset_pm = self.cost_equity()

        wacc = (wd * tax_adjusted_cost_debt) + (we * cap_asset_pm)
        return wacc

    def shares_outstanding_underlying(self):
        '''
        Shares outstanding of underlying
        '''
        fundamentals = self.td_ameritrade_api()
        shares_out = fundamentals['AAPL']['fundamental']['sharesOutstanding']
        return shares_out

    def fair_value_underlying(self):
        '''
        Finds fair value of underlying
        '''
        wacc = self.weighted_avg_cost_capital()
        income_statement_df = self.income_statement_projections()
        shares_out = self.shares_outstanding_underlying()

        dcf_val = income_statement_df.loc[['Free Cash Flow']]
        term_val = (dcf_val.loc['Free Cash Flow', "FY '23"] * (1 + .025)) / (wacc - .025)
        dcf_val['Terminal Value'] = term_val
        discount_factor = (1+wacc)
        dis_fac = [0,0,0,0,0,0,0,0,0,0,discount_factor**1,discount_factor**2,discount_factor**3,discount_factor**4,discount_factor**4]
        dcf_val.loc['Discount Factor'] = dis_fac
        dcf_val.loc['PV of Future Cash Flow'] = dcf_val.loc['Free Cash Flow'] / dcf_val.loc['Discount Factor']
        dcf_val.replace([np.inf], 0, inplace=True)
        todays_val = dcf_val.loc['PV of Future Cash Flow'].sum()
        fair_value = todays_val / shares_out
        print(fair_value)
        return fair_value

if __name__ == '__main__':
    objName = DCF()
    objName.fair_value_underlying()
