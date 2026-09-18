#!/usr/bin/env bash
cd /app
awk '{print $1}' access.log | sort | uniq -c | sort -k1,1nr -k2,2 | head -5 | awk '{print $1, $2}' > top_ips.txt
awk '$9 ~ /^5/ {print $7}' access.log | sort -u > errors.txt
t=$(wc -l < access.log); e=$(awk '$9 ~ /^[45]/' access.log | wc -l); u=$(awk '{print $1}' access.log | sort -u | wc -l)
echo "total=$t errors=$e unique_ips=$u" > summary.txt
