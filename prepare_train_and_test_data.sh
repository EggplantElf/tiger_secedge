#!/bin/bash
set -ue

EXP_NUM=$1
GOLD_SALTO=$2
START=$3
END=$4
PY_DIR=scripts
DATA_DIR=experiment/data/ex0
EXP_DIR=experiment/data/ex$EXP_NUM


echo "Preparing training and test set...(it will take quite a while, why not go and have a coffee)"
# annotated gold data ($START ~ $END)
echo "gold data"
python $PY_DIR/salto_to_tiger.py $GOLD_SALTO $DATA_DIR/tiger.orig.xml $DATA_DIR/head.xml $DATA_DIR/tiger.tmp.gold.xml
python $PY_DIR/cut_xml.py $DATA_DIR/tiger.tmp.gold.xml $DATA_DIR/head.xml $DATA_DIR/tiger.gold.xml $START $END
python $PY_DIR/add_secedge_to_conll.py -g $DATA_DIR/tiger.orig.conll09 $DATA_DIR/tiger.gold.xml $DATA_DIR/tiger.gold.conll09
rm $DATA_DIR/tiger.tmp.gold.xml 
rm  $DATA_DIR/tiger.gold.xml 


# test set for rule-based added edges ($START ~ $END) 
echo "test data"
python $PY_DIR/cut_xml.py $DATA_DIR/tiger.auto.xml $DATA_DIR/head.xml $EXP_DIR/tiger.auto.test.xml $START $END
python $PY_DIR/add_secedge_to_conll.py -p $DATA_DIR/tiger.gold.conll09 $EXP_DIR/tiger.auto.test.xml $EXP_DIR/tiger.auto.test.conll09
rm $EXP_DIR/tiger.auto.test.xml

# traing set (first ~ $START + $END ~ last)  good
echo "training data"
python $PY_DIR/cut_xml.py -r $DATA_DIR/tiger.auto.xml $DATA_DIR/head.xml $DATA_DIR/tiger.train.xml $START $END
python $PY_DIR/add_secedge_to_conll.py -p $DATA_DIR/tiger.orig.conll09 $DATA_DIR/tiger.train.xml $EXP_DIR/tiger.train.conll09
rm  $DATA_DIR/tiger.train.xml 

# (optional) mapping labels
sed 's/SB[ER]/SBC/g' $EXP_DIR/tiger.train.conll09 > $EXP_DIR/tiger.train.MAC.conll09

