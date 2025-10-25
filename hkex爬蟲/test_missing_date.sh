#!/bin/bash
# Test if Oct 4 page exists
echo "Testing Oct 4 date page..."
curl -s -o /dev/null -w "%{http_code}" "https://www.hkex.com.hk/chi/stat/smstat/dayquot/d251004c.htm"
echo ""
echo ""
echo "Testing Oct 7 date page..."
curl -s -o /dev/null -w "%{http_code}" "https://www.hkex.com.hk/chi/stat/smstat/dayquot/d251007c.htm"
echo ""
