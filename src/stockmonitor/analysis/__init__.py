##
##
##

import os
import csv


def write_to_csv( file, headerList, dataFrame ):
    dirPath = os.path.dirname( file )
    os.makedirs( dirPath, exist_ok=True )

    with open(file, 'w', encoding="utf-8") as f:
        writer = csv.writer( f )
        for row in headerList:
            writer.writerow( row )

        writer.writerow( dataFrame.columns )
        rowsList = dataFrame.values.tolist()
        rowsList.sort( key=lambda x: x[0], reverse=True )           ## sort
        for row in rowsList:
            writer.writerow( row )
