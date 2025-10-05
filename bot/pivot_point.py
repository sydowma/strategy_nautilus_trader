

from ast import Dict
import datetime


# Helper functions from the original implementation
def is_new_week(dt: datetime.datetime):
    current_time = round_datetime(dt)
    return current_time.weekday() == 0 and current_time.hour == 8

def is_new_month(dt: datetime.datetime):
    current_time = round_datetime(dt)
    return current_time.day == 1 and current_time.hour == 8


def round_datetime(dt_obj, round_to_seconds=1):
    """
    Round a datetime object to a given number of seconds.

    :param dt_obj: The datetime object to round
    :param round_to_seconds: The number of seconds to round to (default is 1)
    :return: The rounded datetime object
    """
    dt_adjusted = dt_obj + datetime.timedelta(seconds=round_to_seconds / 2)
    dt_adjusted -= datetime.timedelta(seconds=dt_adjusted.second % round_to_seconds, microseconds=dt_adjusted.microsecond)
    return dt_adjusted



class CamarillaPivotPoints:
    """
    Camarilla Pivot Points indicator for Bybit market data
    
    This class calculates Camarilla pivot points based on high, low, and close prices.
    It can be used with minute-by-minute data from Bybit.
    """
    
    def __init__(self, timeframe: str = "1m"):
        """
        Initialize the CamarillaPivotPoints indicator
        
        :param timeframe: The timeframe for data (e.g., "1m", "5m", "1h", "1d")
        """
        self.timeframe = timeframe
        self.pivot_points = {
            'pp': None,
            'r1': None,
            'r2': None,
            'r3': None,
            'r4': None,
            'r5': None,
            's1': None,
            's2': None,
            's3': None,
            's4': None,
            's5': None
        }
        self.last_calculation_time = None
        
        # Map timeframe to recalculation frequency
        self.timeframe_map = {
            "1": "daily",    # 1 minute - recalculate daily
            "3": "daily",    # 3 minutes - recalculate daily
            "5": "daily",    # 5 minutes - recalculate daily
            "15": "daily",   # 15 minutes - recalculate daily
            "30": "daily",   # 30 minutes - recalculate daily
            "60": "weekly",  # 1 hour - recalculate weekly
            "240": "weekly", # 4 hours - recalculate weekly
            "D": "monthly",  # 1 day - recalculate monthly
            "W": "monthly",  # 1 week - recalculate monthly
            "M": "yearly"    # 1 month - recalculate yearly
        }
        
    def update(self, timestamp: datetime.datetime, high: float, low: float, close: float) -> Dict:
        """
        Update the pivot points based on new market data
        
        :param timestamp: The timestamp of the current data point
        :param high: The high price
        :param low: The low price
        :param close: The close price
        :return: Dictionary containing the current pivot points
        """
        # Check if we need to recalculate pivot points
        if self._should_recalculate(timestamp):
            self._calculate_pivot_points(high, low, close)
            self.last_calculation_time = timestamp
            
        return self.pivot_points
    
    def _should_recalculate(self, timestamp: datetime.datetime) -> bool:
        """
        Determine if pivot points should be recalculated
        
        :param timestamp: Current timestamp
        :return: True if pivot points should be recalculated, False otherwise
        """
        # If this is the first calculation, always calculate
        if self.last_calculation_time is None:
            return True
        
        # Get recalculation frequency based on timeframe
        recalc_freq = self.timeframe_map.get(self.timeframe, "daily")
        
        # For daily recalculation, check if it's a new day
        if recalc_freq == "daily":
            current_day = timestamp.date()
            last_day = self.last_calculation_time.date()
            return current_day > last_day
            
        # For weekly recalculation, check if it's a new week
        elif recalc_freq == "weekly":
            if is_new_week(timestamp):
                return True
            
            # Also recalculate if more than 7 days have passed
            days_diff = (timestamp - self.last_calculation_time).days
            return days_diff >= 7
            
        # For monthly recalculation, check if it's a new month
        elif recalc_freq == "monthly":
            if is_new_month(timestamp):
                return True
                
            # Also recalculate if more than 30 days have passed
            days_diff = (timestamp - self.last_calculation_time).days
            return days_diff >= 30
            
        # For yearly recalculation, check if it's a new year
        elif recalc_freq == "yearly":
            current_year = timestamp.year
            last_year = self.last_calculation_time.year
            return current_year > last_year
            
        return False
    
    def _calculate_pivot_points(self, high: float, low: float, close: float) -> None:
        """
        Calculate Camarilla pivot points
        
        :param high: The high price
        :param low: The low price
        :param close: The close price
        """
        price_range = high - low
        pp = (high + low + close) / 3
        
        # Resistance levels
        r1 = close + price_range * 1.1 / 12
        r2 = close + price_range * 1.1 / 6
        r3 = close + price_range * 1.1 / 4
        r4 = close + price_range * 1.1 / 2
        
        # Support levels
        s1 = close - price_range * 1.1 / 12
        s2 = close - price_range * 1.1 / 6
        s3 = close - price_range * 1.1 / 4
        s4 = close - price_range * 1.1 / 2
        
        # Additional levels
        r5 = high / low * close
        s5 = close - (r5 - close)
        
        # Update pivot points
        self.pivot_points = {
            'pp': pp,
            'r1': r1,
            'r2': r2,
            'r3': r3,
            'r4': r4,
            'r5': r5,
            's1': s1,
            's2': s2,
            's3': s3,
            's4': s4,
            's5': s5
        }