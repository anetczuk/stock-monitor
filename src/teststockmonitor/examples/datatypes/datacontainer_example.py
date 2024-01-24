#!/usr/bin/env python3
##
##
##

try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

from stockmonitor.datatypes.datacontainer import DataContainer
from stockmonitor.datatypes.wallettypes import TransactionMatchMode
from teststockmonitor.data import load_yaml


if __name__ == '__main__':

    # isin name ticker map: https://www.gpw.pl/pub/GPW/files/link1.pdf

    trans_dict = load_yaml("trans_alior.yaml")

    dataContainer = DataContainer()
    dataContainer.userContainer.transactionsMatchMode = TransactionMatchMode.OLDEST

    dataContainer.importWalletDict( trans_dict, True )
    wallet = dataContainer.wallet
    # wallet_dict = obj_to_dict( wallet, skip_meta_data=True )
    # pprint.pprint(wallet_dict)

    dataContainer.userContainer.transactionsMatchMode = TransactionMatchMode.OLDEST
    wallet_data = dataContainer.getWalletState()
    print("wallet oldest match summary:", wallet_data)

    dataContainer.importWalletDict( trans_dict, False )
    wallet = dataContainer.wallet
    # wallet_dict = obj_to_dict( wallet, skip_meta_data=True )
    # pprint.pprint(wallet_dict)

    dataContainer.userContainer.transactionsMatchMode = TransactionMatchMode.OLDEST
    wallet_data = dataContainer.getWalletState()
    print("wallet oldest match summary:", wallet_data)
