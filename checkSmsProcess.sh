if pgrep -f "python3.6 /home/fenix/sms.py" &>/dev/null; then
    echo "sms process is already running"
    exit
else
    echo "starting sms process"
    python3.6 /home/fenix/sms.py
fi
