################################################################
# confHists.py
#
# Create confusion histograms.
#
# Author: R. Zanibbi, Oct. 2014
# Copyright (c) 2014 Richard Zanibbi and Harold Mouchere
################################################################

import sys
import csv
import time
import os
import argparse
from glob import glob

from lgeval.src.lg import *
from lgeval.src.lgio import *
import lgeval.src.SmGrConfMatrix as SmGrConfMatrix
import lgeval.src.compareTools as compareTools


def main(
    fileList,
    minCount=1,
    confMat=False,
    confMatObj=True,
    subgraphSize=1,
    img_dir="",
    dotpdf_dir="",
):
    fileReader = csv.reader(open(fileList), delimiter=" ")
    htmlStream = None

    matrix = SmGrConfMatrix.ConfMatrix()
    matrixObj = SmGrConfMatrix.ConfMatrixObject()
    pdf_count = 0
    if os.path.exists(dotpdf_dir):
        pdf_count = len(glob(os.path.join(dotpdf_dir, "*.pdf")))

    if pdf_count == 0:
        dotpdf_dir = "confHist_outputs/dotpdfs"
        print(
            "\nlg2dot comparison output pdfs not found. Generating pdfs at {} ...\n".format(
                dotpdf_dir
            )
        )
        if not os.path.exists(dotpdf_dir):
            os.makedirs(dotpdf_dir)

    for row in fileReader:
        # Skip comments and empty lines.
        if not row == [] and not row[0].strip()[0] == "#":
            # print(row)
            lgfile1 = row[0].strip()  # remove leading/trailing whitespace
            lgfile2 = row[1].strip()
            # Here lg1 is input; lg2 is ground truth/comparison
            lg1 = Lg(lgfile1)
            lg2 = Lg(lgfile2)
            out = lg1.compare(lg2)

            nodeClassErr = set()
            edgeErr = set()
            if confMat or confMatObj:
                for (n, _, _) in out[1]:
                    nodeClassErr.add(n)
                for (e, _, _) in out[2]:
                    edgeErr.add(e)

            (head, tail) = os.path.split(lgfile1)
            (base, _) = os.path.splitext(tail)
            fileName = base + ".lg"
            if pdf_count == 0:
                os.system(
                    "python $LgEvalDir/src/lg2dot.py "
                    + lgfile1
                    + " "
                    + lgfile2
                    + " >"
                    + os.path.join(dotpdf_dir, base + ".dot")
                )
                os.system(
                    "dot -Tpdf "
                    + os.path.join(dotpdf_dir, base + ".dot")
                    + " -o "
                    + os.path.join(dotpdf_dir, base + ".pdf")
                )
            if confMat:
                # Subgraphs of 2 or 3 primitives.
                for (gt, er) in lg1.compareSubStruct(lg2, [subgraphSize]):
                    er.rednodes = set(list(er.nodes)) & nodeClassErr
                    er.rededges = set(list(er.edges)) & edgeErr
                    matrix.incr(gt, er, fileName)
            if confMatObj:
                # Object subgraphs of 2 objects.
                for (obj, gt, er) in lg1.compareSegmentsStruct(lg2, [subgraphSize]):
                    er.rednodes = set(list(er.nodes)) & nodeClassErr
                    er.rededges = set(list(er.edges)) & edgeErr
                    matrixObj.incr(obj, gt, er, fileName)

    htmlStream = None

    objTargets = matrixObj.size()
    primTargets = matrix.size()

    # HTML header output
    fileList_head, fileList_tail = os.path.split(fileList)
    if not fileList_head:
        fileList_head = "confHist_outputs"
    fileList_tail = (
        fileList_tail + "__size_" + str(subgraphSize) + "_min_" + str(minCount)
    )
    print(
        "\nGenerating HTML at "
        + os.path.join(fileList_head, "CH_" + fileList_tail + ".html")
    )
    htmlStream = open(os.path.join(fileList_head, "CH_" + fileList_tail + ".html"), "w")
    htmlStream.write(
        '<meta charset="UTF-8">\n<html xmlns="http://www.w3.org/1999/xhtml">\n'
    )
    htmlStream.write("<head>\n")

    # Code to support 'select all' checkboxes
    # Essentially registering callback functions to checkbox click events.
    # Make sure to include JQuery (using version 2.1.1 for now)
    htmlStream.write(
        '<script src="http://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>\n'
    )
    htmlStream.write(
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/1.0.0/FileSaver.min.js"></script>\n'
    )

    # (Excuse the mess..) create callbacks for checkbox events, save button
    # which saves the unique list of selected files in sorted order.
    # This was a slow, painful way to do this - perhaps an 'include' would be better.
    JS_DIR = os.path.join(fileList_head, "js")
    if not os.path.exists(JS_DIR):
        os.makedirs(JS_DIR)
    jsStream = open(os.path.join(JS_DIR, "functions.js"), "w")
    jsStream.write(
        "$(function(){ \n"
        + '    $("#savebutton").click(function () { \n'
        + '       var output = ""; \n'
        + '       var selections = $(".fileCheck:checked"); \n'
        + '       var fileString = ""; \n'
        + "       for (i=0; i < selections.length; i++) { \n"
        + '            fileString = selections[i].value.concat(" ").concat(fileString); \n'
        + "                                console.log(fileString); \n"
        + "        } \n"
        + '                   fileList = fileString.split(" "); \n'
        + "       fileList.sort(); \n"
        + "       var uniqueSels = []; \n"
        + '       var last = ""; \n'
        + "       for (i=0; i < fileList.length; i++) { \n"
        + "         if (fileList[i] != last) { \n"
        + "            uniqueSels.push( fileList[i]); \n"
        + "            last = fileList[i]; \n"
        + "         } \n"
        + "        } \n"
        + '       output = uniqueSels.join("\\n"); \n'
        + '       var blob = new Blob([ output ], {type: "text/plain;charset=utf-8"}); \n'
        + '       saveAs(blob, "selectedFiles.txt"); \n'
        + "    }); \n"
        + '    $(":checkbox").click(function () { \n'
        + "                        var current = this.id; \n"
        + '                        var re = new RegExp(this.id + "[0-9]","i"); \n'
        + '                        var elementsCommonIdPrefix = $("[id^=" + this.id + "]").filter(function() { \n'
        + '                                return current == "Obj" || ! this.id.match(re); }); \n'
        + '                        console.log(this.id + " Matched: " + elementsCommonIdPrefix.length); \n'
        + "                        var parentId = this.id.match(/[a-zA-Z]+[0-9]+[a-zA-Z]+[0-9]+/); \n"
        + "                        var grandparentId = this.id.match(/[a-zA-Z]+[0-9]+/); \n"
        + "                        if ( ! this.checked ) { \n"
        + '                            elementsCommonIdPrefix.prop("checked",false); \n'
        + "                            if (parentId != null ) \n"
        + '                                $("[id=" + parentId + "]").prop("checked", false); \n'
        + "                            if (grandparentId != null) \n"
        + '                                    $("[id=" + grandparentId + "]").prop("checked", false); \n'
        + '                            if ($("[id=Obj]") != null) \n'
        + '                                    $("[id=Obj]").prop("checked", false); \n'
        + "            } else { \n"
        + '                            elementsCommonIdPrefix.prop("checked", true); \n'
        + '                            var pDescendents = $("[id^=" + parentId + "]"); \n'
        + '                        var pDescChecked = $("[id^=" + parentId + "]:checked"); \n'
        + "                            if (parentId != null && pDescendents.length == pDescChecked.length + 1 ) \n"
        + '                                    $("[id=" + parentId + "]").prop("checked", true); \n'
        + '                            var gDescendents = $("[id^=" + grandparentId + "]"); \n'
        + '                                var gDescChecked = $("[id^=" + grandparentId + "]:checked"); \n'
        + "                                if (grandparentId != null && gDescendents.length == gDescChecked.length + 1 ) \n"
        + '                                    $("[id=" + grandparentId + "]").prop("checked", true); \n'
        + '                                var aDescendents = $("[id^=Obj]"); \n'
        + '                                var aDescChecked = $("[id^=Obj]:checked"); \n'
        + '                                if ($("[id=Obj]") != null && aDescendents.length == aDescChecked.length + 1 ) \n'
        + '                                    $("[id=Obj]").prop("checked", true); \n'
        + "                        } \n"
        + "                }); \n"
        + "}); \n"
    )
    jsStream.close()

    # Style
    CSS_DIR = os.path.join(fileList_head, "css")
    if not os.path.exists(CSS_DIR):
        os.makedirs(CSS_DIR)
    cssStream = open(os.path.join(CSS_DIR, "style.css"), "w")
    cssStream.write('<style type="text/css">\n')
    cssStream.write("svg { overflow: visible; }\n")
    cssStream.write("p { line-height: 125%; }\n")
    cssStream.write("li { line-height: 125%; }\n")
    cssStream.write("button { font-size: 12pt; }\n")
    cssStream.write(
        "td { font-size: 10pt; align: left; text-align: left; border: 1px solid lightgray; padding: 5px; }\n"
    )
    cssStream.write(
        "th { font-size: 10pt; font-weight: normal; border: 1px solid lightgray; padding: 10px; background-color: lavender; text-align: left }\n"
    )
    cssStream.write("tr { padding: 4px; }\n")
    cssStream.write("table { border-collapse:collapse;}\n")
    cssStream.write("</style>")
    cssStream.close()

    htmlStream.write('<script src="js/functions.js"></script>\n')
    htmlStream.write('<link rel="stylesheet" href="css/style.css">\n')
    htmlStream.write('</head>\n\n<font face="helvetica,arial,sans-serif">')
    htmlStream.write("<h2>LgEval Structure Confusion Histograms</h2>")
    htmlStream.write(time.strftime("%c"))
    htmlStream.write("<p><b>" + fileList_tail + "</b><br>")
    htmlStream.write("<b>Subgraphs:</b> " + str(subgraphSize) + " node(s)<br>")
    htmlStream.write("<br>")
    htmlStream.write(
        "<p><b>Note:</b> Only primitive-level graph confusions occurring at least "
        + str(minCount)
        + " times appear below.<br><Note:</b><b>Note:</b> Individual primitive errors may appear in multiple error graphs (e.g. due to segmentation errors).</p>"
    )
    htmlStream.write("<UL>")

    if confMatObj:
        htmlStream.write(
            '<LI><A HREF="#Obj">Object histograms</A> ('
            + str(objTargets)
            + " incorrect targets; "
            + str(matrixObj.errorCount())
            + " errors)"
        )
    if confMat:
        htmlStream.write(
            '<LI><A HREF="#Prim">Primitive histograms</A> ('
            + str(primTargets)
            + " incorrect targets; "
            + str(matrix.errorCount())
            + " errors)"
        )
    htmlStream.write("</UL>")

    htmlStream.write(
        '<button type="button" font-size="12pt" id="savebutton">&nbsp;&nbsp;Save Selected Files&nbsp;&nbsp;</button>'
    )
    htmlStream.write("\n<hr>\n")

    if confMatObj:
        htmlStream.write('<h2><A NAME="#Obj">Object Confusion Histograms</A></h2>')
        htmlStream.write("<p>\n")
        htmlStream.write(
            "Object structures recognized incorrectly are shown at left, sorted by decreasing frequency. "
            + str(objTargets)
            + " incorrect targets, "
            + str(matrixObj.errorCount())
            + " errors."
        )
        htmlStream.write("</p>\n")
        matrixObj.toHTML(
            htmlStream,
            minCount,
            "",
            fileList=fileList_tail,
            img_dir=img_dir,
            dotpdf_dir=os.path.join("../..", dotpdf_dir),
        )

    if confMat:
        htmlStream.write("<hr>\n")
        htmlStream.write('<h2><A NAME="Prim">Primitive Confusion Histograms</A></h2>')
        htmlStream.write(
            "<p>Primitive structure recognizes incorrectly are shown at left, sorted by decreasing frequency. "
            + str(primTargets)
            + " incorrect targets, "
            + str(matrix.errorCount())
            + " errors.</p>"
        )

        # Enforce the given limit for all reported errors for primitives.
        matrix.toHTML(
            htmlStream,
            minCount,
            minCount,
            "",
            primitive=True,
            fileList=fileList_tail,
            img_dir=img_dir,
            dotpdf_dir=os.path.join("../..", dotpdf_dir),
        )

    htmlStream.write("</html>")
    htmlStream.close()


def parse_args():
    parser = argparse.ArgumentParser(description="ConfHist Arguments")
    parser.add_argument(
        "--fileList",
        type=str,
        required=True,
        help="The file containing list of lg file pairs to evaluate",
    )
    parser.add_argument(
        "-gs",
        "--graphSize",
        type=int,
        required=True,
        help="The number of objects/primitives in targets to analyze",
    )
    parser.add_argument(
        "-m",
        "--minCount",
        type=int,
        default=1,
        help="The minimum number of times an error should occur",
    )
    parser.add_argument(
        "-s",
        "--strokes",
        type=int,
        default=0,
        help="Flag whether to construct stroke (primitive) confusion histograms",
    )
    parser.add_argument(
        "-i",
        "--lgimgDir",
        type=str,
        help="The directory containing the expression images of the lg files",
    )
    parser.add_argument(
        "-p",
        "--dotpdfDir",
        type=str,
        help="The directory containing the lg2dot comparison pdf outputs",
    )
    parser.add_argument(
        "-sp",
        "--split",
        type=int,
        default=0,
        help="Flag whether to construct stroke (primitive) confusion histograms",
    )
    parser.add_argument(
        "-f",
        "--filter",
        type=int,
        default=1,
        help="Flag whether to construct stroke (primitive) confusion histograms",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    
    img_dir = os.path.join("../..", args.lgimgDir)
    main(
        args.fileList,
        minCount=args.minCount,
        confMat=bool(args.strokes),
        subgraphSize=args.graphSize,
        img_dir=img_dir,
        dotpdf_dir=args.dotpdfDir,
    )
