#!/bin/python
# -*- coding: utf-8 -*-

import sys
import codecs
from features_util import *

# save some usful tokens in a dictionary to use later
def get_useful_tokens(verb, sentence):
    dic = {}
    # head, head's head, and head's head's head
    dic['HEAD1'] = skip_conj_head(sentence, verb, 1)
    dic['HEAD2'] = skip_conj_head(sentence, verb, 2)
    dic['HEAD3'] = skip_conj_head(sentence, verb, 3)

    # subject, direct object, dative object, and prepositional object on each head
    dic['HEAD1.SB'] = get_token_by_path(sentence, dic['HEAD1'], ['SB'])
    dic['HEAD1.OA'] = get_token_by_path(sentence, dic['HEAD1'], ['OA'])
    dic['HEAD1.DA'] = get_token_by_path(sentence, dic['HEAD1'], ['DA'])
    dic['HEAD1.OP.NK'] = get_token_by_path(sentence, dic['HEAD1'], ['OP', 'NK'])
    dic['HEAD2.SB'] = get_token_by_path(sentence, dic['HEAD2'], ['SB'])
    dic['HEAD2.OA'] = get_token_by_path(sentence, dic['HEAD2'], ['OA'])
    dic['HEAD2.DA'] = get_token_by_path(sentence, dic['HEAD2'], ['DA'])
    dic['HEAD2.OP.NK'] = get_token_by_path(sentence, dic['HEAD2'], ['OP', 'NK'])
    dic['HEAD3.SB'] = get_token_by_path(sentence, dic['HEAD3'], ['SB'])
    dic['HEAD3.OA'] = get_token_by_path(sentence, dic['HEAD3'], ['OA'])
    dic['HEAD3.DA'] = get_token_by_path(sentence, dic['HEAD3'], ['DA'])
    dic['HEAD3.OP.NK'] = get_token_by_path(sentence, dic['HEAD3'], ['OP', 'NK'])
    return dic


# Make features for candidates of a verb in a sencondary dependency
def make_verb_feature_vector(useful_tokens, verb, sentence, mapfunc):   
    features = []
    root_path = chain_to_root(sentence, verb)
    root_path_pos = map(lambda x: x.pos, root_path)
    root_path_label = map(lambda x: skip_conj_label(sentence, x), root_path)


    # features.append(mapfunc('SELF.LEMMA:%s' % verb.lemma)) # decresed the accuracy, try embed brown cluster

    # POS and label of the path to root
    features.append(mapfunc('PATH.POS:%s' % '_'.join(root_path_pos)))
    features.append(mapfunc('PATH.LABEL:%s' % '_'.join(root_path_label)))


    # prefixes of path to root
    # features.append(mapfunc('PATH.P1.POS:%s' % root_path_pos[0])) #?
    # features.append(mapfunc('PATH.P2.POS:%s' % '_'.join((root_path_pos + ['--'])[:2]))) #?
    features.append(mapfunc('PATH.P1.LABEL:%s' % root_path_label[0]))
    features.append(mapfunc('PATH.P2.LABEL:%s' % '_'.join((root_path_label + ['--'])[:2])))
    # features.append(mapfunc('PATH.F3.LABEL:%s' % '_'.join((root_path_label + ['--', '--'])[:3])))

    # whether the verb is infinitive with zu
    features.append(mapfunc('ZU_INF:%s' % (verb.pos == 'VVIZU' or get_token_by_path(sentence, verb, ['PM']) != None)))
    # POS of the verb's OC dependant if there is one
    features.append(mapfunc('SELF.OC.POS:%s' % get_pos(get_token_by_path(sentence, verb, ['OC']))))

    # lemmas of the heads
    features.append(mapfunc('HEAD1.LEMMA:%s' % get_lemma(useful_tokens['HEAD1'])))
    features.append(mapfunc('HEAD2.LEMMA:%s' % get_lemma(useful_tokens['HEAD2'])))
    features.append(mapfunc('HEAD3.LEMMA:%s' % get_lemma(useful_tokens['HEAD3'])))


    # POS of the heads and their dependants
    features.append(mapfunc('HEAD1:%s' % get_pos(useful_tokens['HEAD1'])))
    features.append(mapfunc('HEAD1.SB:%s' % get_pos(useful_tokens['HEAD1.SB'])))
    features.append(mapfunc('HEAD1.OA:%s' % get_pos(useful_tokens['HEAD1.OA'])))
    features.append(mapfunc('HEAD1.DA:%s' % get_pos(useful_tokens['HEAD1.DA'])))
    features.append(mapfunc('HEAD1.OP.NK:%s' % get_pos(useful_tokens['HEAD1.OP.NK'])))

    features.append(mapfunc('HEAD2:%s' % get_pos(useful_tokens['HEAD2'])))
    features.append(mapfunc('HEAD2.SB:%s' % get_pos(useful_tokens['HEAD2.SB'])))
    features.append(mapfunc('HEAD2.OA:%s' % get_pos(useful_tokens['HEAD2.OA'])))
    features.append(mapfunc('HEAD2.DA:%s' % get_pos(useful_tokens['HEAD2.DA'])))
    features.append(mapfunc('HEAD2.OP.NK:%s' % get_pos(useful_tokens['HEAD2.OP.NK'])))

    features.append(mapfunc('HEAD3:%s' % get_pos(useful_tokens['HEAD3'])))
    features.append(mapfunc('HEAD3.SB:%s' % get_pos(useful_tokens['HEAD3.SB'])))
    features.append(mapfunc('HEAD3.OA:%s' % get_pos(useful_tokens['HEAD3.OA'])))
    features.append(mapfunc('HEAD3.DA:%s' % get_pos(useful_tokens['HEAD3.DA'])))
    features.append(mapfunc('HEAD3.OP.NK:%s' % get_pos(useful_tokens['HEAD3.OP.NK'])))

    return features


# Make features for candidates of a subject in a secondary dependency 
# (not necessary to be a noun, just easier to understand)
def make_noun_feature_vector(useful_tokens, noun, sentence, mapfunc):
    features = []
    features.append(mapfunc('NOUN_POS:%s' % noun.pos))
    features.append(mapfunc('NOUN_IS_HEAD1.SB:%s' % (noun == useful_tokens['HEAD1.SB'])))
    features.append(mapfunc('NOUN_IS_HEAD1.OA:%s' % (noun == useful_tokens['HEAD1.OA'])))
    features.append(mapfunc('NOUN_IS_HEAD1.DA:%s' % (noun == useful_tokens['HEAD1.DA'])))
    features.append(mapfunc('NOUN_IS_HEAD1.OP.NK:%s' % (noun == useful_tokens['HEAD1.OP.NK'])))
    features.append(mapfunc('NOUN_IS_HEAD2.SB:%s' % (noun == useful_tokens['HEAD2.SB'])))
    features.append(mapfunc('NOUN_IS_HEAD2.OA:%s' % (noun == useful_tokens['HEAD2.OA'])))
    features.append(mapfunc('NOUN_IS_HEAD2.DA:%s' % (noun == useful_tokens['HEAD2.DA'])))
    features.append(mapfunc('NOUN_IS_HEAD2.OP.NK:%s' % (noun == useful_tokens['HEAD2.OP.NK'])))
    features.append(mapfunc('NOUN_IS_HEAD3.SB:%s' % (noun == useful_tokens['HEAD3.SB'])))
    features.append(mapfunc('NOUN_IS_HEAD3.OA:%s' % (noun == useful_tokens['HEAD3.OA'])))
    features.append(mapfunc('NOUN_IS_HEAD3.DA:%s' % (noun == useful_tokens['HEAD3.DA'])))
    features.append(mapfunc('NOUN_IS_HEAD3.OP.NK:%s' % (noun == useful_tokens['HEAD3.OP.NK'])))

    return features


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

        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBM', 'SBA']):
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
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBM', 'SBA']):
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
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBM', 'SBA']):
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









