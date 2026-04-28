#!/bin/bash
while true; do
  if ! kill -0 $1 2>/dev/null; then
    break
  fi
  sleep 1
done
