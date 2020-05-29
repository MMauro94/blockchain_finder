#!/bin/bash

x=1
while [ ! $x -eq 0 ]
do
  echo "Waiting for HTTP..."
  curl -I http://blockchain-finder:8081 --silent
  x=$?
  sleep 1
done

echo "HTTP OK!"

function tsunga_start() {
  tsung start -m /root/.tsung/log/mon.txt

  cd ~/.tsung/log/ && cd $(ls ./ | tail -n 1) && /usr/local/lib/tsung/bin/tsung_stats.pl
  tsunga_res=$(tail -1 ./data/request.txt | cut -d' ' -f7)
}

function tsunga() {
  template=$(cat /root/.tsung/tsung_template.xml)
  xml="${template/\%duration\%/$1}"
  xml="${xml/\%arrivalRate\%/$2}"
  echo $xml > /root/.tsung/tsung.xml

  tsunga_start
  echo "$1 $2 $tsunga_res" >> /results.txt
}

function tsunga_servicerate() {
  xml=$(cat /root/.tsung/tsung_servicerate.xml)
  echo $xml > /root/.tsung/tsung.xml
  tsunga_start
}

python3 fill-cache.py

echo "" > /results.txt
#echo "Discover service rate"
#tsunga_servicerate
#serviceTime=$tsunga_res
#serviceRate=$(python -c "print 1.0/($serviceTime/1000.0)")
#echo "Service time is $serviceTime, service rate is $serviceRate"
#echo "Service time is $serviceTime, service rate is $serviceRate" >> /results.txt

serviceRate="0.007114754999999998"

loads=("0.1" "0.2" "0.3" "0.4" "0.5" "0.6" "0.65" "0.7" "0.75" "0.8" "0.85" "0.9" "0.95" "0.99")
#loads=("0.75" "0.76" "0.77" "0.78" "0.79" "0.8" "0.85")

for load in "${loads[@]}"
do
  #time=$(python -c "print max(10, int($load*30))")
  time=10
  echo "Testing load $load for $time min"
  arrivalRate=$(python -c "print $serviceRate*$load")
  tsunga $time $arrivalRate
done