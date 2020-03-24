#!/bin/bash

x=1
while [ ! $x -eq 0 ]
do
  echo "Waiting for HTTP..."
  curl -I http://blockchain-finder:8080 --silent
  x=$?
  sleep 1
done

echo "HTTP OK!"

function tsunga() {
  template=$(cat /root/.tsung/tsung_template.xml)
  xml="${template/\%duration\%/$1}"
  xml="${xml/\%arrivalRate\%/$2}"
  echo $xml > /root/.tsung/tsung.xml
  tsung start

  cd ~/.tsung/log/ && cd $(ls ./ | tail -n 1) && /usr/local/lib/tsung/bin/tsung_stats.pl
  tsunga_res=$(tail -1 ./data/session.txt | cut -d' ' -f7)
  echo "$1 $2 $tsunga_res" >> /results.txt
}

echo "" > /results.txt

echo "Discover service rate"
tsunga "12" "0.05"
serviceTime=$tsunga_res
serviceRate=$(python -c "print 1.0/($serviceTime/1000.0)")
echo "Service time is $serviceTime, service rate is $serviceRate"

loads=("0.15" "0.25" "0.5" "0.75" "0.9" "0.95" "0.98")

for load in "${loads[@]}"
do
  echo "Testing load $load"
  arrivalRate=$(python -c "print $serviceRate*$load")
  tsunga "12" $arrivalRate
done
