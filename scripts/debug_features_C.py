#!/bin/python
# -*- coding: utf-8 -*-

import sys
import codecs
from features_util import *

# Make features for candidates of a verb in a sencondary dependency
def make_verb_feature_vector(useful_tokens, verb, sentence, mapfunc):   
    # print verb.form
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
    # features.append(mapfunc('ZU_INF:%s' % (verb.pos == 'VVIZU' or get_token_by_path(sentence, verb, ['PM']) != None)))
    if verb.pos == 'VVIZU' or get_token_by_path(sentence, verb, ['PM']) != None:
        features.append(mapfunc('ZU_INF'))


    # POS of the verb's OC dependant if there is one
    if get_pos(get_token_by_path(sentence, verb, ['OC'])):
        features.append(mapfunc('SELF.OC.POS'))
    # whether the verb has "wie", "weil", "um" etc
    for pos in ['KOUI', 'KOUS', 'PWAV', 'PAV']:
        if get_deps_by_pos(sentence, verb, 'PWAV'):
            features.append(mapfunc('SELF.%s' % pos))

    # lemmas of the heads
    # features.append(mapfunc('HEAD1.LEMMA:%s' % get_lemma(useful_tokens['HEAD1'])))
    # features.append(mapfunc('HEAD2.LEMMA:%s' % get_lemma(useful_tokens['HEAD2'])))
    # features.append(mapfunc('HEAD3.LEMMA:%s' % get_lemma(useful_tokens['HEAD3'])))

    for role in useful_tokens:
        if useful_tokens[role]:
            features.append(mapfunc('%s:%s' % (role, get_pos(useful_tokens[role]))))

    return features


# Make features for candidates of a subject in a secondary dependency 
# (not necessary to be a noun, just easier to understand)
def make_noun_feature_vector(useful_tokens, noun, sentence, mapfunc):
    # print noun.form
    features = []
    features.append(mapfunc('NOUN_POS:%s' % noun.pos))
    for role in useful_tokens:
        if noun == useful_tokens[role]:
            features.append(mapfunc('NOUN_IS_%s' % role))





    # experimental
    # features.append(mapfunc('NOUN_BEFORE_VERB:%s' % (int(noun.tid) < int(useful_tokens['VERB'].tid))))
    if useful_tokens['HEAD1'] and str(useful_tokens['HEAD1'].tid) in noun.sec_heads:
        features.append(mapfunc('NOUN_IS_HEAD1.SECSUBJ'))
    # features.append(mapfunc('NOUN_IS_HEAD2.SECSUBJ:%s' % (useful_tokens['HEAD2'] and str(useful_tokens['HEAD2'].tid) in noun.sec_heads)))
    # features.append(mapfunc('NOUN_BEFORE_HEAD1:%s' % (int(noun.tid) < int(useful_tokens['HEAD1'].tid))))
    # features.append(mapfunc('NOUN_BEFORE_HEAD2:%s' % (int(noun.tid) < int(useful_tokens['HEAD2'].tid))))
    # features.append(mapfunc('NOUN_BEFORE_HEAD3:%s' % (int(noun.tid) < int(useful_tokens['HEAD3'].tid))))
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

        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBC']):
            for tid1,token1 in enumerate(sentence):
                if token1.pos[0] == 'V' and token1.head.pos != '-ROOT-':
                    useful_tokens = get_useful_tokens(token1, sentence)
                    # add feature of verb
                    # verb_features = make_verb_feature_vector(useful_tokens,token1, sentence,feattab.register_feature)
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
        print len(feattab.feattab)
        # print '-' * 20
        # for k in feattab.feattab:
        #   print k, feattab.feattab[k]



    elif args.pred:
        # result = open('gold.txt', 'w')

        feattab.load(args.mapfile)
        feattab.invert_tabs()
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8'), ['SBC']):
            # for tid,token in enumerate(sentence):
            #   features = make_feature_vector(tid,token,sentence,feattab.map_feature)
            #   write_to_file(0,features,outstream)
            if sentence[0].sid != '10330':
                continue
            for tid1,token1 in enumerate(sentence):
                if token1.pos[0] == 'V' and token1.head.pos != '-ROOT-':
                    useful_tokens = get_useful_tokens(token1, sentence)
                    # print useful_tokens
                    # add feature of verb
                    verb_features = make_verb_feature_vector(useful_tokens,token1, sentence,feattab.map_feature)
                    for tid2, token2 in enumerate(sentence):
                        if tid1 != tid2:
                            # add label

                            # print token1.form, token2.form

                            if token2 in token1.sec_subj:
                                label = token1.sec_subj[token2]
                            else:
                                label = ''
                            i = feattab.map_label(label)
                            # result.write('%d\t%s\t%s\t%s\t%s\n' % (i, token1.sid, label, token2.form, token1.form))
                            # add feature of noun
                            noun_features = make_noun_feature_vector(useful_tokens, token2, sentence,feattab.map_feature)
                            write_to_file(i,verb_features + noun_features,outstream)

                            print_features(feattab, verb_features + noun_features, token1, token2)

        # result.close()
        print len(feattab.feattab)
        
    outstream.close()









