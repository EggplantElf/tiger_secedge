#!/bin/bash

set -ue

EXP_DIR=$1


echo "making features for train..."
python make_features_find_SBC.py -train -i $EXP_DIR/tiger.train.MAC.conll09 -m $EXP_DIR/find_SBC.map -o $EXP_DIR/find_SBC_train.features
echo "making features for predict..."
python make_features_find_SBC.py -test -i $EXP_DIR/tiger.gold.conll09 -m $EXP_DIR/find_SBC.map -o $EXP_DIR/find_SBC_test.features

echo "train and predict..."
liblinear/train $EXP_DIR/find_SBC_train.features $EXP_DIR/find_SBC.model
liblinear/predict $EXP_DIR/find_SBC_test.features $EXP_DIR/find_SBC.model $EXP_DIR/find_pred.txt

echo "mapping back"
python make_features_find_SBC.py -mapback -i $EXP_DIR/tiger.gold.conll09 -m $EXP_DIR/find_SBC.map -o $EXP_DIR/tiger.pred.MAC.conll09 -p $EXP_DIR/find_pred.txt

# echo "evaluating...(not important here)"
# python evaluate.py gold.txt pred.txt
