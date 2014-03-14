#!/bin/bash

set -ue

EXP_DIR=$1

echo "making features for train..."
python make_features_map_SBC.py -train -i $EXP_DIR/tiger.train.conll09 -m $EXP_DIR/map_SBC.map -o $EXP_DIR/map_SBC_train.features
echo "making features for predict..."
python make_features_map_SBC.py -test -i $EXP_DIR/tiger.pred.MAC.conll09 -m $EXP_DIR/map_SBC.map -o $EXP_DIR/map_SBC_test.features

echo "train and predict..."
liblinear/train $EXP_DIR/map_SBC_train.features $EXP_DIR/map_SBC.model
liblinear/predict $EXP_DIR/map_SBC_test.features $EXP_DIR/map_SBC.model $EXP_DIR/map_pred.txt

echo "mapping back"
python make_features_map_SBC.py -mapback -i $EXP_DIR/tiger.pred.MAC.conll09 -m $EXP_DIR/map_SBC.map -o $EXP_DIR/tiger.pred.conll09 -p $EXP_DIR/map_pred.txt

# echo "evaluating..." 
# python evaluate.py gold1.txt pred.txt
echo "evaluation"
# need change
python evaluate_conll.py $EXP_DIR/tiger.pred.conll09 > $EXP_DIR/result.txt
cat $EXP_DIR/result.txt