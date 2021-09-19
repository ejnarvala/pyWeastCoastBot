from enum import Enum

class StonkPeriods(Enum):
    one_day = "1d"
    five_day = "5d"
    one_month = "1mo"
    three_month = "3mo"
    six_month = "6mo"
    one_year = "1y"
    two_year = "2y"
    five_year = "5y"
    ten_year = "10y"
    year_to_date = "ytd"
    max_period = "max"
