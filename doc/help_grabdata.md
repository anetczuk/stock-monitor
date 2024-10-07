## <a name="main_help"></a> grabdata.py --help
```
usage: grabdata.py [-h] [-la] [--listtools]
                   {config_mode,all_current,gpw_curr_stock,gpw_curr_indexes,gpw_isin_data,gpw_stock_indicators,gpw_espi,gpw_curr_stock_intra,gpw_curr_index_intra,gpw_archive_data,div_cal,fin_reps_cal,pub_fin_reps_cal,global_indexes,metastock_intraday,curr_short_sell,hist_short_sell}
                   ...

stock data grabber

options:
  -h, --help            show this help message and exit
  -la, --logall         Log all messages
  --listtools           List tools

subcommands:
  select one of subcommands

  {config_mode,all_current,gpw_curr_stock,gpw_curr_indexes,gpw_isin_data,gpw_stock_indicators,gpw_espi,gpw_curr_stock_intra,gpw_curr_index_intra,gpw_archive_data,div_cal,fin_reps_cal,pub_fin_reps_cal,global_indexes,metastock_intraday,curr_short_sell,hist_short_sell}
                        data providers
    config_mode         Store data based on configuration file
    all_current         Store data from almost all providers using current
                        data if required
    gpw_curr_stock      GPW current stock
    gpw_curr_indexes    GPW current indexes (main, macro and sectors)
    gpw_isin_data       GPW ISIN data
    gpw_stock_indicators
                        GPW stock indicators
    gpw_espi            GPW ESPI
    gpw_curr_stock_intra
                        GPW current intraday stock data
    gpw_curr_index_intra
                        GPW current intraday index data
    gpw_archive_data    GPW archive data
    div_cal             Dividends calendar
    fin_reps_cal        Financial reports calendar
    pub_fin_reps_cal    Published financial reports calendar
    global_indexes      Global indexes
    metastock_intraday  MetaStock intraday data
    curr_short_sell     Current short sellings
    hist_short_sell     History short sellings
```



## <a name="config_mode_help"></a> grabdata.py config_mode --help
```
usage: grabdata.py config_mode [-h] -cp CONFIG_PATH

options:
  -h, --help            show this help message and exit
  -cp CONFIG_PATH, --config_path CONFIG_PATH
                        Path for config file.
```



## <a name="all_current_help"></a> grabdata.py all_current --help
```
usage: grabdata.py all_current [-h] [-f] -of OUT_FORMAT [-od OUT_DIR]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -od OUT_DIR, --out_dir OUT_DIR
                        Output directory
```



## <a name="gpw_curr_stock_help"></a> grabdata.py gpw_curr_stock --help
```
usage: grabdata.py gpw_curr_stock [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="gpw_curr_indexes_help"></a> grabdata.py gpw_curr_indexes --help
```
usage: grabdata.py gpw_curr_indexes [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="gpw_isin_data_help"></a> grabdata.py gpw_isin_data --help
```
usage: grabdata.py gpw_isin_data [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="gpw_stock_indicators_help"></a> grabdata.py gpw_stock_indicators --help
```
usage: grabdata.py gpw_stock_indicators [-h] [-f] [-of OUT_FORMAT]
                                        [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="gpw_espi_help"></a> grabdata.py gpw_espi --help
```
usage: grabdata.py gpw_espi [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="gpw_curr_stock_intra_help"></a> grabdata.py gpw_curr_stock_intra --help
```
usage: grabdata.py gpw_curr_stock_intra [-h] --isin ISIN [-f] [-of OUT_FORMAT]
                                        [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  --isin ISIN           ISIN
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="gpw_curr_index_intra_help"></a> grabdata.py gpw_curr_index_intra --help
```
usage: grabdata.py gpw_curr_index_intra [-h] --isin ISIN [-f] [-of OUT_FORMAT]
                                        [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  --isin ISIN           ISIN
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="gpw_archive_data_help"></a> grabdata.py gpw_archive_data --help
```
usage: grabdata.py gpw_archive_data [-h] [-d DATE] [-dr DATE_RANGE] [-f]
                                    [-of OUT_FORMAT] [-op OUT_PATH]
                                    [-od OUT_DIR]

options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  Archive date
  -dr DATE_RANGE, --date_range DATE_RANGE
                        Archive date range
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path (in case of single date)
  -od OUT_DIR, --out_dir OUT_DIR
                        Output directory (in case of range)
```



## <a name="div_cal_help"></a> grabdata.py div_cal --help
```
usage: grabdata.py div_cal [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="fin_reps_cal_help"></a> grabdata.py fin_reps_cal --help
```
usage: grabdata.py fin_reps_cal [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="pub_fin_reps_cal_help"></a> grabdata.py pub_fin_reps_cal --help
```
usage: grabdata.py pub_fin_reps_cal [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="global_indexes_help"></a> grabdata.py global_indexes --help
```
usage: grabdata.py global_indexes [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="metastock_intraday_help"></a> grabdata.py metastock_intraday --help
```
usage: grabdata.py metastock_intraday [-h] -d DATE [-dr DATE_RANGE] [-f]
                                      [-of OUT_FORMAT] [-op OUT_PATH]
                                      [-od OUT_DIR]

options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  Archive date
  -dr DATE_RANGE, --date_range DATE_RANGE
                        Archive date range
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path (in case of single date)
  -od OUT_DIR, --out_dir OUT_DIR
                        Output directory (in case of range)
```



## <a name="curr_short_sell_help"></a> grabdata.py curr_short_sell --help
```
usage: grabdata.py curr_short_sell [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```



## <a name="hist_short_sell_help"></a> grabdata.py hist_short_sell --help
```
usage: grabdata.py hist_short_sell [-h] [-f] [-of OUT_FORMAT] [-op OUT_PATH]

options:
  -h, --help            show this help message and exit
  -f, --force           Force refresh data
  -of OUT_FORMAT, --out_format OUT_FORMAT
                        Output format, one of: csv, xls, pickle. If none
                        given, then will be deduced based on extension of
                        output path.
  -op OUT_PATH, --out_path OUT_PATH
                        Output file path
```
