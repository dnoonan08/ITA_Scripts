#!/bin/bash
# usage: watch.sh <your_command> <sleep_duration>

while :;
  do
  clear
  date
  tail $1
  sleep ${2:-5}
done
