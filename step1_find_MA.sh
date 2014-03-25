#!/bin/bash

set -ue

EXP_DIR=$1
INPUT=$2
OUTPUT=$3

echo "making features for train and predict..."
python scripts/make_features_MA.py -train -i $EXP_DIR/tiger.train.conll09 -m $EXP_DIR/find_MA.map -o $EXP_DIR/find_MA_train.features
python scripts/make_features_MA.py -pred -i $EXP_DIR/$INPUT -m $EXP_DIR/find_MA.map -o $EXP_DIR/find_MA_pred.features

echo "train and predict..."
liblinear/train $EXP_DIR/find_MA_train.features $EXP_DIR/find_MA.model
liblinear/predict $EXP_DIR/find_MA_pred.features $EXP_DIR/find_MA.model $EXP_DIR/pred_MA.txt

echo "mapping back"
python scripts/make_features_MA.py -mapback -i $EXP_DIR/$INPUT -m $EXP_DIR/find_MA.map -o $EXP_DIR/$OUTPUT -p $EXP_DIR/pred_MA.txt
