#!/bin/bash

set -eux

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


$SCRIPT_DIR/teststockdataaccess/dataaccess/intgr_finreportscalendardata.py

$SCRIPT_DIR/testintegration/dividendscalendardata.py

$SCRIPT_DIR/teststockmonitor/integration/checkintegration.py


echo -e "\nall tests completed"
