# programming for Data Analysis
## 1. Introduction
This project was developed to build a complete data pipeline for Qualcomm (QCOM) 1-minute stock market data.  
The aim of the system is to fetch real time data from some reasonable period of time, clean it, transform it into meaningful analytical values, store it in a SQL database, and present the results in a Flask dashboard.

The system was implemented step by step on a virtual machine environment with Visual Studio, Python, MariaDB/MySQL, Flask, and GitHub.

## 2. Project Overview
The Project divided into four major parts:
1. **Data Collection**
    - QCOM 1-minute stock data is fetched from Yahoo Finance.
    - Data is automatically being fetched and stroed in mysql database through cronjob and data fetching history is maintained at github since 14_03_2026
    - Some previous weeks data was fetched using google colab and CSV files collected earlier, were also pushed into github and mysql db.
2. **Data Transformation**
   - Raw stock data is transformed into analytical values such as monthly gain/loss, returns, volatility, and unusual behavior indicators.
3. **Data Storage**
   - All transformed and raw data is stored in MySQL/MariaDB tables for further analysis.
4. **Presentation Layer**
   - A Flask dashboard is used to display the collected and transformed data in a professional and presentable way.

-----
## 3. Main Implementation Components
### 3.1 Data Fetching Script
->scripts/fetch_qcom_1m_weekly.py 
The main stock data fetching script was implemented to collect QCOM 1-minute data from Yahoo Finance and store it in the SQL database.

It has the code to:
- connect to Yahoo Finance API endpoint
- fetch recent 1-minute stock data
- clean duplicates
- insert/update rows in the main stock table

### 3.2 Historical CSV Import
->scripts/existing_data.py
A separate import workflow was created to bring older CSV data into the same database structure.

It has the code to:
- read previously collected CSV files
- combine multiple CSV files
- sort them by timestamp
- remove duplicate timestamps
- store them in the database
This allowed the project to show that data had been collected over a reasonable period of time.

### 3.3 Transformation Logic
-> scripts/transform_qcom_1m.py
A separate transformation script which has the logic to get transformed features.

The transformation function calculates:
- `price_gain`
- `return_pct`
- `log_return`
- `realized_vol_20`
- `realized_vol_60`
- `cumulative_gain`
- `volume_zscore`
- `unusual_move_flag`
- `unusual_volume_flag`
- `unusual_vol_flag`

### 3.4 Monthly Summary Generation
->scripts/monthly_summary_qcom.py 
A monthly summary process was implemented to create higher-level analysis from the minute-level data.

The summary table stores values such as:
- monthly low
- monthly high
- monthly median close
- first close of the month
- last close of the month
- monthly gain/loss
- monthly gain/loss percentage
- average realized volatility
- average log return
- standard deviation of log return
- unusual behavior counts and ratios

### 3.5 Flask Dashboard

A Flask dashboard was implemented with some assistance from AI as the frontend of the project.

The dashboard shows:
- total rows collected
- start and end dates of the dataset
- latest close price
- latest realized volatility
- daily close price chart
- daily volatility chart
- daily volume chart
- monthly gain/loss chart
- monthly summary table
- recent minute-level rows
- transformation descriptions

---

## 4. Database Design (mysql)
Two tables were created in database, one for raw data fetching and some tranformation. other for final tranformation and key insightful values

### 4.1 `stock_prices_1m`

This is the main table in the system.

It stores:
- raw 1-minute stock data
- transformed analytical columns
- unusual behavior flags

Important fields include:
- `datetime_utc`
- `open_price`
- `high_price`
- `low_price`
- `close_price`
- `volume`
- `price_gain`
- `return_pct`
- `log_return`
- `realized_vol_20`
- `realized_vol_60`
- `cumulative_gain`
- `volume_zscore`
- `unusual_move_flag`
- `unusual_volume_flag`
- `unusual_vol_flag`

### 4.2 `monthly_summary_qcom`

This table stores month-level summaries created from the minute-level dataset.

It includes:
- price summary metrics
- monthly performance metrics
- volatility summary metrics
- unusual behavior counts and ratios

---

## 5. Data Flow in the System

This project follows this flow:

1. Raw QCOM data is  being automatically fetched using cronjob on every Monday.
2. The data is cleaned and sorted by timestamp.
3. Duplicate timestamps are removed.
4. The transformation function generates analytical columns.
5. The data is stored in the `stock_prices_1m` table.
6. Monthly summaries are calculated from the minute-level table.
7. Monthly values are stored in `monthly_summary_qcom`.
8. The Flask application reads from both tables and displays the results in a dashboard.

---
## 6. Testing Performed

Testing was performed at two levels:

### 6.1 Unit Testing

Unit testing was performed on the main transformation function.

The purpose of the unit test was to verify that:
- transformed columns are created correctly
- mathematically expected values are produced
- first-row values remain empty where appropriate
- rolling volatility values appear after sufficient rows
- flag columns contain valid binary values

A second unit test was also added to check whether the function produce the expected results or not:
- `price_gain`
- `return_pct`
- `log_return`
- `cumulative_gain`


### 6.2 Integration Testing

An integration test was implemented to verify interaction between:
- MySQL database
- Flask backend
- dashboard frontend route

The integration test checked that:
- the MySQL connection is successful
- the stock table contains QCOM rows
- the Flask dashboard route `/` returns a successful response
- the dashboard page contains expected content
- a known real timestamp in the database contains the expected transformed values

This ensured that the different parts of the system work together correctly as a full pipeline.

---
