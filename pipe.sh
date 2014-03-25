#!/bin/bash

set -ue

EXP_DIR=$1

echo "step1"
./step1_find_MA.sh  $EXP_DIR    tiger.gold.conll09      tiger.pred.MA.conll09
echo "step2"
./step2_find_C.sh   $EXP_DIR    tiger.pred.MA.conll09   tiger.pred.MAC.conll09
echo "step3"
./step3_find_RE.sh  $EXP_DIR    tiger.pred.MAC.conll09  tiger.pred.MARE.conll09

python scripts/evaluate_conll.py $EXP_DIR/tiger.pred.MARE.conll09