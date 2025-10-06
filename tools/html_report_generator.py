"""
HTML Report Generator for Nautilus Trader Backtest

This module generates interactive HTML reports for backtest results.
"""

import pandas as pd
from datetime import datetime


def generate_html_report(
    symbol: str,
    timeframe: str,
    initial_balance: float,
    final_balance: float,
    orders_report: pd.DataFrame,
    positions_report: pd.DataFrame,
    fills_report: pd.DataFrame,
    timestamp: str,
    currency: str = "USDT"
) -> str:
    """
    Generate HTML format backtest report
    
    Parameters
    ----------
    symbol : str
        Trading symbol
    timeframe : str
        Timeframe
    initial_balance : float
        Initial balance
    final_balance : float
        Final balance
    orders_report : pd.DataFrame
        Orders report
    positions_report : pd.DataFrame
        Positions report
    fills_report : pd.DataFrame
        Fills report
    timestamp : str
        Timestamp
    currency : str
        Currency symbol (default: USDT)
        
    Returns
    -------
    str
        HTML content
    """
    # Calculate statistics
    total_pnl = final_balance - initial_balance
    total_return = (total_pnl / initial_balance) * 100
    
    num_trades = len(positions_report) if positions_report is not None and not positions_report.empty else 0
    num_orders = len(orders_report) if orders_report is not None and not orders_report.empty else 0
    num_fills = len(fills_report) if fills_report is not None and not fills_report.empty else 0
    
    # Calculate win rate
    win_trades = 0
    loss_trades = 0
    if positions_report is not None and not positions_report.empty and 'realized_pnl' in positions_report.columns:
        for pnl in positions_report['realized_pnl']:
            # Remove currency suffix
            pnl_str = str(pnl).replace(f' {currency}', '').replace(' USD', '').replace(' USDT', '')
            try:
                pnl_value = float(pnl_str)
                if pnl_value > 0:
                    win_trades += 1
                elif pnl_value < 0:
                    loss_trades += 1
            except ValueError:
                continue
    
    win_rate = (win_trades / num_trades * 100) if num_trades > 0 else 0
    
    # Convert DataFrames to HTML tables
    orders_html = orders_report.to_html(index=False, classes='data-table', escape=False) if orders_report is not None and not orders_report.empty else '<p class="no-data">No orders data</p>'
    positions_html = positions_report.to_html(index=False, classes='data-table', escape=False) if positions_report is not None and not positions_report.empty else '<p class="no-data">No positions data</p>'
    fills_html = fills_report.to_html(index=False, classes='data-table', escape=False) if fills_report is not None and not fills_report.empty else '<p class="no-data">No fills data</p>'
    
    # Load CSS
    css_content = get_css_content()
    
    # Load JavaScript
    js_content = get_js_content()
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {symbol} {timeframe}</title>
    <style>{css_content}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Backtest Report</h1>
            <p>{symbol} | {timeframe} | {timestamp}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Initial Balance</div>
                <div class="value">${initial_balance:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">Final Balance</div>
                <div class="value">${final_balance:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">Total P&L</div>
                <div class="value {'positive' if total_pnl >= 0 else 'negative'}">${total_pnl:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">Return</div>
                <div class="value {'positive' if total_return >= 0 else 'negative'}">{total_return:.2f}%</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Trades</div>
                <div class="value">{num_trades}</div>
            </div>
            <div class="stat-card">
                <div class="label">Win Rate</div>
                <div class="value">{win_rate:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="label">Winning Trades</div>
                <div class="value positive">{win_trades}</div>
            </div>
            <div class="stat-card">
                <div class="label">Losing Trades</div>
                <div class="value negative">{loss_trades}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="tabs">
                <button class="tab active" onclick="showTab('positions')">📈 Positions</button>
                <button class="tab" onclick="showTab('orders')">📝 Orders</button>
                <button class="tab" onclick="showTab('fills')">✅ Fills</button>
            </div>
            
            <div id="positions-tab" class="tab-content active">
                <div class="search-box">
                    <input type="text" id="positions-search" placeholder="🔍 Search positions..." onkeyup="searchTable('positions-search', 'positions-table')">
                </div>
                <div class="table-container">
                    <div id="positions-table">{positions_html}</div>
                </div>
            </div>
            
            <div id="orders-tab" class="tab-content">
                <div class="search-box">
                    <input type="text" id="orders-search" placeholder="🔍 Search orders..." onkeyup="searchTable('orders-search', 'orders-table')">
                </div>
                <div class="table-container">
                    <div id="orders-table">{orders_html}</div>
                </div>
            </div>
            
            <div id="fills-tab" class="tab-content">
                <div class="search-box">
                    <input type="text" id="fills-search" placeholder="🔍 Search fills..." onkeyup="searchTable('fills-search', 'fills-table')">
                </div>
                <div class="table-container">
                    <div id="fills-table">{fills_html}</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Nautilus Trader Backtest System | {timestamp}</p>
        </div>
    </div>
    
    <script>{js_content}</script>
</body>
</html>
"""
    return html_content


def get_css_content() -> str:
    """
    Get CSS content for the HTML report
    
    Returns
    -------
    str
        CSS content
    """
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .stat-card .label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-card .value {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        
        .stat-card .value.positive {
            color: #10b981;
        }
        
        .stat-card .value.negative {
            color: #ef4444;
        }
        
        .section {
            padding: 30px;
        }
        
        .section h2 {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .table-container {
            overflow-x: auto;
            margin-top: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            font-size: 0.9em;
        }
        
        .data-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .data-table th {
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }
        
        .data-table td {
            padding: 12px 10px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .data-table tbody tr:hover {
            background-color: #f3f4f6;
        }
        
        .data-table tbody tr:nth-child(even) {
            background-color: #f9fafb;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #e5e7eb;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 15px 30px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1em;
            font-weight: 600;
            color: #666;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }
        
        .tab:hover {
            color: #667eea;
            background: #f3f4f6;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }
        
        .search-box {
            margin-bottom: 20px;
        }
        
        .search-box input {
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.1em;
        }
"""


def get_js_content() -> str:
    """
    Get JavaScript content for the HTML report
    
    Returns
    -------
    str
        JavaScript content
    """
    return """
        function showTab(tabName) {
            // Hide all tab contents
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));
            
            // Remove active state from all tabs
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        function searchTable(searchId, tableId) {
            const input = document.getElementById(searchId);
            const filter = input.value.toLowerCase();
            const tableDiv = document.getElementById(tableId);
            const table = tableDiv.querySelector('table');
            
            if (!table) return;
            
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.getElementsByTagName('td');
                let found = false;
                
                for (let j = 0; j < cells.length; j++) {
                    const cell = cells[j];
                    if (cell.textContent.toLowerCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                    }
                }
                
                row.style.display = found ? '' : 'none';
            }
        }
        
        // Add sorting functionality to tables
        document.addEventListener('DOMContentLoaded', function() {
            const tables = document.querySelectorAll('.data-table');
            tables.forEach(table => {
                const headers = table.querySelectorAll('th');
                headers.forEach((header, index) => {
                    header.style.cursor = 'pointer';
                    header.title = 'Click to sort';
                    header.addEventListener('click', () => sortTable(table, index));
                });
            });
        });
        
        function sortTable(table, columnIndex) {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const isAscending = table.dataset.sortColumn === String(columnIndex) && table.dataset.sortDirection === 'asc';
            
            rows.sort((a, b) => {
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();
                
                const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAscending ? bNum - aNum : aNum - bNum;
                }
                
                return isAscending ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
            });
            
            rows.forEach(row => tbody.appendChild(row));
            
            table.dataset.sortColumn = columnIndex;
            table.dataset.sortDirection = isAscending ? 'desc' : 'asc';
        }
"""

