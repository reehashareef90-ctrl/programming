#!/bin/bash

PROJECT="/home/g20093595/project/programming"
PYTHON_BIN="$PROJECT/venv/bin/python"
SCRIPT_PATH="$PROJECT/scripts/fetch_qcom_1m_weekly.py"
LOG_FILE="$PROJECT/logs/fetch_qcom.log"
HISTORY_FILE="$PROJECT/run_history.csv"

mkdir -p "$PROJECT/logs"
cd "$PROJECT" || exit 1

git pull origin main >> "$LOG_FILE" 2>&1

OUTPUT=$("$PYTHON_BIN" "$SCRIPT_PATH" 2>&1)
STATUS=$?

echo "$OUTPUT" >> "$LOG_FILE"

ROWS=$(echo "$OUTPUT" | grep "Inserted/updated rows:" | awk '{print $3}' | tail -n 1)
ROWS=${ROWS:-0}

if [ $STATUS -eq 0 ]; then
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ'),success,$ROWS" >> "$HISTORY_FILE"
else
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ'),failed,0" >> "$HISTORY_FILE"
fi

git add run_history.csv
git commit -m "Weekly fetch $(date -u '+%Y-%m-%d %H:%M UTC')" >> "$LOG_FILE" 2>&1 || true
git push origin main >> "$LOG_FILE" 2>&1
