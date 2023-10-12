#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


$SCRIPT_DIR/doc/generate-doc.sh

echo "checking links in MD files"
./tools/md_check_links.py -d $SCRIPT_DIR -i ".*venv.*;.*site-packages.*"

echo "generation completed"
