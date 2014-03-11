#!/bin/bash

set -ue

EXDIR=data/$1

echo "making features for train..."
python make_features_find_SBC.py -train -i $EXDIR/train.MAC.conll09 -m $EXDIR/find_SBC.map -o $EXDIR/find_SBC_train.features
echo "making features for predict..."
python make_features_find_SBC.py -test -i $EXDIR/test.conll09 -m $EXDIR/find_SBC.map -o $EXDIR/find_SBC_test.features

echo "train and predict..."
../liblinear/train $EXDIR/find_SBC_train.features $EXDIR/find_SBC.model
../liblinear/predict $EXDIR/find_SBC_test.features $EXDIR/find_SBC.model $EXDIR/pred.txt

echo "mapping back"
python make_features_find_SBC.py -mapback -i $EXDIR/test.conll09 -m $EXDIR/find_SBC.map -o $EXDIR/test.MAC.conll09 -p $EXDIR/pred.txt

# echo "evaluating...(not important here)"
# python evaluate.py gold.txt pred.txt
