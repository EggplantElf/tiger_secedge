#!/bin/bash

set -ue

echo "making features for train..."
python make_features_find_SBC.py -train -i train.MAC.conll09 -m tmp/find_SBC.map -o tmp/find_SBC_train.features
echo "making features for predict..."
python make_features_find_SBC.py -test -i test.conll09 -m tmp/find_SBC.map -o tmp/find_SBC_test.features

echo "train and predict..."
../liblinear/train tmp/find_SBC_train.features tmp/find_SBC.model
../liblinear/predict tmp/find_SBC_test.features tmp/find_SBC.model pred.txt

echo "mapping back"
python make_features_find_SBC.py -mapback -i test.conll09 -m tmp/find_SBC.map -o test.MAC.conll09 -p pred.txt

echo "evaluating...(not important here)"
python evaluate.py gold.txt pred.txt
