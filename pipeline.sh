#!/bin/bash
set -ue

GOLD_SALTO=$1
START=$2
END=$3
DATA=experiment/data/ex0


echo "Finding raising and equi from LFG files..."
python find_control_from_LFG.py -r ../bestTrain/ $DATA
python find_control_from_LFG.py -e ../bestTrain/ $DATA

echo "Adding secondary edges into TIGER...(it will take quite a while, why not go and have a coffee)"
python process_tiger.py $DATA/tiger.orig.xml $DATA/tiger.auto.xml $DATA/raising_indices.txt $DATA/equi_indices.txt 123 > $DATAprocess_tiger.log


echo "Preparing training and test set...(it will take quite a while, why not have another coffee)"
# annotated gold data ($START ~ $END)
echo "gold data"
python salto_to_tiger.py $GOLD_SALTO $DATA/tiger.orig.xml $DATA/head.xml $DATA/tiger.tmp.gold.xml
python cut_xml.py $DATA/tiger.tmp.gold.xml $DATA/head.xml $DATA/tiger.gold.xml $START $END
python add_secedge_to_conll.py -g $DATA/tiger.orig.conll09 $DATA/tiger.gold.xml $DATA/tiger.gold.conll09

# test set for rule-based added edges ($START ~ $END) 
echo "test data"
python cut_xml.py $DATA/tiger.auto.xml $DATA/head.xml $DATA/tiger.auto.test.xml $START $END
python add_secedge_to_conll.py -p $DATA/tiger.gold.conll09 $DATA/tiger.auto.test.xml $DATA/tiger.auto.test.conll09
    
# traing set (first ~ $START + $END ~ last)  good
echo "training data"
python cut_xml.py -r $DATA/tiger.auto.xml $DATA/head.xml $DATA/tiger.train.xml $START $END
python add_secedge_to_conll.py -p $DATA/tiger.orig.conll09 $DATA/tiger.train.xml $DATA/tiger.train.conll09

# rm $DATA/tiger.tmp.gold.xml $DATA/tiger.train.xml $ DATA/tiger.test.xml