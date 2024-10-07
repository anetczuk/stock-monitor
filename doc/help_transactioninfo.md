## <a name="main_help"></a> transactioninfo.py --help
```
usage: transactioninfo.py [-h] [-la] [--listtools]
                          {buysell,current,currentbuy,walletvaluehistory,walletgainhistory,walletprofithistory}
                          ...

stock data grabber

options:
  -h, --help            show this help message and exit
  -la, --logall         Log all messages
  --listtools           List tools

subcommands:
  select one of subcommands

  {buysell,current,currentbuy,walletvaluehistory,walletgainhistory,walletprofithistory}
                        extract mode
    buysell             Extract buy and matched sell transactions
    current             Extract current state of wallet
    currentbuy          Extract list of current buy transactions
    walletvaluehistory  Extract history of wallet value
    walletgainhistory   Extract history of wallet gain of sold stock
    walletprofithistory
                        Extract history of wallet profit
```



## <a name="buysell_help"></a> transactioninfo.py buysell --help
```
usage: transactioninfo.py buysell [-h] [-th TRANSHISTORY]
                                  [--trans_out_file TRANS_OUT_FILE]

options:
  -h, --help            show this help message and exit
  -th TRANSHISTORY, --transhistory TRANSHISTORY
                        Path to file with history of transactions
  --trans_out_file TRANS_OUT_FILE
                        Path to file with transactions (supported .json, .xls,
                        .xlsx, .csv extensions)
```



## <a name="current_help"></a> transactioninfo.py current --help
```
usage: transactioninfo.py current [-h] [-th TRANSHISTORY]
                                  [--trans_out_file TRANS_OUT_FILE]

options:
  -h, --help            show this help message and exit
  -th TRANSHISTORY, --transhistory TRANSHISTORY
                        Path to file with history of transactions
  --trans_out_file TRANS_OUT_FILE
                        Path to file with transactions (supported .json, .xls,
                        .xlsx, .csv extensions)
```



## <a name="currentbuy_help"></a> transactioninfo.py currentbuy --help
```
usage: transactioninfo.py currentbuy [-h] [-th TRANSHISTORY]
                                     [--trans_out_file TRANS_OUT_FILE]

options:
  -h, --help            show this help message and exit
  -th TRANSHISTORY, --transhistory TRANSHISTORY
                        Path to file with history of transactions
  --trans_out_file TRANS_OUT_FILE
                        Path to file with transactions (supported .json, .xls,
                        .xlsx, .csv extensions)
```



## <a name="walletvaluehistory_help"></a> transactioninfo.py walletvaluehistory --help
```
usage: transactioninfo.py walletvaluehistory [-h] [-th TRANSHISTORY]
                                             [--out_file OUT_FILE]

options:
  -h, --help            show this help message and exit
  -th TRANSHISTORY, --transhistory TRANSHISTORY
                        Path to file with history of transactions
  --out_file OUT_FILE   Path to file with output (supported .json, .xls,
                        .xlsx, .csv extensions)
```



## <a name="walletgainhistory_help"></a> transactioninfo.py walletgainhistory --help
```
usage: transactioninfo.py walletgainhistory [-h] [-th TRANSHISTORY]
                                            [--out_file OUT_FILE]

options:
  -h, --help            show this help message and exit
  -th TRANSHISTORY, --transhistory TRANSHISTORY
                        Path to file with history of transactions
  --out_file OUT_FILE   Path to file with output (supported .json, .xls,
                        .xlsx, .csv extensions)
```



## <a name="walletprofithistory_help"></a> transactioninfo.py walletprofithistory --help
```
usage: transactioninfo.py walletprofithistory [-h] [-th TRANSHISTORY]
                                              [--overall]
                                              [--out_file OUT_FILE]

options:
  -h, --help            show this help message and exit
  -th TRANSHISTORY, --transhistory TRANSHISTORY
                        Path to file with history of transactions
  --overall             Include gain of sold transactions
  --out_file OUT_FILE   Path to file with output (supported .json, .xls,
                        .xlsx, .csv extensions)
```
