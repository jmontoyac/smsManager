if pgrep -f "python3.6 /home/fenix/firebase.py" &>/dev/null; then
    echo "firebase commands process is already running"
    exit
else
    echo "starting firebase commands process"
    python3.6 /home/fenix/firebase.py
fi
