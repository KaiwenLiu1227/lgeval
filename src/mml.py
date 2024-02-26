import os
import sys
import csv
import re
import os.path as osp

from lgeval.src.lg import Lg
import lgeval.src.lg2txt as lg2txt
from lgeval.src.settings import (
    LABELS_TRANS_CSV,
    MATHML_MAP_DIR,
    CROHMELIB_SRC_DIR,
    CROHMELIB_GRAMMAR_DIR,
    MATHML_TXL_FILE,
)


def readMapFile(mapFile):
    """Read in symbol and structure mappings from a file."""
    try:
        fileReader = csv.reader(open(mapFile))
    except:
        sys.stderr.write("  !! IO Error (cannot open): " + mapFile + "\n")
        return

    symbolsMap = {}
    relationsMap = {}
    readingSymbols = True
    for row in fileReader:
        # Skip blank lines and comments.
        if len(row) == 0:
            continue
        elif row[0].strip()[0] == "#":
            continue
        elif row[0].strip() == "SYMBOLS":
            readingSymbols = True
        elif row[0].strip() == "RELATIONSHIPS":
            readingSymbols = False
        else:
            if readingSymbols:
                symbolsMap[row[0]] = row[1]
            else:
                relationsMap[row[0]] = row[1]
    return symbolsMap, relationsMap


def get_mml(filename, translate=True):
    temp_lg = osp.join(osp.split(filename)[0], "temp_" + osp.split(filename)[1])
    inputFile = Lg(filename)
    lg_NE_string = inputFile.csv()
    if translate:
        symbolsMap, relationsMap = readMapFile(LABELS_TRANS_CSV)
        edge_pattern = re.compile(r"^E,")
        node_pattern = re.compile(r"(^N,)|#")
        symbol_temp = relabel(lg_NE_string, symbolsMap, node_pattern)
        edge_temp = relabel(
            lg_NE_string, dict(**symbolsMap, **relationsMap), edge_pattern
        )
        lg_NE_string = symbol_temp + "\n" + edge_temp
    print("\n" + temp_lg)
    with open(temp_lg, "w") as f:
        f.writelines(lg_NE_string)

    try:
        mml_out = lg2txt.main(temp_lg, MATHML_MAP_DIR)
    except:
        mml_out = ""
    return mml_out


def relabel(lg_NE_string, Map, pattern):
    temp = "\n".join(
        [line for line in lg_NE_string.split("\n") if re.match(pattern, line)]
    )
    for source_label, mapped_label in Map.items():
        temp = temp.replace("," + source_label + ",", "," + mapped_label + ",")
    return temp


if __name__ == "__main__":
    filename = sys.argv[1]
    get_mml(filename)
