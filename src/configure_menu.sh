#!/bin/bash


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


EXEC_PATH="$SCRIPT_DIR/startmonitor"
if [ "$#" -ge 1 ]; then
    ## add prefix program
    EXEC_PATH="$1 $EXEC_PATH"
fi


## add udev rule
CONFIG_FILE=~/.local/share/applications/menulibre-stockmonitor.desktop


cat > $CONFIG_FILE << EOL
[Desktop Entry]
Name=Stock Monitor
GenericName=Stock Monitor
Comment=Monitor and tools for Stock Exchange.
Version=1.1
Type=Application
Exec=$EXEC_PATH
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/stockmonitor/gui/img/stock-black.png
Actions=
Categories=Office;
StartupNotify=true
Terminal=false

EOL


echo "File created in: $CONFIG_FILE"
