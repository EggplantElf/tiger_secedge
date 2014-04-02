#!/bin/bash

set -ue

EXP_DIR=$1


echo "making features for train..."
python make_features.py -train -i $EXP_DIR/tiger.train.conll09 -m $EXP_DIR/feat.map -o $EXP_DIR/tiger.train.features
echo "making features for predict..."
python make_features.py -test -i $EXP_DIR/tiger.gold.conll09 -m $EXP_DIR/feat.map -o $EXP_DIR/tiger.pred.features

echo "train and predict..."
liblinear/train $EXP_DIR/tiger.train.features $EXP_DIR/train.model
liblinear/predict $EXP_DIR/tiger.pred.features $EXP_DIR/train.model $EXP_DIR/pred.txt

echo "mapping back"
python make_features.py -mapback -i $EXP_DIR/tiger.gold.conll09 -m $EXP_DIR/feat.map -o $EXP_DIR/tiger.pred.conll09 -p $EXP_DIR/pred.txt

python evaluate_conll.py $EXP_DIR/tiger.pred.conll09 > $EXP_DIR/result.txt
cat $EXP_DIR/result.txt
