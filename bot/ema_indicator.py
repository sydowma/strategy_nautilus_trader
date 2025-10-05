class MultiEMAIndicator:
    """
    Calculate multiple EMAs and determine if the trend is up or down.

    Example Usage:
    --------------
    # Input price data
    price_data = [10, 10.5, 11, 10.8, 11.2, 11.5, 11.3, 11.8, 12, 12.2]

    # Initialize with periods, e.g., 3-period and 5-period EMAs
    indicator = MultiEMAIndicator(periods=[3, 5])

    # Calculate all EMAs
    # This will return a list of lists, e.g., [[ema3_values], [ema5_values]]
    all_ema_values = indicator.calculate(price_data)
    ema3_series = all_ema_values[0]
    ema5_series = all_ema_values[1]

    # `ema3_series` might look something like:
    # [0.0, 0.0, 10.5, 10.65, 10.925, 11.2125, 11.25625, 11.528125, 11.7640625, 11.98203125]
    # (Note: Initial values are 0.0 until the first EMA can be calculated)

    # `ema5_series` might look something like:
    # [0.0, 0.0, 0.0, 0.0, 10.7, 10.86666, 10.97777, 11.25185, 11.50123, 11.73415]

    # Check if the overall trend is up based on the defined criteria
    # (all EMAs trending up, faster EMAs above slower EMAs, price above fastest EMA)
    is_up = indicator.is_trend_up(price_data)
    print(f"Trend is up: {is_up}")

    How _calculate_ema works internally:
    ------------------------------------
    # To get just the 3-period EMA directly (though typically you'd use `calculate`):
    # ema3_direct = indicator._calculate_ema(price_data, period=3)
    # Output for `ema3_direct` would be similar to `ema3_series` above.
    # For data = [10, 10.5, 11] and period = 3:
    #   SMA for first EMA point: (10 + 10.5 + 11) / 3 = 10.5
    #   Result: [0.0, 0.0, 10.5]
    # For data = [10, 10.5, 11, 10.8] and period = 3:
    #   EMA_prev = 10.5 (from above)
    #   Multiplier = 2 / (3 + 1) = 0.5
    #   EMA_current = (10.8 - 10.5) * 0.5 + 10.5 = 0.3 * 0.5 + 10.5 = 0.15 + 10.5 = 10.65
    #   Result: [0.0, 0.0, 10.5, 10.65]
    """
    def __init__(self, periods: list[int]):
        self.periods = periods

    def _calculate_ema(self, data: list[float], period: int) -> list[float]:
        """
        Calculate the Exponential Moving Average (EMA) for a single period.

        The returned list will have the same length as the input `data`.
        The first `period - 1` elements of the returned list will be 0.0,
        as EMA calculation requires a history of `period` data points.
        The first actual EMA value is calculated at index `period - 1` (it's an SMA initially),
        and subsequent values are calculated based on the preceding EMA value.

        For example, if data = [10, 11, 12, 13, 14] and period = 3:
        - Index 0: EMA = 0.0 (padding)
        - Index 1: EMA = 0.0 (padding)
        - Index 2: EMA = (10+11+12)/3 = 11.0 (SMA as first value)
        - Index 3: EMA = (13 - 11.0) * (2/(3+1)) + 11.0 = 12.0
        - Index 4: EMA = (14 - 12.0) * (2/(3+1)) + 12.0 = 13.0
        Result: [0.0, 0.0, 11.0, 12.0, 13.0]

        :param data: list of float, the input data (e.g., closing prices).
        :param period: int, the time period for the EMA.
        :return: list of float, the EMA values. The list is padded with 0.0 at the beginning
                 for indices where EMA cannot be computed yet.
        """
        if not data or len(data) < period:
            return [0.0] * len(data)  # Not enough data to calculate EMA

        ema = [0.0] * len(data)
        sma = sum(data[:period]) / period
        ema[period - 1] = sma
        multiplier = 2 / (period + 1)

        for i in range(period, len(data)):
            ema[i] = (data[i] - ema[i - 1]) * multiplier + ema[i - 1]
        
        # For the initial part of the series where EMA is not yet defined, 
        # we can fill with NaN or 0. Here, using 0 for simplicity.
        # Alternatively, one might choose to return only the valid part of EMA.
        for i in range(period -1):
            ema[i] = 0.0 # Or float('nan')
        return ema

    def calculate(self, data: list[float]) -> list[list[float]]:
        """
        Calculate the EMAs for all configured periods.
        :param data: list of float, the data to calculate the EMAs.
        :return: list of lists of float, where each inner list contains EMA values for a period.
        """
        return [self._calculate_ema(data, period) for period in self.periods]

    def is_trend_up(self, data: list[float]) -> bool:
        """
        Determine if the trend is up based on the latest values of all calculated EMAs.
        The trend is considered up if for every EMA, the last value is greater than the second to last value.
        Assumes at least two data points are available to make a comparison.
        :param data: list of float, the input data.
        :return: True if the trend is up, False otherwise.
        """
        if len(data) < 2:
            return False  # Not enough data to determine trend

        all_emas = self.calculate(data)
        
        # Check trend for each EMA period
        for ema_values in all_emas:
            # Ensure there are enough EMA values to compare the last two
            # This check depends on how _calculate_ema handles insufficient data.
            # If _calculate_ema returns fewer than 2 values, or values that are not comparable (e.g. NaN, 0 if it means 'not calculated yet')
            # this logic might need adjustment.
            # Given the current _calculate_ema, it fills initial values with 0.0.
            # We should ensure that we are comparing actual calculated EMA values.
            
            # Find the first non-zero EMA value to start comparison
            first_valid_index = -1
            for i in range(len(ema_values)):
                if ema_values[i] != 0.0: # Assuming 0.0 means not calculated or initial SMA
                    first_valid_index = i
                    break
            
            # Need at least two valid (non-zero) points to compare
            if first_valid_index == -1 or len(ema_values) - first_valid_index < 2:
                return False # Not enough valid EMA points to determine trend for this period

            # Get the last two valid EMA values
            # The ema_values list can have leading zeros if period > len(data) or for the initial part.
            # We need to compare the actual last two computed EMA values.
            
            # Let's find the last two non-zero values if the list might end with zeros due to insufficient data
            # for a specific period more than the length of the overall data.
            # However, calculate should ensure data is long enough for periods.
            # The current _calculate_ema pads with 0s at the beginning.
            
            # We need to compare the last calculated EMA value with the one before it.
            # The last value is at index -1, the one before is at index -2.
            # We must ensure these are actual EMA values, not padding.
            
            # If the EMA list for a period has fewer than 2 elements after removing leading zeros,
            # or if the actual data itself is too short.
            # The current logic implies we look at the very end of the `ema_values` list.
            
            # Let's get the full list of EMAs for the shortest period first to simplify.
            # The `is_trend_up` logic was: self.calculate(data)[-1] > self.calculate(data)[-2]
            # This implies it was comparing the *list of latest EMAs* with the *list of second to latest EMAs*.
            # This is not how trend is usually determined for multiple EMAs.
            # Usually, for an uptrend with multiple EMAs (e.g., EMA20, EMA50, EMA100):
            # 1. All EMAs are trending up (current > previous for each EMA line).
            # 2. Or, faster EMAs are above slower EMAs (e.g., EMA20 > EMA50 > EMA100).
            # The original docstring "15m, EMA 20 50 100 200 up" is ambiguous.
            # "up" could mean each EMA line is pointing upwards, or they are ordered (short > mid > long).

            # Let's assume "up" means each individual EMA line is pointing upwards.
            # And that price must be above all EMAs (or the shortest EMA).
            # The original code was: self.calculate(data)[-1] > self.calculate(data)[-2]
            # If self.calculate(data) returned [ema20_series, ema50_series], then
            # [-1] would be ema50_series and [-2] would be ema20_series.
            # So it was checking if latest_ema50 > latest_ema20, which is for a DOWNTREND if periods are [20, 50].
            # This seems incorrect.

            # Let's reinterpret "EMA 20 50 100 200 up" to mean:
            # EMA20[-1] > EMA20[-2] AND
            # EMA50[-1] > EMA50[-2] AND
            # EMA100[-1] > EMA100[-2] AND
            # EMA200[-1] > EMA200[-2]
            # AND ideally, price > EMA20[-1] and EMA20[-1] > EMA50[-1] > EMA100[-1] > EMA200[-1]
            # The example docstring "allow price to fluctuate within 1% of the EMA" also needs clarification.

            # For now, let's stick to the simpler interpretation: each EMA is individually trending up.
            # We need to make sure we are comparing valid points.
            # The `_calculate_ema` function pads the start with 0s.
            # So, `ema_values[-1]` and `ema_values[-2]` should be valid if `len(data)` is large enough.

            # Find last two non-padding values
            relevant_emas = [val for val in ema_values if val != 0.0] # Assuming 0.0 is padding
            if len(relevant_emas) < 2:
                return False # Not enough data points for this EMA to determine trend
            
            if not (relevant_emas[-1] > relevant_emas[-2]):
                return False  # This EMA is not trending up
        
        # If all EMAs are trending up:
        # Now consider the "allow price to fluctuate within 1% of the EMA"
        # This suggests a relationship between price and EMAs.
        # Let's assume price should be above the shortest EMA (or all EMAs).
        # The docstring "15m, EMA 20 50 100 200 up" could mean all EMAs are ordered short > long
        # and price is above the shortest.

        # The original code was `self.calculate(data)[-1] > self.calculate(data)[-2]`.
        # If `periods = [20, 50]`, `calculate` (old one using talib) would return `[ema20_series, ema50_series]`.
        # Then `self.calculate(data)[-1]` is `ema50_series` and `self.calculate(data)[-2]` is `ema20_series`.
        # Accessing `ema_series[-1]` (last value) and `ema_series[-2]` (second last value) on these.
        # So it was trying to compare `ema50_series[-1] > ema50_series[-2]` and `ema20_series[-1] > ema20_series[-2]`? No.
        # It was `talib.EMA(data, 50)[-1] > talib.EMA(data, 20)[-1]` if periods = [20, 50] and we sort periods.
        # This is wrong. The old code was:
        # `return self.calculate(data)[-1] > self.calculate(data)[-2]`
        # If `self.calculate(data)` returned a list of EMA *values* (not series) for the last point:
        # e.g. `[ema20_last, ema50_last, ema100_last, ema200_last]`
        # Then `[-1]` would be `ema200_last` and `[-2]` would be `ema100_last`.
        # It would check if `ema200_last > ema100_last`. This is a condition for downtrend (longer EMA > shorter EMA).

        # Let's re-evaluate the original intent of `is_trend_up`'s previous one-liner with talib.
        # `self.calculate(data)` was `[talib.EMA(data, period) for period in self.periods]`
        # This returns a list of arrays. e.g., `[ema20_array, ema50_array]`.
        # `self.calculate(data)[-1]` would be `ema50_array`.
        # `self.calculate(data)[-2]` would be `ema20_array`.
        # The comparison `ema50_array > ema20_array` would perform an element-wise comparison
        # and return an array of booleans. This is not what `is_trend_up` should return.
        # It seems the previous implementation of `is_trend_up` was conceptually flawed or incomplete.

        # Let's define "trend is up" as:
        # 1. All EMAs are individually pointing upwards (last value > second to last value).
        # 2. The faster EMAs are above the slower EMAs (e.g., EMA20 > EMA50 > EMA100).
        # 3. The current price is above the fastest EMA (or all EMAs).

        # For simplicity, let's first implement condition 1: all EMAs are pointing upwards.
        # This was started above.
        # If we reach here, all individual EMAs are trending up (relevant_emas[-1] > relevant_emas[-2]).
        
        # Now, let's implement condition 2: faster EMAs are above slower EMAs.
        # We need to ensure periods are sorted, or retrieve EMAs by period.
        # Assuming self.periods is sorted from fastest to slowest (e.g., [20, 50, 100]).
        # The `all_emas` list will correspond to `self.periods`.
        
        last_ema_values = []
        for ema_series in all_emas:
            relevant_emas_for_period = [val for val in ema_series if val != 0.0]
            if not relevant_emas_for_period: # Should not happen if data is sufficient
                return False 
            last_ema_values.append(relevant_emas_for_period[-1])
        
        if not last_ema_values: return False

        # Check if faster EMAs are above slower EMAs
        # (assuming self.periods is sorted from shortest to longest)
        # e.g. last_ema_values = [ema20_last, ema50_last, ema100_last]
        # We need ema20_last > ema50_last AND ema50_last > ema100_last
        for i in range(len(last_ema_values) - 1):
            if not (last_ema_values[i] > last_ema_values[i+1]):
                return False # Faster EMA is not above slower EMA

        # Condition 3: Price is above the fastest EMA.
        # The "price" is `data[-1]`. The fastest EMA is `last_ema_values[0]` (if periods sorted).
        if not self.periods: return False # No periods defined
        
        # Ensure periods are sorted to correctly identify the fastest EMA
        sorted_periods = sorted(self.periods)
        if not sorted_periods: return False

        # Find the EMA corresponding to the fastest period
        fastest_period = sorted_periods[0]
        fastest_ema_series_index = self.periods.index(fastest_period) # Find original index
        
        fastest_ema_series = all_emas[fastest_ema_series_index]
        relevant_fastest_ema = [val for val in fastest_ema_series if val != 0.0]
        if not relevant_fastest_ema: return False
        
        last_fastest_ema = relevant_fastest_ema[-1]

        # The docstring says: "allow price to fluctuate within 1% of the EMA"
        # This means price can be slightly below the EMA.
        # Price > EMA * (1 - 0.01)  which is Price > EMA * 0.99
        current_price = data[-1]
        if not (current_price > last_fastest_ema * 0.99):
            return False
            
        return True # All conditions met for an uptrend

