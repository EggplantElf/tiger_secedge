#!/bin/python
# -*- coding: utf-8 -*-

import sys
import codecs
import cPickle
import gzip

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
        if entries[13] == '_':
            self.sec_heads = {}
        else:
            self.sec_heads = dict(zip(entries[13].split('|'), entries[15].split('|')))
        self.sec_subj = {}
        self.deps = []
        self.entries = entries

    def to_line(self):
        if self.sec_heads:
            self.entries[13] = '|'.join([t for (t, l) in sorted(self.sec_heads.items(), key = lambda x: int(x[0]))])
            self.entries[15] = '|'.join([l for (t, l) in sorted(self.sec_heads.items(), key = lambda x: int(x[0]))])
        # print '\t'.join(self.entries)
        return '\t'.join(self.entries)

    # for debugging
    def infos(self):
        return '\t'.join([self.sid, self.tid, self.form, ','.join([k +'='+ v for (k,v) in self.sec_heads.items()])])


class Root(Token):
    """
    Special root token
    """

    def __init__(self):
        self.form = '-ROOT-'
        self.lemma = '-ROOT-'
        self.pos = '-ROOT-'
        self.head = None
        self.label = '-ROOT-'
        self.sec_heads = {}
        self.sec_subj = {}
        self.deps = []


def update_label(token1, token2, label):
    """
    Update the output entries of a token, if it is assigned a new label.
    used in mapping the prediction back to original conll data
    """
    if label:
        token1.sec_subj[token2] = label
        token2.sec_heads[token1.tid] = label
        # for (k, v) in token2.sec_heads.items():
        #     if k == token1.tid:
        #         token2.sec_heads[k] = label
        #         print token2.sec_heads
        # token2.sec_heads[token1.tid] = label #changed
        # for (k, v) in token2.sec_heads.items():
        #     # print k, v, token2.sec_heads
        #     if k == token1.tid:
        #         token2.sec_heads[k] = label
        # premise: index also sorted in original file
        # if token2.sec_heads:
        #     token2.entries[13] = '|'.join([t for (t, l) in sorted(token2.sec_heads.items(), key = lambda x: int(x[0]))])
        #     token2.entries[15] = '|'.join([l for (t, l) in sorted(token2.sec_heads.items(), key = lambda x: int(x[0]))])
        #     print '\t'.join(token2.entries)



def postprocess_tokens(sentence, label_filter = None):
    """
    After reading a sentence, add links to head, dependants and secondary dependency into each token
    Only add specific secondary dependencies, if there is a filter for label
    """
    for token in sentence:
        # find the head of the token and add the token into the deps of it's head
        if token.head != 0:
            token.head = sentence[token.head - 1]
            token.head.deps.append(token)
        else:
            token.head = Root()
            token.head.deps.append(token)
        # find the secendary subject with label of the token
        for (index, label) in token.sec_heads.items():
            if not label_filter or label in label_filter:
                sentence[int(index) - 1].sec_subj[token] = label # verb.sec_subj[subj] = label


def sentences( filestream , label_filter = None):
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
            postprocess_tokens(sentence, label_filter)
            yield sentence
            sentence = []
    if sentence:
        postprocess_tokens(sentence, label_filter)
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


# Return the path of tokens from a given token(incl.) to root(excl.), skipping dependency of conjunctions
# e.g. a path "ROOT --> Verb -OA-> Noun1 -CJ-> Noun2 -CD-> und -CJ-> Noun3", 
# chain_to_root(sentence, Noun3) will return [Noun3, Verb]
def chain_to_root(sentence, token):
    # skip the CJ/CD nodes
    chain = []
    while token.pos != '-ROOT-':
        chain.append(token)
        token = skip_conj_head(sentence, token)
    return chain

# Return the head of a given token, skipping dependency of conjunctions
# setting a level higher than 1 can get the ancestor of the token
def skip_conj_head(sentence, token, level = 1):
    # print token.pos
    for i in range(level):
        while token.label in ['CD', 'CJ']:
            token = token.head
        token = token.head
        if token.pos == '-ROOT-':
            break
    return token


# Return the label of the token to its head, skipping dependency of conjunctions
def skip_conj_label(sentence, token):
    while token.label in ['CD', 'CJ']:
        token = token.head
    return token.label


# Return the first matching token of a start token and a path
# e.g. get_token_by_path(sentence, token, ['OP', 'NK'] means
# the NK dependant of the OP dependant of the given token
# Doesn't handle multiple matches and conjuncts(and mostly shouldn't), 
# but for our purpose it works in general
def get_token_by_path(sentence, token, path):
    for label in path:
        token = [d for d in token.deps if d.label == label]
        if not token:
            return None
        else:
            token = token[0]
    return token

# Return the POS tag of a token
def get_pos(token):
    if token:
        return token.pos
    else:
        return '-NONE-'

# Return the lemma of a token
def get_lemma(token):
    if token:
        return token.lemma
    else:
        return '-NONE-'

