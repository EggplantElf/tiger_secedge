#!/bin/bash

set -ue

EXP_DIR=$1
INPUT=$2
OUTPUT=$3

echo "making features for train and predict..."
python scripts/make_features_RE.py -train -i $EXP_DIR/tiger.train.conll09 -m $EXP_DIR/find_RE.map -o $EXP_DIR/find_RE_train.features -f RE.feat 
python scripts/make_features_RE.py -pred -i $EXP_DIR/$INPUT -m $EXP_DIR/find_RE.map -o $EXP_DIR/find_RE_pred.features -f RE.feat

echo "train and predict..."
liblinear/train $EXP_DIR/find_RE_train.features $EXP_DIR/find_RE.model
liblinear/predict $EXP_DIR/find_RE_pred.features $EXP_DIR/find_RE.model $EXP_DIR/pred_RE.txt

echo "mapping back..."
python scripts/make_features_RE.py -mapback -i $EXP_DIR/$INPUT -m $EXP_DIR/find_RE.map -o $EXP_DIR/$OUTPUT -p $EXP_DIR/pred_RE.txt -f RE.feat

