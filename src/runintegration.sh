#!/bin/bash

set -eux

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


$SCRIPT_DIR/teststockdataaccess/dataaccess/intgr_finreportscalendardata.py


echo -e "\nall tests completed"
