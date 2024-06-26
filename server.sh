#!/bin/bash

start() {
    echo "Starting Gunicorn..."
    source /home/ecs-user/miniconda3/etc/profile.d/conda.sh
    conda activate py310
    nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > trace.log 2>&1 &
    echo "Gunicorn started."
}

stop() {
    echo "Stopping Gunicorn..."
    pkill gunicorn
    echo "Gunicorn stopped."
}

restart() {
    stop
    start
}

case $1 in
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
