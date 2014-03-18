#!/bin/bash
set -ue

EXP_NUM=$1
GOLD_SALTO=$2
START=$3
END=$4
DATA_DIR=experiment/data/ex0
EXP_DIR=experiment/data/ex$EXP_NUM

if [ ! -d $EXP_DIR ]; then
  mkdir $EXP_DIR
fi

# echo "Finding raising and equi from LFG files..."
# python find_control_from_LFG.py -r ../bestTrain/ $DATA_DIR
# python find_control_from_LFG.py -e ../bestTrain/ $DATA_DIR

# echo "Adding secondary edges into TIGER...(it will take quite a while, why not go and have a coffee)"
# python process_tiger.py $DATA_DIR/tiger.orig.xml $DATA_DIR/tiger.auto.xml $DATA_DIR/raising_indices.txt $DATA_DIR/equi_indices.txt 123 > $DATA_DIR/process_tiger.log


# echo "Preparing training and test set...(it will take quite a while, why not have another coffee)"
# # annotated gold data ($START ~ $END)
# echo "gold data"
# python salto_to_tiger.py $GOLD_SALTO $DATA_DIR/tiger.orig.xml $DATA_DIR/head.xml $DATA_DIR/tiger.tmp.gold.xml
# python cut_xml.py $DATA_DIR/tiger.tmp.gold.xml $DATA_DIR/head.xml $DATA_DIR/tiger.gold.xml $START $END
# python add_secedge_to_conll.py -g $DATA_DIR/tiger.orig.conll09 $DATA_DIR/tiger.gold.xml $DATA_DIR/tiger.gold.conll09
# rm $DATA_DIR/tiger.tmp.gold.xml 
# rm  $DATA_DIR/tiger.gold.xml 
# cp $DATA_DIR/tiger.gold.conll09 $EXP_DIR

# # test set for rule-based added edges ($START ~ $END) 
# echo "test data"
# python cut_xml.py $DATA_DIR/tiger.auto.xml $DATA_DIR/head.xml $EXP_DIR/tiger.auto.test.xml $START $END
# python add_secedge_to_conll.py -p $DATA_DIR/tiger.gold.conll09 $EXP_DIR/tiger.auto.test.xml $EXP_DIR/tiger.auto.test.conll09
# rm $EXP_DIR/tiger.auto.test.xml

# # traing set (first ~ $START + $END ~ last)  good



# echo "training data"
# python cut_xml.py -r $DATA_DIR/tiger.auto.xml $DATA_DIR/head.xml $DATA_DIR/tiger.train.xml $START $END
# python add_secedge_to_conll.py -p $DATA_DIR/tiger.orig.conll09 $DATA_DIR/tiger.train.xml $EXP_DIR/tiger.train.conll09
# rm  $EXP_DIR/tiger.train.xml 

# sed 's/SB[ER]/SBC/g' $EXP_DIR/tiger.train.conll09 > $EXP_DIR/tiger.train.MAC.conll09


# ./find_SBC.sh $EXP_DIR
# ./map_SBC.sh $EXP_DIR

echo "making features for train..."
python make_features.py -train -i $EXP_DIR/tiger.train.conll09 -m $EXP_DIR/feat.map -o $EXP_DIR/tiger.train.features
echo "making features for predict..."
python make_features.py -test -i $EXP_DIR/tiger.gold.conll09 -m $EXP_DIR/feat.map -o $EXP_DIR/tiger.pred.features

echo "train and predict..."
liblinear/train $EXP_DIR/tiger.train.features $EXP_DIR/train.model
liblinear/predict $EXP_DIR/tiger.pred.features $EXP_DIR/train.model $EXP_DIR/pred.txt

echo "mapping back"
python make_features.py -mapback -i $EXP_DIR/tiger.gold.conll09 -m $EXP_DIR/feat.map -o $EXP_DIR/tiger.pred.conll09 -p $EXP_DIR/pred.txt

python evaluate_conll.py $EXP_DIR/tiger.pred.conll09 > $EXP_DIR/result.txt
cat $EXP_DIR/result.txt


