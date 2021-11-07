#!/bin/bash


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


## add udev rule
CONFIG_FILE=~/.config/autostart/stockmonitor.desktop


cat > $CONFIG_FILE << EOL
[Desktop Entry]
Name=Stock Monitor
GenericName=Stock Monitor
Comment=Monitor and tools for Stock Exchange.
Type=Application
Categories=Office;
Exec=$SCRIPT_DIR/startmonitor --minimized
Icon=$SCRIPT_DIR/stockmonitor/gui/img/stock-black.png
Terminal=false
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOL


echo "File created in: $CONFIG_FILE"
