#!/bin/bash

ACTION=$1

start() {
    echo "Starting Gunicorn..."
    nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > gunicorn.log 2>&1 &
    echo "Gunicorn started."
}

stop() {
    echo "Stopping Gunicorn..."
    PID=`pidof gunicorn`
    if [ -n "$PID" ]; then
        kill $PID
        echo "Gunicorn stopped."
    else
        echo "Gunicorn is not running."
    fi
}

restart() {
    stop
    start
}

case $ACTION in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        ;;
esac
