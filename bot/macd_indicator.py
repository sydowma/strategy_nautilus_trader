class MACDIndicator:
    """
    Calculate MACD (Moving Average Convergence Divergence) indicator.
    
    MACD is a trend-following momentum indicator that shows the relationship 
    between two exponential moving averages (EMAs) of a security's price.
    
    Components:
    - MACD Line: 12-period EMA - 26-period EMA
    - Signal Line: 9-period EMA of MACD Line
    - Histogram: MACD Line - Signal Line
    
    Example Usage:
    --------------
    price_data = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, ...]
    
    indicator = MACDIndicator(fast_period=12, slow_period=26, signal_period=9)
    
    # Calculate MACD components
    macd_line, signal_line, histogram = indicator.calculate(price_data)
    
    # Check for bullish/bearish signals
    is_bullish = indicator.is_bullish_crossover(price_data)
    is_bearish = indicator.is_bearish_crossover(price_data)
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        Initialize MACD indicator with default periods.
        
        :param fast_period: Fast EMA period (default: 12)
        :param slow_period: Slow EMA period (default: 26)
        :param signal_period: Signal line EMA period (default: 9)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def _calculate_ema(self, data: list[float], period: int) -> list[float]:
        """
        Calculate Exponential Moving Average (EMA).
        
        :param data: Input price data
        :param period: EMA period
        :return: List of EMA values
        """
        if not data or len(data) < period:
            return [0.0] * len(data)
        
        ema = [0.0] * len(data)
        sma = sum(data[:period]) / period
        ema[period - 1] = sma
        multiplier = 2 / (period + 1)
        
        for i in range(period, len(data)):
            ema[i] = (data[i] - ema[i - 1]) * multiplier + ema[i - 1]
        
        return ema
    
    def calculate(self, data: list[float]) -> tuple[list[float], list[float], list[float]]:
        """
        Calculate MACD components.
        
        :param data: Input price data
        :return: Tuple of (macd_line, signal_line, histogram)
        """
        if len(data) < self.slow_period:
            empty = [0.0] * len(data)
            return empty, empty, empty
        
        # Calculate fast and slow EMAs
        fast_ema = self._calculate_ema(data, self.fast_period)
        slow_ema = self._calculate_ema(data, self.slow_period)
        
        # Calculate MACD line (fast EMA - slow EMA)
        macd_line = [fast - slow for fast, slow in zip(fast_ema, slow_ema)]
        
        # Calculate signal line (EMA of MACD line)
        # Only use MACD values starting from slow_period to avoid zeros
        signal_line = self._calculate_ema(macd_line, self.signal_period)
        
        # Calculate histogram (MACD - Signal)
        histogram = [macd - signal for macd, signal in zip(macd_line, signal_line)]
        
        return macd_line, signal_line, histogram
    
    def is_bullish_crossover(self, data: list[float]) -> bool:
        """
        Check if there's a bullish crossover (MACD crosses above signal line).
        
        :param data: Input price data
        :return: True if bullish crossover detected
        """
        if len(data) < self.slow_period + self.signal_period + 2:
            return False
        
        macd_line, signal_line, _ = self.calculate(data)
        
        # Check if MACD crossed above signal line
        # Previous: MACD <= Signal, Current: MACD > Signal
        if (macd_line[-2] <= signal_line[-2] and 
            macd_line[-1] > signal_line[-1] and
            macd_line[-1] != 0.0 and signal_line[-1] != 0.0):
            return True
        
        return False
    
    def is_bearish_crossover(self, data: list[float]) -> bool:
        """
        Check if there's a bearish crossover (MACD crosses below signal line).
        
        :param data: Input price data
        :return: True if bearish crossover detected
        """
        if len(data) < self.slow_period + self.signal_period + 2:
            return False
        
        macd_line, signal_line, _ = self.calculate(data)
        
        # Check if MACD crossed below signal line
        # Previous: MACD >= Signal, Current: MACD < Signal
        if (macd_line[-2] >= signal_line[-2] and 
            macd_line[-1] < signal_line[-1] and
            macd_line[-1] != 0.0 and signal_line[-1] != 0.0):
            return True
        
        return False
    
    def get_histogram_trend(self, data: list[float], lookback: int = 3) -> str:
        """
        Get the trend of the histogram over the last few bars.
        
        :param data: Input price data
        :param lookback: Number of bars to look back
        :return: "increasing", "decreasing", or "neutral"
        """
        if len(data) < self.slow_period + self.signal_period + lookback:
            return "neutral"
        
        _, _, histogram = self.calculate(data)
        
        # Get the last 'lookback' histogram values
        recent_hist = histogram[-lookback:]
        
        # Check if all are increasing
        is_increasing = all(recent_hist[i] < recent_hist[i+1] for i in range(len(recent_hist)-1))
        is_decreasing = all(recent_hist[i] > recent_hist[i+1] for i in range(len(recent_hist)-1))
        
        if is_increasing:
            return "increasing"
        elif is_decreasing:
            return "decreasing"
        else:
            return "neutral"

