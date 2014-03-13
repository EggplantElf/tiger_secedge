#!/bin/bash
set -ue

EXP_NUM=$1
GOLD_SALTO=$2
START=$3
END=$4
DATA_DIR=experiment/data/ex0
EXP_DIR=experiment/data/ex$EXP_NUM

echo "Finding raising and equi from LFG files..."
python find_control_from_LFG.py -r ../bestTrain/ $DATA_DIR
python find_control_from_LFG.py -e ../bestTrain/ $DATA_DIR

# echo "Adding secondary edges into TIGER...(it will take quite a while, why not go and have a coffee)"
# python process_tiger.py $DATA_DIR/tiger.orig.xml $DATA_DIR/tiger.auto.xml $DATA_DIR/raising_indices.txt $DATA_DIR/equi_indices.txt 123 > $DATA_DIR/process_tiger.log


# echo "Preparing training and test set...(it will take quite a while, why not have another coffee)"
# # annotated gold data ($START ~ $END)
# echo "gold data"
# python salto_to_tiger.py $GOLD_SALTO $DATA_DIR/tiger.orig.xml $DATA_DIR/head.xml $DATA_DIR/tiger.tmp.gold.xml
# python cut_xml.py $DATA_DIR/tiger.tmp.gold.xml $DATA_DIR/head.xml $DATA_DIR/tiger.gold.xml $START $END
# python add_secedge_to_conll.py -g $DATA_DIR/tiger.orig.conll09 $DATA_DIR/tiger.gold.xml $DATA_DIR/tiger.gold.conll09

# # test set for rule-based added edges ($START ~ $END) 
# echo "test data"
# python cut_xml.py $DATA_DIR/tiger.auto.xml $DATA_DIR/head.xml $DATA_DIR/tiger.auto.test.xml $START $END
# python add_secedge_to_conll.py -p $DATA_DIR/tiger.gold.conll09 $DATA_DIR/tiger.auto.test.xml $DATA_DIR/tiger.auto.test.conll09
    
# traing set (first ~ $START + $END ~ last)  good

# mkdir experiment/data/ex$EXP_NUM

# echo "training data"
# python cut_xml.py -r $DATA_DIR/tiger.auto.xml $DATA_DIR/head.xml $DATA_DIR/tiger.train.xml $START $END
# python add_secedge_to_conll.py -p $DATA_DIR/tiger.orig.conll09 $DATA_DIR/tiger.train.xml EXP_DIR/tiger.train.conll09

# sed 's/SB[E|R]/SBC/g' $DATA_DIR/tiger.train.conll09 > $DATA_DIR/tiger.train.MAC.conll09


# rm $DATA_DIR/tiger.tmp.gold.xml $DATA_DIR/tiger.train.xml $DATA_DIR/tiger.auto.test.xml

# experiment/find_SBC.sh EXP_DIR
# experiment/map_SBC.sh EXP_DIR
