#!/bin/bash

x=1
while [ ! $x -eq 0 ]
do
  echo "Waiting for HTTP..."
  curl -I http://blockchain-finder:8080 --silent
  x=$?
  sleep 1
done

echo "HTTP OK, starting tsung..."
tsung start
cd ~/.tsung/log/ && cd $(ls ./ | tail -n 1) && /usr/local/lib/tsung/bin/tsung_stats.pl
