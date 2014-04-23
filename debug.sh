DIR=experiment/data/ex19/

python scripts/make_features_C.py -pred -i $DIR/tiger.test.C.conll09 -m $DIR/find_C.map -o $DIR/find_C_pred.features -f C.feat
