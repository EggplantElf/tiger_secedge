#!/bin/python
# -*- coding: utf-8 -*-

import sys
import codecs
from features_util import *


if __name__=='__main__':
    import argparse

    argpar = argparse.ArgumentParser(description='Creates a feature representation for each word in a given file in CoNLL09 format')
    mode = argpar.add_mutually_exclusive_group(required=True)
    mode.add_argument('-train',dest='train',action='store_true',help='run in training mode')
    mode.add_argument('-pred',dest='pred',action='store_true',help='run in pred mode')
    mode.add_argument('-mapback',dest='mapback',action='store_true',help='map result back into original conll file')
    argpar.add_argument('-i','--input',dest='inputfile',help='input file',required=True)
    argpar.add_argument('-m','--featmap',dest='mapfile',help='feature mapping file',required=True)
    argpar.add_argument('-o','--output',dest='outputfile',help='output file',required=True)
    argpar.add_argument('-f','--filter',dest='filterfile',help='feature filter file',required=True)
    argpar.add_argument('-p','--predict',dest='predfile',help='predict file',required=False)
    args = argpar.parse_args()

    feattab = FeatureTable()
    outstream = open(args.outputfile,'w')
    feat_filter = read_feat_filter(args.filterfile)


    if args.train:
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBC']):
            # if sentence[0].sid != '479':
            #     continue
            traverse_train(sentence, feattab, feat_filter, outstream)
            # exit(0)
        feattab.save(args.mapfile)


    elif args.pred:
        feattab.load(args.mapfile)
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8')):
            if sentence[0].sid != '10330':
                continue
            traverse_pred(sentence, feattab, feat_filter, outstream)
            exit(0)

    elif args.mapback:
        pred = codecs.open(args.predfile,encoding='utf-8')
        feattab.load(args.mapfile)
        feattab.invert_tabs()

        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBC']):
            traverse_mapback(sentence, feattab, outstream, pred)

    outstream.close()









