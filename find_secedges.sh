#!/bin/bash
set -ue

EXP_NUM=$1
GOLD_SALTO=$2
START=$3
END=$4
PY_DIR=scripts
DATA_DIR=experiment/data/ex0
EXP_DIR=experiment/data/ex$EXP_NUM

if [ ! -d $EXP_DIR ]; then
  mkdir $EXP_DIR
fi

echo "Finding raising and equi from LFG files..."
python $PY_DIR/find_control_from_LFG.py -r ../bestTrain/ $DATA_DIR
python $PY_DIR/find_control_from_LFG.py -e ../bestTrain/ $DATA_DIR

echo "Adding secondary edges into TIGER...(it will take quite a while, why not go and have a coffee)"
python $PY_DIR/process_tiger.py $DATA_DIR/tiger.orig.xml $DATA_DIR/tiger.auto.xml $DATA_DIR/raising_indices.txt $DATA_DIR/equi_indices.txt 123 > $DATA_DIR/process_tiger.log





