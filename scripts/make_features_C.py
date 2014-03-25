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
    argpar.add_argument('-p','--predict',dest='predfile',help='predict file',required=False)
    args = argpar.parse_args()

    feattab = FeatureTable()
    outstream = open(args.outputfile,'w')

    if args.mapback:
        pred = codecs.open(args.predfile,encoding='utf-8')
        feattab.load(args.mapfile)
        feattab.invert_tabs()

        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBC']):
            for tid1,token1 in enumerate(sentence):
                if token1.pos[0] == 'V' and token1.head.pos != '-ROOT-':
                    useful_tokens = get_useful_tokens(token1, sentence)
                    # add feature of verb
                    verb_features = make_verb_feature_vector(useful_tokens,token1, sentence,feattab.register_feature)
                    for tid2, token2 in enumerate(sentence):
                        if tid1 != tid2:
                            pred_label = feattab.mapback_label(int(pred.readline()))
                            if pred_label:
                                update_label(token1, token2, pred_label)
            for tid, token in enumerate(sentence):
                print >> outstream, token.to_line()
            print >> outstream, ''




    elif args.train:
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBC']):
            for tid1,token1 in enumerate(sentence):
                if token1.pos[0] == 'V' and token1.head.pos != '-ROOT-':
                    useful_tokens = get_useful_tokens(token1, sentence)
                    # print useful_tokens
                    # add feature of verb
                    verb_features = make_verb_feature_vector(useful_tokens,token1, sentence,feattab.register_feature)
                    for tid2, token2 in enumerate(sentence):
                        if tid1 != tid2:
                            # add label
                            if token2 in token1.sec_subj:
                                label = feattab.register_label(token1.sec_subj[token2])
                            else:
                                label = feattab.register_label('')
                            # add feature of noun
                            noun_features = make_noun_feature_vector(useful_tokens, token2, sentence,feattab.register_feature)
                            write_to_file(label,verb_features + noun_features,outstream)
        feattab.save(args.mapfile)

        # print '-' * 20
        # for k in feattab.feattab:
        #   print k, feattab.feattab[k]



    elif args.pred:
        # result = open('gold.txt', 'w')

        feattab.load(args.mapfile)
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBC']):
            # for tid,token in enumerate(sentence):
            #   features = make_feature_vector(tid,token,sentence,feattab.map_feature)
            #   write_to_file(0,features,outstream)

            for tid1,token1 in enumerate(sentence):
                if token1.pos[0] == 'V' and token1.head.pos != '-ROOT-':
                    useful_tokens = get_useful_tokens(token1, sentence)
                    # print useful_tokens
                    # add feature of verb
                    verb_features = make_verb_feature_vector(useful_tokens,token1, sentence,feattab.register_feature)
                    for tid2, token2 in enumerate(sentence):
                        if tid1 != tid2:
                            # add label
                            if token2 in token1.sec_subj:
                                label = token1.sec_subj[token2]
                            else:
                                label = ''
                            i = feattab.map_label(label)
                            # result.write('%d\t%s\t%s\t%s\t%s\n' % (i, token1.sid, label, token2.form, token1.form))
                            # add feature of noun
                            noun_features = make_noun_feature_vector(useful_tokens, token2, sentence,feattab.register_feature)
                            # print verb_features + noun_features
                            write_to_file(i,verb_features + noun_features,outstream)
        # result.close()
    outstream.close()









