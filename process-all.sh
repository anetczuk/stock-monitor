#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


$SCRIPT_DIR/doc/generate-doc.sh

./tools/checkall.sh

echo "processing completed"
