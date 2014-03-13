#!/bin/bash

set -ue

EXDIR=$1

echo "making features for train..."
python make_features_map_SBC.py -train -i $EXDIR/train.conll09 -m $EXDIR/map_SBC.map -o $EXDIR/map_SBC_train.features
echo "making features for predict..."
python make_features_map_SBC.py -test -i $EXDIR/test.MAC.conll09 -m $EXDIR/map_SBC.map -o $EXDIR/map_SBC_test.features

echo "train and predict..."
../liblinear/train $EXDIR/map_SBC_train.features $EXDIR/map_SBC.model
../liblinear/predict $EXDIR/map_SBC_test.features $EXDIR/map_SBC.model $EXDIR/pred.txt

echo "mapping back"
python make_features_map_SBC.py -mapback -i $EXDIR/test.MAC.conll09 -m $EXDIR/map_SBC.map -o $EXDIR/pred.conll09 -p $EXDIR/pred.txt

# echo "evaluating..." 
# python evaluate.py gold1.txt pred.txt
echo "evaluation"
python evaluate_conll.py $EXDIR/test.conll09 $EXDIR/pred.conll09 > $EXDIR/result.txt
cat $EXDIR/result.txt