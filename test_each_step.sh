#!/bin/bash

set -ue

EXP_DIR=$1


echo "step 1"
echo "step 1" >> $EXP_DIR/result.log

./step1_find_MA.sh  $EXP_DIR    tiger.gold.conll09      tiger.pred.MA.conll09
python scripts/evaluate_conll.py $EXP_DIR/tiger.pred.MA.conll09 >> $EXP_DIR/result.log



echo "step 2"
echo "step 2" >> $EXP_DIR/result.log

sed 's/SB[RE]/SBC/g' $EXP_DIR/tiger.gold.conll09 > $EXP_DIR/tiger.gold.C.conll09
./step2_find_C.sh   $EXP_DIR    tiger.gold.C.conll09    tiger.pred.C.conll09
python scripts/evaluate_conll.py $EXP_DIR/tiger.pred.C.conll09 >> $EXP_DIR/result.log


echo "step 3"
echo "step 3" >> $EXP_DIR/result.log

cut -f 1-13 $EXP_DIR/tiger.gold.conll09 > tmp1
cut -f 13 $EXP_DIR/tiger.gold.C.conll09 > tmp2
cut -f 15 $EXP_DIR/tiger.gold.conll09 > tmp3
cut -f 15 $EXP_DIR/tiger.gold.C.conll09 > tmp4
paste -d "\t" tmp1 tmp2 tmp3 tmp4 > $EXP_DIR/tiger.gold.RE.C.conll09
rm tmp1 tmp2 tmp3 tmp4



./step3_find_RE.sh  $EXP_DIR    tiger.gold.RE.C.conll09    tiger.pred.RE.conll09

python scripts/evaluate_conll.py $EXP_DIR/tiger.pred.RE.conll09 >> $EXP_DIR/result.log

