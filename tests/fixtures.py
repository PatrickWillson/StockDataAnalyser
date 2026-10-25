"""
Test Fixtures for Stock Data Analyser

This module provides reusable mock data for testing API clients without making real API calls.
All fixtures are based on real API responses but sanitized for testing.
"""

from typing import Dict, Any, List


class EODHDFixtures:
    """Mock responses for EODHD API."""
    
    @staticmethod
    def get_aapl_fundamentals() -> Dict[str, Any]:
        """
        Mock EODHD fundamentals response for AAPL.US.
        Based on real API response structure.
        """
        return {
            'General': {
                'Code': 'AAPL',
                'Exchange': 'NASDAQ',
                'Name': 'Apple Inc',
                'Type': 'Common Stock',
                'CurrencyCode': 'USD',
                'CurrencyName': 'US Dollar',
                'CurrencySymbol': '$',
                'CountryName': 'USA',
                'CountryISO': 'US',
                'Sector': 'Technology',
                'Industry': 'Consumer Electronics',
                'Description': 'Apple Inc. designs, manufactures, and markets smartphones...',
                'FullTimeEmployees': 164000,
                'UpdatedAt': '2024-01-15',
                'IsDelisted': False,
                'Officers': {
                    '0': {
                        'Name': 'Mr. Timothy D. Cook',
                        'Title': 'CEO & Director',
                        'YearBorn': '1960'
                    },
                    '1': {
                        'Name': 'Mr. Luca Maestri',
                        'Title': 'CFO & Senior VP',
                        'YearBorn': '1963'
                    }
                }
            },
            'SharesStats': {
                'SharesOutstanding': 15550061000,
                'SharesFloat': 15528145000,
                'PercentInsiders': 0.071,
                'PercentInstitutions': 61.44
            },
            'Highlights': {
                'MarketCapitalization': 2916000000000,
                'MarketCapitalizationMln': 2916000.0,
                'EBITDA': 129556000000,
                'PERatio': 29.43,
                'PEGRatio': 2.89,
                'WallStreetTargetPrice': 198.5,
                'BookValue': 3.951,
                'DividendShare': 0.96,
                'DividendYield': 0.0051,
                'EarningsShare': 6.16,
                'EPSEstimateCurrentYear': 6.57,
                'EPSEstimateNextYear': 7.23,
                'EPSEstimateNextQuarter': 1.54,
                'EPSEstimateCurrentQuarter': 2.11,
                'MostRecentQuarter': '2023-09-30',
                'ProfitMargin': 0.253,
                'OperatingMarginTTM': 0.297,
                'ReturnOnAssetsTTM': 0.224,
                'ReturnOnEquityTTM': 1.568,
                'RevenueTTM': 383285000000,
                'RevenuePerShareTTM': 24.54,
                'QuarterlyRevenueGrowthYOY': -0.009,
                'GrossProfitTTM': 169148000000,
                'DilutedEpsTTM': 6.16,
                'QuarterlyEarningsGrowthYOY': -0.131,
                'SharePrice': 187.45
            },
            'Valuation': {
                'TrailingPE': 29.43,
                'ForwardPE': 27.89,
                'PriceSalesTTM': 7.45,
                'PriceBookMRQ': 45.23,
                'EnterpriseValue': 2965000000000,
                'EnterpriseValueRevenue': 7.74,
                'EnterpriseValueEbitda': 22.89
            },
            'Technicals': {
                'Beta': 1.29,
                '52WeekHigh': 199.62,
                '52WeekLow': 124.17,
                '50DayMA': 181.23,
                '200DayMA': 175.89
            },
            'Financials': {
                'Balance_Sheet': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2023-09-30': {
                            'date': '2023-09-30',
                            'filing_date': '2023-11-03',
                            'currency_symbol': 'USD',
                            'totalAssets': 352755000000,
                            'intangibleAssets': 0,
                            'earningAssets': None,
                            'otherCurrentAssets': 14695000000,
                            'totalLiab': 290437000000,
                            'totalStockholderEquity': 62146000000,
                            'deferredLongTermLiab': 0,
                            'otherCurrentLiab': 58829000000,
                            'commonStock': 73812000000,
                            'capitalStock': 73812000000,
                            'retainedEarnings': -214000000,
                            'otherLiab': 28636000000,
                            'goodwill': 0,
                            'otherAssets': 64758000000,
                            'cash': 29965000000,
                            'cashAndEquivalents': 29965000000,
                            'totalCurrentLiabilities': 145308000000,
                            'currentDeferredRevenue': 8061000000,
                            'netDebt': 76290000000,
                            'shortTermDebt': 15000000,
                            'shortLongTermDebt': 9822000000,
                            'shortLongTermDebtTotal': 111088000000,
                            'otherStockholderEquity': -11452000000,
                            'propertyPlantEquipment': 43715000000,
                            'totalCurrentAssets': 143566000000,
                            'longTermInvestments': 100544000000,
                            'netTangibleAssets': 62146000000,
                            'shortTermInvestments': 31590000000,
                            'netReceivables': 60985000000,
                            'longTermDebt': 106000000000,
                            'inventory': 6331000000,
                            'accountsPayable': 62611000000,
                            'totalPermanentEquity': None,
                            'noncontrollingInterestInConsolidatedEntity': None,
                            'temporaryEquityRedeemableNoncontrollingInterests': None,
                            'accumulatedOtherComprehensiveIncome': -11452000000,
                            'additionalPaidInCapital': None,
                            'commonStockTotalEquity': None,
                            'preferredStockTotalEquity': None,
                            'retainedEarningsTotalEquity': None,
                            'treasuryStock': None,
                            'accumulatedAmortization': None,
                            'nonCurrrentAssetsOther': None,
                            'deferredLongTermAssetCharges': None,
                            'nonCurrentAssetsTotal': 209189000000,
                            'capitalLeaseObligations': None,
                            'longTermDebtTotal': 106000000000,
                            'nonCurrentLiabilitiesOther': 28636000000,
                            'nonCurrentLiabilitiesTotal': 145129000000,
                            'negativeGoodwill': None,
                            'warrants': None,
                            'preferredStockRedeemable': None,
                            'capitalSurpluse': None,
                            'liabilitiesAndStockholdersEquity': 352755000000,
                            'cashAndShortTermInvestments': 61555000000,
                            'propertyPlantAndEquipmentGross': 114526000000,
                            'propertyPlantAndEquipmentNet': 43715000000,
                            'accumulatedDepreciation': 70811000000,
                            'netWorkingCapital': -1742000000,
                            'netInvestedCapital': 167234000000,
                            'commonStockSharesOutstanding': 15550061000
                        },
                        '2022-09-24': {
                            'date': '2022-09-24',
                            'filing_date': '2022-10-28',
                            'currency_symbol': 'USD',
                            'totalAssets': 352583000000,
                            'intangibleAssets': 0,
                            'totalLiab': 302083000000,
                            'totalStockholderEquity': 50672000000,
                            'commonStock': 64849000000,
                            'retainedEarnings': -3068000000,
                            'goodwill': 0,
                            'cash': 23646000000,
                            'totalCurrentLiabilities': 153982000000,
                            'shortLongTermDebtTotal': 120069000000,
                            'propertyPlantEquipment': 42117000000,
                            'totalCurrentAssets': 135405000000,
                            'longTermInvestments': 120805000000,
                            'netTangibleAssets': 50672000000,
                            'longTermDebt': 98959000000,
                            'inventory': 4946000000,
                            'accountsPayable': 64115000000,
                            'commonStockSharesOutstanding': 15943425000
                        },
                        '2021-09-25': {
                            'date': '2021-09-25',
                            'totalAssets': 351002000000,
                            'totalLiab': 287912000000,
                            'totalStockholderEquity': 63090000000,
                            'commonStock': 57365000000,
                            'retainedEarnings': 5562000000,
                            'goodwill': 0,
                            'intangibleAssets': 0,
                            'cash': 34940000000,
                            'totalCurrentLiabilities': 125481000000,
                            'longTermDebt': 109106000000,
                            'totalCurrentAssets': 134836000000,
                            'inventory': 6580000000,
                            'commonStockSharesOutstanding': 16426786000
                        }
                    }
                },
                'Income_Statement': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2023-09-30': {
                            'date': '2023-09-30',
                            'filing_date': '2023-11-03',
                            'currency_symbol': 'USD',
                            'researchDevelopment': 29915000000,
                            'effectOfAccountingCharges': None,
                            'incomeBeforeTax': 119437000000,
                            'minorityInterest': None,
                            'netIncome': 96995000000,
                            'sellingGeneralAdministrative': 24932000000,
                            'sellingAndMarketingExpenses': None,
                            'grossProfit': 169148000000,
                            'reconciledDepreciation': 11519000000,
                            'ebit': 114301000000,
                            'ebitda': 125820000000,
                            'depreciationAndAmortization': 11519000000,
                            'nonOperatingIncomeNetOther': 0,
                            'operatingIncome': 114301000000,
                            'otherOperatingExpenses': 54847000000,
                            'interestExpense': -3933000000,
                            'taxProvision': 16741000000,
                            'interestIncome': 3750000000,
                            'netInterestIncome': -183000000,
                            'extraordinaryItems': None,
                            'nonRecurring': None,
                            'otherItems': None,
                            'incomeTaxExpense': 16741000000,
                            'totalRevenue': 383285000000,
                            'totalOperatingExpenses': 268984000000,
                            'costOfRevenue': 214137000000,
                            'totalOtherIncomeExpenseNet': 5136000000,
                            'discontinuedOperations': None,
                            'netIncomeFromContinuingOps': 96995000000,
                            'netIncomeApplicableToCommonShares': 96995000000,
                            'preferredStockAndOtherAdjustments': None
                        },
                        '2022-09-24': {
                            'date': '2022-09-24',
                            'netIncome': 99803000000,
                            'totalRevenue': 394328000000,
                            'costOfRevenue': 223546000000,
                            'grossProfit': 170782000000,
                            'operatingIncome': 119437000000,
                            'ebit': 119437000000,
                            'ebitda': 130541000000,
                            'researchDevelopment': 26251000000,
                            'sellingGeneralAdministrative': 25094000000
                        },
                        '2021-09-25': {
                            'date': '2021-09-25',
                            'netIncome': 94680000000,
                            'totalRevenue': 365817000000,
                            'costOfRevenue': 212981000000,
                            'grossProfit': 152836000000,
                            'operatingIncome': 108949000000,
                            'ebit': 108949000000,
                            'ebitda': 120233000000
                        }
                    }
                },
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2023-09-30': {
                            'date': '2023-09-30',
                            'investments': -29513000000,
                            'changeToLiabilities': 8006000000,
                            'totalCashflowsFromInvestingActivities': -29513000000,
                            'netBorrowings': -6686000000,
                            'totalCashFromFinancingActivities': -108488000000,
                            'changeToOperatingActivities': -8314000000,
                            'netIncome': 96995000000,
                            'changeInCash': -3318000000,
                            'beginPeriodCashFlow': 24977000000,
                            'endPeriodCashFlow': 29965000000,
                            'totalCashFromOperatingActivities': 110543000000,
                            'depreciation': 11519000000,
                            'otherCashflowsFromInvestingActivities': 1337000000,
                            'dividendsPaid': -14841000000,
                            'changeToInventory': -1618000000,
                            'changeToAccountReceivables': -1688000000,
                            'salePurchaseOfStock': -77550000000,
                            'otherCashflowsFromFinancingActivities': -3911000000,
                            'changeToNetincome': 14195000000,
                            'capitalExpenditures': -10959000000,
                            'changeReceivables': None,
                            'cashFlowsOtherOperating': None,
                            'exchangeRateChanges': None,
                            'cashAndCashEquivalentsChanges': None,
                            'changeInWorkingCapital': None,
                            'stockBasedCompensation': None,
                            'otherNonCashItems': None,
                            'freeCashFlow': 99584000000
                        },
                        '2022-09-24': {
                            'date': '2022-09-24',
                            'dividendsPaid': -14793000000,
                            'totalCashFromOperatingActivities': 122151000000,
                            'capitalExpenditures': -10708000000,
                            'freeCashFlow': 111443000000
                        },
                        '2021-09-25': {
                            'date': '2021-09-25',
                            'dividendsPaid': -14467000000,
                            'totalCashFromOperatingActivities': 104038000000,
                            'capitalExpenditures': -11085000000,
                            'freeCashFlow': 92953000000
                        }
                    }
                }
            },
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 0.96,
                'ForwardAnnualDividendYield': 0.0051,
                'PayoutRatio': 0.1558,
                'DividendDate': '2023-11-16',
                'ExDividendDate': '2023-11-10',
                'LastSplitFactor': '4:1',
                'LastSplitDate': '2020-08-31',
                'NumberDividendsByYear': {
                    '2023': 4,
                    '2022': 4,
                    '2021': 4,
                    '2020': 4,
                    '2019': 4
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2023', 'shares': 15550061000},
                    '1': {'date': '2022', 'shares': 15943425000},
                    '2': {'date': '2021', 'shares': 16426786000},
                    '3': {'date': '2020', 'shares': 16976763000},
                    '4': {'date': '2019', 'shares': 17772944000}
                }
            }
        }
    
    @staticmethod
    def get_lse_stock_fundamentals() -> Dict[str, Any]:
        """
        Mock EODHD fundamentals response for a London Stock Exchange stock (YU.LSE).
        Demonstrates GBX/GBP currency handling and London Fix scenario.
        """
        return {
            'General': {
                'Code': 'YU',
                'Exchange': 'LSE',
                'Name': 'Yellow Utilities PLC',
                'Type': 'Common Stock',
                'CurrencyCode': 'GBX',  # Pence
                'CurrencyName': 'Pence Sterling',
                'CurrencySymbol': 'p',
                'CountryName': 'UK',
                'CountryISO': 'GB',
                'Sector': 'Utilities',
                'Industry': 'Utilities - Diversified',
                'FullTimeEmployees': 472,
                'UpdatedAt': '2024-01-15',
                'IsDelisted': False,
                'Officers': {
                    '0': {
                        'Name': 'Mr. Baljit Bobby Kalar',
                        'Title': 'CEO & Director',
                        'YearBorn': '1965'
                    }
                }
            },
            'SharesStats': {
                'SharesOutstanding': 18000000,
                'SharesFloat': 6300000,
                'PercentInsiders': 65.0,
                'PercentInstitutions': 13.73
            },
            'Highlights': {
                'MarketCapitalization': 297000000,
                'MarketCapitalizationMln': 297.0,
                'EBITDA': 45000000,
                'PERatio': 8.46,
                'BookValue': 4.82,
                'DividendShare': 0.63,
                'DividendYield': 0.0382,
                'EarningsShare': 1.95,
                'MostRecentQuarter': '2023-12-31',
                'ProfitMargin': 0.054,
                'OperatingMarginTTM': 0.071,
                'ReturnOnAssetsTTM': 0.125,
                'ReturnOnEquityTTM': 0.5308,
                'RevenueTTM': 620000000,
                'RevenuePerShareTTM': 34.44,
                'SharePrice': 1650.0  # Price in GBX (pence)
            },
            'Technicals': {
                'Beta': 0.668,
                '52WeekHigh': 1834.0,
                '52WeekLow': 1235.0
            },
            'Financials': {
                'Balance_Sheet': {
                    'currency_symbol': 'GBP',  # Financials in pounds
                    'yearly': {
                        '2023-12-31': {
                            'date': '2023-12-31',
                            'currency_symbol': 'GBP',
                            'totalAssets': 190000000,
                            'intangibleAssets': 4800000,
                            'totalLiab': 109000000,
                            'totalStockholderEquity': 81000000,
                            'goodwill': 1900000,
                            'cash': 15000000,
                            'totalCurrentLiabilities': 85000000,
                            'propertyPlantEquipment': 95000000,
                            'totalCurrentAssets': 110000000,
                            'netTangibleAssets': 74300000,
                            'longTermDebt': 9500000,
                            'inventory': 8000000,
                            'accountsPayable': 45000000,
                            'commonStockSharesOutstanding': 18000000
                        },
                        '2022-12-31': {
                            'date': '2022-12-31',
                            'totalAssets': 180000000,
                            'totalLiab': 105000000,
                            'totalStockholderEquity': 75000000,
                            'intangibleAssets': 4600000,
                            'goodwill': 1800000,
                            'longTermDebt': 9000000,
                            'totalCurrentAssets': 100000000,
                            'totalCurrentLiabilities': 80000000,
                            'commonStockSharesOutstanding': 18000000
                        }
                    }
                },
                'Income_Statement': {
                    'currency_symbol': 'GBP',
                    'yearly': {
                        '2023-12-31': {
                            'date': '2023-12-31',
                            'currency_symbol': 'GBP',
                            'netIncome': 30860000,
                            'totalRevenue': 620000000,
                            'costOfRevenue': 520000000,
                            'grossProfit': 100000000,
                            'operatingIncome': 44000000,
                            'ebit': 44000000,
                            'ebitda': 50000000
                        },
                        '2022-12-31': {
                            'date': '2022-12-31',
                            'netIncome': 4769000,
                            'totalRevenue': 600000000,
                            'costOfRevenue': 510000000,
                            'grossProfit': 90000000,
                            'operatingIncome': 35000000
                        }
                    }
                },
                'Cash_Flow': {
                    'currency_symbol': 'GBP',
                    'yearly': {
                        '2023-12-31': {
                            'date': '2023-12-31',
                            'dividendsPaid': -10500000,
                            'totalCashFromOperatingActivities': 45000000,
                            'capitalExpenditures': -12000000,
                            'freeCashFlow': 33000000
                        },
                        '2022-12-31': {
                            'date': '2022-12-31',
                            'dividendsPaid': 0,  # Missing dividend data
                            'totalCashFromOperatingActivities': 38000000,
                            'capitalExpenditures': -10000000,
                            'freeCashFlow': 28000000
                        }
                    }
                }
            },
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 0.63,
                'ForwardAnnualDividendYield': 0.0382,
                'PayoutRatio': 0.323,
                'DividendDate': '2024-01-15',
                'ExDividendDate': '2023-12-20'
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2023', 'shares': 18000000},
                    '1': {'date': '2022', 'shares': 18000000},
                    '2': {'date': '2021', 'shares': 18000000}
                }
            }
        }


    @staticmethod
    def get_dividend_api_response() -> List[Dict[str, Any]]:
        """
        Mock EODHD Dividend API response.
        Returns list of dividend declarations with dates and amounts.
        """
        return [
            {
                'date': '2024-06-15',
                'declarationDate': '2024-05-01',
                'recordDate': '2024-06-20',
                'paymentDate': '2024-07-01',
                'period': 'Q2',
                'value': 0.24,
                'unadjustedValue': 0.24,
                'currency': 'USD'
            },
            {
                'date': '2024-03-15',
                'declarationDate': '2024-02-01',
                'recordDate': '2024-03-20',
                'paymentDate': '2024-04-01',
                'period': 'Q1',
                'value': 0.24,
                'unadjustedValue': 0.24,
                'currency': 'USD'
            },
            {
                'date': '2023-12-15',
                'declarationDate': '2023-11-01',
                'recordDate': '2023-12-20',
                'paymentDate': '2024-01-01',
                'period': 'Q4',
                'value': 0.24,
                'unadjustedValue': 0.24,
                'currency': 'USD'
            },
            {
                'date': '2023-09-15',
                'declarationDate': '2023-08-01',
                'recordDate': '2023-09-20',
                'paymentDate': '2023-10-01',
                'period': 'Q3',
                'value': 0.24,
                'unadjustedValue': 0.24,
                'currency': 'USD'
            }
        ]


class YFinanceFixtures:
    """Mock responses for yfinance API."""
    
    @staticmethod
    def get_ticker_fast_info(price: float = 187.45):
        """
        Mock yfinance Ticker.fast_info object.
        
        Args:
            price: Stock price to return
        """
        from unittest.mock import MagicMock
        
        fast_info = MagicMock()
        fast_info.last_price = price
        return fast_info
    
    @staticmethod
    def get_ticker_mock(price: float = 187.45):
        """
        Mock complete yfinance Ticker object.
        
        Args:
            price: Stock price to return
        """
        from unittest.mock import MagicMock
        
        ticker = MagicMock()
        ticker.fast_info = YFinanceFixtures.get_ticker_fast_info(price)
        return ticker


class FXFixtures:
    """Mock responses for Frankfurter FX API."""
    
    @staticmethod
    def get_fx_rate_response(from_currency: str, to_currency: str, rate: float):
        """
        Mock Frankfurter API response for FX rate.
        
        Args:
            from_currency: Source currency code (e.g., 'EUR')
            to_currency: Target currency code (e.g., 'USD')
            rate: Exchange rate to return
        """
        return {
            'amount': 1.0,
            'base': from_currency,
            'date': '2024-01-15',
            'rates': {
                to_currency: rate
            }
        }
    
    @staticmethod
    def get_common_rates():
        """Common FX rates for testing."""
        return {
            ('EUR', 'USD'): 1.10,
            ('GBP', 'USD'): 1.27,
            ('USD', 'EUR'): 0.91,
            ('USD', 'GBP'): 0.79,
            ('GBP', 'EUR'): 1.17,
            ('EUR', 'GBP'): 0.85,
            ('CAD', 'USD'): 0.74,
            ('USD', 'CAD'): 1.35,
            ('JPY', 'USD'): 0.0068,
            ('USD', 'JPY'): 147.0
        }


# Helper functions for creating mock responses

def create_mock_http_response(status_code: int, json_data: Any = None):
    """
    Create a mock HTTP response object.
    
    Args:
        status_code: HTTP status code
        json_data: Data to return from response.json()
    
    Returns:
        Mock response object
    """
    from unittest.mock import Mock
    
    response = Mock()
    response.status_code = status_code
    if json_data is not None:
        response.json.return_value = json_data
    else:
        response.json.side_effect = ValueError("No JSON data")
    return response


def create_financial_data_dict(
    ticker: str = 'TEST.US',
    exchange: str = 'NASDAQ',
    currency: str = 'USD',
    price: float = 100.0,
    years_of_history: int = 10
) -> Dict[str, Any]:
    """
    Create a complete financial_data dictionary for testing.
    
    This mimics the structure returned by EODHDClient.fetch_all_data().
    
    Args:
        ticker: Stock ticker
        exchange: Exchange code
        currency: Currency code
        price: Current stock price
        years_of_history: Number of years of historical data to generate
    
    Returns:
        Complete financial_data dictionary
    """
    history = {}
    base_year = 2024
    
    for i in range(years_of_history):
        year = base_year - i
        year_str = f'{year}-12-31'
        
        # Generate realistic growing financials
        growth_factor = 1.0 + (0.05 * i)  # 5% annual growth backwards
        
        history[year_str] = {
            'revenue': 100000000.0 * growth_factor,
            'net_income': 10000000.0 * growth_factor,
            'eps': 5.0 * growth_factor,
            'dividend': 1.0 * growth_factor,
            'total_equity': 50000000.0 * growth_factor,
            'intangible_assets': 5000000.0 * growth_factor,
            'goodwill': 2000000.0 * growth_factor,
            'shares_outstanding': 2000000.0,
            'current_assets': 30000000.0 * growth_factor,
            'current_liabilities': 10000000.0 * growth_factor,
            'total_liabilities': 20000000.0 * growth_factor,
            'long_term_debt': 10000000.0 * growth_factor
        }
    
    return {
        'ticker': ticker,
        'exchange': exchange,
        'currency': currency,
        'original_stock_currency': currency,
        'price': price,
        'price_source': 'yfinance',
        'ceo_name': 'Test CEO',
        'sector': 'Technology',
        'industry': 'Software',
        'employees': 1000,
        'shares_outstanding': 2000000.0,
        'beta': 1.2,
        'roe': 0.20,
        'roa': 0.10,
        'pe_ratio': 20.0,
        'price_to_book': 2.0,
        'insider_ownership': 10.0,
        'institutional_ownership': 60.0,
        'forward_dividend_rate': 1.0,
        'dividend_source': 'forward_rate',
        'is_dividend_amounts': True,
        'history': history,
        'warnings': []
    }
