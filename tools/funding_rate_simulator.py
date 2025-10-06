"""
Funding Rate Simulator for NautilusTrader

This module simulates funding rate payments/receipts for perpetual futures contracts
in backtesting. Funding rates are typically settled every 8 hours in crypto markets.
"""

import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional
from decimal import Decimal


class FundingRateData:
    """
    Container for funding rate historical data
    """
    
    def __init__(self):
        self.rates: Dict[int, float] = {}  # timestamp -> funding_rate
        self.settlement_times: List[int] = []
        
    def load_from_csv(self, csv_file: str):
        """
        Load funding rate data from CSV file
        
        Parameters
        ----------
        csv_file : str
            Path to CSV file with columns: timestamp, funding_rate
        """
        df = pd.read_csv(csv_file)
        
        # Convert timestamp to UTC nanoseconds if needed
        if 'datetime' in df.columns:
            df['timestamp'] = pd.to_datetime(df['datetime']).astype(int) // 10**6
        
        for _, row in df.iterrows():
            timestamp = int(row['timestamp'])
            funding_rate = float(row['funding_rate'])
            self.rates[timestamp] = funding_rate
            self.settlement_times.append(timestamp)
        
        self.settlement_times.sort()
        print(f"✅ Loaded {len(self.rates)} funding rate records")
        print(f"   Date range: {datetime.fromtimestamp(self.settlement_times[0]/1000, tz=timezone.utc)} to "
              f"{datetime.fromtimestamp(self.settlement_times[-1]/1000, tz=timezone.utc)}")
        print(f"   Rate range: {min(self.rates.values()):.6f} to {max(self.rates.values()):.6f}")
    
    def load_from_dict(self, data: Dict[int, float]):
        """
        Load funding rate data from dictionary
        
        Parameters
        ----------
        data : Dict[int, float]
            Dictionary mapping timestamp (ms) to funding rate
        """
        self.rates = data.copy()
        self.settlement_times = sorted(list(data.keys()))
    
    def get_rate_at(self, timestamp_ms: int) -> Optional[float]:
        """
        Get funding rate at specific timestamp
        
        Parameters
        ----------
        timestamp_ms : int
            Timestamp in milliseconds
            
        Returns
        -------
        Optional[float]
            Funding rate, or None if not found
        """
        return self.rates.get(timestamp_ms)
    
    def get_next_settlement(self, current_time_ms: int) -> Optional[int]:
        """
        Get next funding rate settlement time after current time
        
        Parameters
        ----------
        current_time_ms : int
            Current timestamp in milliseconds
            
        Returns
        -------
        Optional[int]
            Next settlement timestamp, or None if no more settlements
        """
        for settlement in self.settlement_times:
            if settlement > current_time_ms:
                return settlement
        return None
    
    def is_settlement_time(self, timestamp_ms: int, tolerance_ms: int = 60000) -> bool:
        """
        Check if timestamp is a funding rate settlement time
        
        Parameters
        ----------
        timestamp_ms : int
            Timestamp to check (milliseconds)
        tolerance_ms : int
            Tolerance in milliseconds (default 1 minute)
            
        Returns
        -------
        bool
            True if within tolerance of a settlement time
        """
        for settlement in self.settlement_times:
            if abs(timestamp_ms - settlement) <= tolerance_ms:
                return True
        return False


class FundingRateTracker:
    """
    Track funding rate payments and receipts during backtest
    """
    
    def __init__(self, funding_data: FundingRateData):
        self.funding_data = funding_data
        self.total_funding_paid = 0.0
        self.total_funding_received = 0.0
        self.funding_history: List[Dict] = []
        self.position_history: List[Dict] = []
        
    def record_position(self, timestamp_ms: int, position_size: float, 
                       position_value: float, side: str):
        """
        Record position state for funding calculation
        
        Parameters
        ----------
        timestamp_ms : int
            Timestamp in milliseconds
        position_size : float
            Position size (quantity)
        position_value : float
            Position value in quote currency
        side : str
            'LONG' or 'SHORT'
        """
        self.position_history.append({
            'timestamp': timestamp_ms,
            'size': position_size,
            'value': position_value,
            'side': side
        })
    
    def calculate_funding(self, timestamp_ms: int, position_size: float,
                         position_value: float, side: str) -> float:
        """
        Calculate funding payment/receipt for a position
        
        Parameters
        ----------
        timestamp_ms : int
            Settlement timestamp in milliseconds
        position_size : float
            Position size (quantity)
        position_value : float
            Position value in quote currency
        side : str
            'LONG' or 'SHORT'
            
        Returns
        -------
        float
            Funding amount (positive = received, negative = paid)
        """
        if position_size == 0:
            return 0.0
        
        funding_rate = self.funding_data.get_rate_at(timestamp_ms)
        if funding_rate is None:
            return 0.0
        
        # Calculate funding payment
        # Positive rate: longs pay shorts
        # Negative rate: shorts pay longs
        funding_payment = position_value * funding_rate
        
        if side == 'LONG':
            # Longs pay when rate is positive, receive when negative
            actual_payment = -funding_payment
        else:  # SHORT
            # Shorts receive when rate is positive, pay when negative
            actual_payment = funding_payment
        
        # Record history
        self.funding_history.append({
            'timestamp': timestamp_ms,
            'datetime': datetime.fromtimestamp(timestamp_ms/1000, tz=timezone.utc),
            'funding_rate': funding_rate,
            'position_size': position_size,
            'position_value': position_value,
            'side': side,
            'payment': actual_payment
        })
        
        # Update totals
        if actual_payment > 0:
            self.total_funding_received += actual_payment
        else:
            self.total_funding_paid += abs(actual_payment)
        
        return actual_payment
    
    def get_net_funding(self) -> float:
        """
        Get net funding (received - paid)
        
        Returns
        -------
        float
            Net funding amount
        """
        return self.total_funding_received - self.total_funding_paid
    
    def get_funding_summary(self) -> Dict:
        """
        Get summary of funding payments
        
        Returns
        -------
        Dict
            Summary statistics
        """
        if not self.funding_history:
            return {
                'total_settlements': 0,
                'total_received': 0.0,
                'total_paid': 0.0,
                'net_funding': 0.0,
                'avg_rate': 0.0,
                'avg_payment': 0.0,
                'min_rate': 0.0,
                'max_rate': 0.0,
            }
        
        rates = [h['funding_rate'] for h in self.funding_history]
        payments = [h['payment'] for h in self.funding_history]
        
        return {
            'total_settlements': len(self.funding_history),
            'total_received': self.total_funding_received,
            'total_paid': self.total_funding_paid,
            'net_funding': self.get_net_funding(),
            'avg_rate': sum(rates) / len(rates),
            'avg_payment': sum(payments) / len(payments),
            'min_rate': min(rates),
            'max_rate': max(rates),
        }
    
    def get_funding_report(self) -> pd.DataFrame:
        """
        Get detailed funding history as DataFrame
        
        Returns
        -------
        pd.DataFrame
            Funding history
        """
        if not self.funding_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.funding_history)
    
    def print_summary(self):
        """
        Print funding summary to console
        """
        summary = self.get_funding_summary()
        
        print("\n" + "=" * 80)
        print("💰 FUNDING RATE SUMMARY")
        print("=" * 80)
        print(f"Total Settlements:  {summary['total_settlements']}")
        print(f"Total Received:     ${summary['total_received']:,.2f}")
        print(f"Total Paid:         ${summary['total_paid']:,.2f}")
        print(f"Net Funding:        ${summary['net_funding']:,.2f}")
        print(f"Average Rate:       {summary['avg_rate']:.6f} ({summary['avg_rate']*100:.4f}%)")
        print(f"Average Payment:    ${summary['avg_payment']:,.2f}")
        print(f"Rate Range:         {summary['min_rate']:.6f} to {summary['max_rate']:.6f}")
        print("=" * 80 + "\n")


def generate_synthetic_funding_rates(
    start_date: datetime,
    end_date: datetime,
    base_rate: float = 0.0001,
    volatility: float = 0.00005
) -> FundingRateData:
    """
    Generate synthetic funding rate data for testing
    
    Parameters
    ----------
    start_date : datetime
        Start date
    end_date : datetime
        End date
    base_rate : float
        Base funding rate (default 0.01% = 0.0001)
    volatility : float
        Rate volatility
        
    Returns
    -------
    FundingRateData
        Synthetic funding rate data
    """
    import numpy as np
    
    funding_data = FundingRateData()
    
    # Generate settlement times every 8 hours
    current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    while current <= end_date:
        timestamp_ms = int(current.timestamp() * 1000)
        
        # Generate rate with mean reversion
        rate = base_rate + np.random.normal(0, volatility)
        rate = max(-0.0005, min(0.0005, rate))  # Clamp to realistic range
        
        funding_data.rates[timestamp_ms] = rate
        funding_data.settlement_times.append(timestamp_ms)
        
        # Next settlement (8 hours later)
        current = current.replace(hour=(current.hour + 8) % 24)
        if current.hour == 0:
            current = current.replace(day=current.day + 1)
    
    funding_data.settlement_times.sort()
    
    return funding_data

