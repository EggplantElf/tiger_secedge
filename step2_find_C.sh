#!/bin/bash

set -ue

EXP_DIR=$1
INPUT=$2
OUTPUT=$3


echo "making features for train and predict..."
sed 's/SB[RE]/SBC/g' $EXP_DIR/tiger.train.conll09 > $EXP_DIR/tiger.train.C.conll09
python scripts/make_features_C.py -train -i $EXP_DIR/tiger.train.C.conll09 -m $EXP_DIR/find_C.map -o $EXP_DIR/find_C_train.features
python scripts/make_features_C.py -pred -i $EXP_DIR/$INPUT -m $EXP_DIR/find_C.map -o $EXP_DIR/find_C_pred.features

echo "train and predict..."
liblinear/train $EXP_DIR/find_C_train.features $EXP_DIR/find_C.model
liblinear/predict $EXP_DIR/find_C_pred.features $EXP_DIR/find_C.model $EXP_DIR/pred_C.txt

echo "mapping back"
python scripts/make_features_C.py -mapback -i $EXP_DIR/$INPUT -m $EXP_DIR/find_C.map -o $EXP_DIR/$OUTPUT -p $EXP_DIR/pred_C.txt
