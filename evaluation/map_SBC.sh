#!/bin/bash

set -ue

echo "making features for train..."
python make_features_map_SBC.py -train -i train.conll09 -m tmp/map_SBC.map -o tmp/map_SBC_train.features
echo "making features for predict..."
python make_features_map_SBC.py -test -i test.MAC.conll09 -m tmp/map_SBC.map -o tmp/map_SBCtest.features

echo "train and predict..."
../liblinear/train tmp/map_SBC_train.features tmp/map_SBC.model
../liblinear/predict tmp/map_SBCtest.features tmp/map_SBC.model pred.txt

echo "mapping back"
python make_features_map_SBC.py -mapback -i test.MAC.conll09 -m tmp/map_SBC.map -o test.MARE.conll09 -p pred.txt

echo "evaluating..."
# python evaluate.py gold1.txt pred.txt
