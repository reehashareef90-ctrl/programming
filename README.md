# programming for Data Analysis
-This project is about building an automated data pipeline for Qualcomm (QCOM) 1-minute stock market data and analyze this data
-It is being developed step by step on a virtual machine, with GitHub for storing all scripts and MariaDB/MySQL used for storage.
# Major Steps
- Fetching regular QCOM 1-minute stock data from more than two months from Yahoo Finance
- Imported older historical CSV files that were collected earlier using google colab
- Combined both historical and recent data into one structure
- Made fetching automatic using cron jobs
  # ####### Data Cleaning ######
- The imported and fetched data has been cleaned.
- Sorted rows by timestamp
- Removed duplicate timestamps
- Making sure only unique timestamp rows remain in the database
- Stored all data in a SQL database
  # ############ Useful key Tranformation s########
- Calculated useful analytical values from the raw data i.e.
- gain and loss
- minute-to-minute return movement
- volatility using standard deviation
- unusual behavior in price, volume, and volatility
  # ######## Monthly summary Table ###
- Created another table for monthly summaries i.e., monthly low, monthly high, monthly median close, monthly gain/loss
monthly gain/loss percentage, total volume, average realized volatility
- Made Flask dashboard to show results
