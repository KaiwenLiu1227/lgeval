import os
import os.path as osp

LG_EVAL_DIR = os.environ.get("LgEvalDir")
CROHMELIB_DIR = os.environ.get("CROHMELibDir")

LABELS_TRANS_CSV = osp.join(LG_EVAL_DIR, "translate", "infty_to_crohme.csv")
MATHML_MAP_DIR = osp.join(LG_EVAL_DIR, "translate", "mathMLMap.csv")
CROHMELIB_SRC_DIR = osp.join(CROHMELIB_DIR, "src")
CROHMELIB_GRAMMAR_DIR = osp.join(CROHMELIB_SRC_DIR, "Grammar")
MATHML_TXL_FILE = osp.join(CROHMELIB_SRC_DIR, "pprintMathML.Txl")
