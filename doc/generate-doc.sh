#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


SRC_DIR="$SCRIPT_DIR/../src"


generate_main_help() {
    HELP_PATH=$SCRIPT_DIR/help_startmonitor.md
    TOOL_PATH="$SRC_DIR/startmonitor"
    
    echo "## <a name=\"main_help\"></a> startmonitor --help" > ${HELP_PATH}
    echo -e "\`\`\`" >> ${HELP_PATH}
    ${TOOL_PATH} --help >> ${HELP_PATH}
    echo -e "\`\`\`" >> ${HELP_PATH}
}


generate_grab_help() {
    HELP_PATH=$SCRIPT_DIR/help_grabdata.md
    TOOL_PATH="$SRC_DIR/grabdata.py"
    
    echo "## <a name=\"main_help\"></a> grabdata.py --help" > ${HELP_PATH}
    echo -e "\`\`\`" >> ${HELP_PATH}
    ${TOOL_PATH} --help >> ${HELP_PATH}
    echo -e "\`\`\`" >> ${HELP_PATH}
    
    
    tools=$(${TOOL_PATH} --listtools)
    
    IFS=', ' read -r -a tools_list <<< "$tools"
    
    
    for item in ${tools_list[@]}; do
        echo $item
        echo -e "\n\n" >> ${HELP_PATH}
        echo "## <a name=\"${item}_help\"></a> grabdata.py $item --help" >> ${HELP_PATH}
        echo -e "\`\`\`" >> ${HELP_PATH}
        ${TOOL_PATH} $item --help >> ${HELP_PATH}
        echo -e "\`\`\`"  >> ${HELP_PATH}
    done
}


generate_transaction_help() {
    HELP_PATH=$SCRIPT_DIR/help_transactioninfo.md
    TOOL_PATH="$SRC_DIR/transactioninfo.py"
    
    echo "## <a name=\"main_help\"></a> transactioninfo.py --help" > ${HELP_PATH}
    echo -e "\`\`\`" >> ${HELP_PATH}
    ${TOOL_PATH} --help >> ${HELP_PATH}
    echo -e "\`\`\`" >> ${HELP_PATH}
    
    
    tools=$(${TOOL_PATH} --listtools)
    
    IFS=', ' read -r -a tools_list <<< "$tools"
    
    
    for item in ${tools_list[@]}; do
        echo $item
        echo -e "\n\n" >> ${HELP_PATH}
        echo "## <a name=\"${item}_help\"></a> transactioninfo.py $item --help" >> ${HELP_PATH}
        echo -e "\`\`\`" >> ${HELP_PATH}
        ${TOOL_PATH} $item --help >> ${HELP_PATH}
        echo -e "\`\`\`"  >> ${HELP_PATH}
    done
}


generate_main_help
generate_grab_help
generate_transaction_help

$SCRIPT_DIR/generate_small.sh
