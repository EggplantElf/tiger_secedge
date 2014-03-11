#!/bin/python
# -*- coding: utf-8 -*-

import sys
import codecs
import cPickle
import gzip
import re
import random

class Token(object):
    """
    Represents one token 
    (a non-empty line in CoNLL09 format).
    """
    def __init__( self, line ):
        entries = line.encode('utf-8').split('\t')
        self.sid = entries[0].split('_')[0]
        self.tid = entries[0].split('_')[1]
        self.form = entries[1]
        self.lemma = entries[2]
        self.pos = entries[4]
        self.head = int(entries[8])
        self.label = entries[10]
        if entries[12] == '_':
            self.sec_heads = {}
        else:
            self.sec_heads = dict(zip(entries[12].split('|'), entries[14].split('|')))
        self.sec_subj = {}
        self.deps = []
        self.entries = entries

    def to_line(self):
        # if self.entries[14] != '_' and 'SBC' in self.entries[14].split('|'):
        #     print '\t'.join(self.entries)
        return '\t'.join(self.entries)



class Root(Token):
    def __init__(self):
        self.form = '-ROOT-'
        self.lemma = '-ROOT-'
        self.pos = '-ROOT-'
        self.head = None
        self.label = '-ROOT-'
        self.sec_heads = {}
        self.sec_subj = {}
        self.deps = []

def postprocess_tokens(sentence):
    for token in sentence:
        # find the head of the token and add the token into the deps of it's head
        if token.head != 0:
            token.head = sentence[token.head - 1]
            token.head.deps.append((token))
        else:
            token.head = Root()
            token.head.deps.append((token))
        # find the secendary subject with label of the token
        for (index, label) in token.sec_heads.items():
            if label in ['SBM', 'SBA' ,'SBC']:
                sentence[int(index) - 1].sec_subj[token] = label # verb.sec_subj[subj] = label


def update_label(token1, token2, label):
    if label:
        token1.sec_subj[token2] = label
        for (k, v) in token2.sec_heads.items():
            if k == token1.tid:
                # print token2.sec_heads
                token2.sec_heads[k] = label
        # premise: index also sorted in original file
        if token2.sec_heads:
            token2.entries[12] = '|'.join([t for (t, l) in sorted(token2.sec_heads.items(), key = lambda x: int(x[0]))])
            token2.entries[14] = '|'.join([l for (t, l) in sorted(token2.sec_heads.items(), key = lambda x: int(x[0]))])
        else:
            token2.entries[12] = '_'
            token2.entries[14] = '_'
        # print '\t'.join(token2.entries)



def sentences( filestream ):
    """
    Generator that returns sentences as lists of Token objects.
    Reads CoNLL09 format.
    """
    i = 0
    sentence = []
    for line in filestream:
        line = line.rstrip()
        if line:
            sentence.append(Token(line))
        elif sentence:
            postprocess_tokens(sentence)
            yield sentence
            sentence = []
            # i += 1
            # if i % 1000 == 0:
            #   print i
    if sentence:
        postprocess_tokens(sentence)
        yield sentence


class FeatureTable(object):
    """
    FeatureTable stores features and labels, 
    and maps them to integer values.
    """
    def __init__( self ):
        self.labeltab = {}
        self.feattab = {}

    def save( self, filename ):
        stream = gzip.open(filename,'wb')
        cPickle.dump(self.labeltab,stream,-1)
        cPickle.dump(self.feattab,stream,-1)
        stream.close()

    def load( self, filename ):
        stream = gzip.open(filename,'rb')
        self.labeltab = cPickle.load(stream)
        self.feattab = cPickle.load(stream)
        stream.close()

    def numfeatures( self ):
        return len(self.feattab)

    def numlabels( self ):
        return len(self.labeltab)

    def register_feature( self, feature ):
        if feature not in self.feattab:
            self.feattab[feature] = self.numfeatures()+1 # +1 to comply with liblinear format
            return self.numfeatures()
        return self.feattab[feature]

    def register_label( self, label ):
        if label not in self.labeltab:
            self.labeltab[label] = self.numlabels()
            return self.numlabels()-1
        return self.labeltab[label] 

    def map_feature( self, feature ):
        return self.feattab.get(feature,None)

    def map_label( self, label ):
        return self.labeltab.get(label,None)

    def invert_tabs(self):
        self.inv_labeltab = {v:k for k, v in self.labeltab.items()}
        # self.inv_feattab = {v:k for k, v in self.feattab.items()}


    def mapback_label( self, i):
        return self.inv_labeltab.get(i, None)



def write_to_file( label, features, fileobj ):
    features = set(features)
    features.discard(None)
    print >> fileobj, '%d %s' % (label,' '.join(map(lambda x: '%d:1' % x,sorted(features))))

def get_useful_tokens(verb, sentence):
    dic = {}
    dic['HEAD1'] = skip_conj_head(sentence, verb, 1)
    dic['HEAD2'] = skip_conj_head(sentence, verb, 2)
    dic['HEAD3'] = skip_conj_head(sentence, verb, 3)
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


def make_verb_feature_vector(useful_tokens, verb, sentence, mapfunc):   
    features = []
    root_path = chain_to_root(sentence, verb)
    root_path_label = map(lambda x: skip_conj_label(sentence, x), root_path)
    features.append(mapfunc('PATH.POS:%s' % '_'.join(map(lambda x: x.pos, root_path))))
    features.append(mapfunc('PATH.LABEL:%s' % '_'.join(root_path_label)))

    features.append(mapfunc('PATH.F1.LABEL:%s' % root_path_label[0]))
    features.append(mapfunc('PATH.F2.LABEL:%s' % '_'.join((root_path_label + ['--'])[:2])))
    # features.append(mapfunc('PATH.F3.LABEL:%s' % '_'.join((root_path_label + ['--', '--'])[:3])))


    features.append(mapfunc('ZU_INF:%s' % (verb.pos == 'VVIZU' or get_token_by_path(sentence, verb, ['PM'])) and True or False))
    features.append(mapfunc('SELF.OC:%s' % get_pos(get_token_by_path(sentence, verb, ['OC']))))




    features.append(mapfunc('HEAD1.LEMMA:%s' % get_lemma(useful_tokens['HEAD1'])))
    features.append(mapfunc('HEAD2.LEMMA:%s' % get_lemma(useful_tokens['HEAD2'])))
    features.append(mapfunc('HEAD3.LEMMA:%s' % get_lemma(useful_tokens['HEAD3'])))


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



def chain_to_root(sentence, token):
    # skip the CJ/CD nodes
    chain = []
    while token.pos != '-ROOT-':
        chain.append(token)
        token = skip_conj_head(sentence, token)
    return chain

def skip_conj_head(sentence, token, level = 1):
    # print token.pos
    for i in range(level):
        while token.label in ['CD', 'CJ']:
            token = token.head
        token = token.head
        if token.pos == '-ROOT-':
            break
    return token

def skip_conj_self(sentence, token):
    while token.label in ['CD', 'CJ']:
        token = token.head

def skip_conj_label(sentence, token):
    while token.label in ['CD', 'CJ']:
        token = token.head
    return token.label


# need change
def get_token_by_path(sentence, token, path):
    for label in path:
        token = [d for d in token.deps if d.label == label]
        if not token:
            return None
        else:
            token = token[0]
    return token

def get_token_by_path_new(sentence, token, path):
    res = []
    label = path[0]
    for label in path:
        token = [d for d in token.deps if d.label == label]
        if not token:
            return None
        else:
            token = token[0]
    return token

def get_pos(token):
    if token:
        return token.pos
    else:
        return '-NONE-'

def get_lemma(token):
    if token:
        return token.lemma
    else:
        return '-NONE-'



if __name__=='__main__':
    import argparse

    argpar = argparse.ArgumentParser(description='Creates a feature representation for each word in a given file in CoNLL09 format')
    mode = argpar.add_mutually_exclusive_group(required=True)
    mode.add_argument('-train',dest='train',action='store_true',help='run in training mode')
    mode.add_argument('-test',dest='test',action='store_true',help='run in test mode')
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

        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8')):
            for tid1,token1 in enumerate(sentence):
                if token1.pos[0] == 'V' and token1.head.pos != '-ROOT-':
                    useful_tokens = get_useful_tokens(token1, sentence)
                    # print useful_tokens
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
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8')):
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
                            # print verb_features + noun_features
                            write_to_file(label,verb_features + noun_features,outstream)
        feattab.save(args.mapfile)

        # print '-' * 20
        # for k in feattab.feattab:
        #   print k, feattab.feattab[k]



    elif args.test:
        # result = open('gold.txt', 'w')

        feattab.load(args.mapfile)
        for sentence in sentences(codecs.open(args.inputfile,encoding='utf-8')):
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
                            # i = feattab.map_label(label)
                            # result.write('%d\t%s\t%s\t%s\t%s\n' % (i, token1.sid, label, token2.form, token1.form))
                            # add feature of noun
                            noun_features = make_noun_feature_vector(useful_tokens, token2, sentence,feattab.register_feature)
                            # print verb_features + noun_features
                            write_to_file(i,verb_features + noun_features,outstream)
        # result.close()
    outstream.close()









