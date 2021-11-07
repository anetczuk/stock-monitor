#!/bin/bash


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


## add udev rule
CONFIG_FILE=~/.local/share/applications/menulibre-stockmonitor.desktop


cat > $CONFIG_FILE << EOL
[Desktop Entry]
Name=Stock Monitor
GenericName=Stock Monitor
Comment=Monitor and tools for Stock Exchange.
Version=1.1
Type=Application
Exec=$SCRIPT_DIR/startmonitor
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/stockmonitor/gui/img/stock-black.png
Actions=
Categories=Office;
StartupNotify=true
Terminal=false

EOL


echo "File created in: $CONFIG_FILE"
