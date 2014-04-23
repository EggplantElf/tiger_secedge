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
        self.sec_deps = {}
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
        self.tid = 0
        self.form = '-ROOT-'
        self.lemma = '-ROOT-'
        self.pos = '-ROOT-'
        self.head = None
        self.label = '-ROOT-'
        self.sec_heads = {}
        self.sec_subj = {}
        self.sec_deps = {}
        self.deps = []


def update_label(token1, token2, label, overwrite = False):
    """
    Update the output entries of a token, if it is assigned a new label.
    used in mapping the prediction back to original conll data
    """
    if label and (overwrite or token1 not in token2.sec_heads):
        token1.sec_subj[token2] = label
        token1.sec_deps[token2] = label #?
        token2.sec_heads[token1.tid] = label




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
            sentence[int(index) - 1].sec_deps[token] = label
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
        self.inv_feattab = {v:k for k, v in self.feattab.items()}


    def mapback_label( self, i):
        return self.inv_labeltab.get(i, None)

    def mapback_feature( self, i):
        return self.inv_feattab.get(i, None)



def write_to_file( label, features, fileobj ):
    features = set(features)
    features.discard(None)
    print >> fileobj, '%d %s' % (label,' '.join(map(lambda x: '%d:1' % x,sorted(features))))





# travese all possible verb subject pairs
def traverse_train(sentence, feattab, feat_filter, outstream, label_filter = None):
    for tid1, verb in enumerate(sentence):
        if  verb.pos[0] == 'V' and  verb.head.pos != '-ROOT-':
            useful_tokens = get_useful_tokens( verb, sentence)
            verb_features = make_verb_feature_vector(useful_tokens, verb, sentence)
            if label_filter: # for mapping RE
                for noun in verb.sec_subj:
                    label = verb.sec_subj[noun]
                    if label in label_filter:
                        label = feattab.labeltab[label]
                        noun_features = make_noun_feature_vector(useful_tokens, noun, sentence)
                        features = add_features(verb_features, noun_features, feattab.register_feature, feat_filter)
                        write_to_file(label, features, outstream)
                        # debug
                        # for k, v in filter(lambda x: x[0] in feat_filter and x[1], verb_features.items() + noun_features.items()):
                        #     print k, v
            else:
                for noun in related_nouns(verb):
                    if noun in  verb.sec_subj:
                        label = feattab.register_label( verb.sec_subj[noun])
                    else:
                        label = feattab.register_label('')
                    noun_features = make_noun_feature_vector(useful_tokens, noun, sentence)
                    features = add_features(verb_features, noun_features, feattab.register_feature, feat_filter)
                    write_to_file(label, features, outstream)
                    # debug
                    # print verb.form, '-->', noun.form
                    # for k, v in filter(lambda x: x[0] in feat_filter and x[1], verb_features.items() + noun_features.items()):
                    #     print '\t',k, v

# travese all possible verb subject pairs
def traverse_pred(sentence, feattab, feat_filter, outstream, label_filter = None):
    for tid1, verb in enumerate(sentence):

        if  verb.pos[0] == 'V' and  verb.head.pos != '-ROOT-':
            useful_tokens = get_useful_tokens( verb, sentence)
            verb_features = make_verb_feature_vector(useful_tokens, verb, sentence)

            if label_filter: # for mapping RE
                for noun in verb.sec_subj:
                    label = verb.sec_subj[noun]
                    if label in label_filter:
                        noun_features = make_noun_feature_vector(useful_tokens, noun, sentence)
                        # print verb.form, '-->', noun.form

                        features = add_features(verb_features, noun_features, feattab.map_feature, feat_filter, False)
                        write_to_file(0, features, outstream)
                        # debug
                        # for k, v in filter(lambda x: x[0] in feat_filter and x[1], verb_features.items() + noun_features.items()):
                            # print k, v
            else:
                for noun in related_nouns(verb):
                    noun_features = make_noun_feature_vector(useful_tokens, noun, sentence)
                    print verb.form, '-->', noun.form

                    features = add_features(verb_features, noun_features, feattab.map_feature, feat_filter, True)
                    write_to_file(0,features,outstream)
                    # # debug
                    # for k, v in filter(lambda x: x[0] in feat_filter and x[1], verb_features.items() + noun_features.items()):
                    # # for k, v in verb_features.items() + noun_features.items():
                    #     print '\t', k, v

# travese all possible verb subject pairs
def traverse_mapback(sentence, feattab, outstream, pred, label_filter = None):
    for tid1, verb in enumerate(sentence):
        if  verb.pos[0] == 'V' and  verb.head.pos != '-ROOT-':
            if label_filter: # for mapping RE
                for noun in verb.sec_subj:
                    label = verb.sec_subj[noun]
                    if label in label_filter:
                        pred_label = feattab.mapback_label(int(pred.readline()))
                        update_label(verb, noun, pred_label, False)
            else:
                for noun in related_nouns(verb):
                    pred_label = feattab.mapback_label(int(pred.readline()))
                    if pred_label:
                        update_label( verb, noun, pred_label)
    for tid, token in enumerate(sentence):
        print >> outstream, token.to_line()
    print >> outstream, ''


def related_nouns(verb):
    nouns = []
    chain = chain_to_root(verb)
    for verb in filter(lambda x: x.pos[0] == 'V', chain):
        for path in [['SB'], ['OA'], ['DA'], ['OP', 'NK']]:
            noun = get_token_by_path(verb, path)
            if noun and noun not in chain:
                nouns.append(noun)
    return nouns


# save some usful tokens in a dictionary to use later
def get_useful_tokens(verb, sentence):
    dic = {}
    # head, head's head, and head's head's head
    dic['VERB'] = verb
    dic['HEAD1'] = skip_conj_head(verb, 1)
    dic['HEAD2'] = skip_conj_head(verb, 2)
    dic['HEAD3'] = skip_conj_head(verb, 3)
    # subject, direct object, dative object, and prepositional object on each head
    dic['HEAD1.SB'] = get_token_by_path(dic['HEAD1'], ['SB'])
    dic['HEAD1.OA'] = get_token_by_path(dic['HEAD1'], ['OA'])
    dic['HEAD1.DA'] = get_token_by_path(dic['HEAD1'], ['DA'])
    dic['HEAD1.OP.NK'] = get_token_by_path(dic['HEAD1'], ['OP', 'NK'])
    dic['HEAD2.SB'] = get_token_by_path(dic['HEAD2'], ['SB'])
    dic['HEAD2.OA'] = get_token_by_path(dic['HEAD2'], ['OA'])
    dic['HEAD2.DA'] = get_token_by_path(dic['HEAD2'], ['DA'])
    dic['HEAD2.OP.NK'] = get_token_by_path(dic['HEAD2'], ['OP', 'NK'])
    dic['HEAD3.SB'] = get_token_by_path(dic['HEAD3'], ['SB'])
    dic['HEAD3.OA'] = get_token_by_path(dic['HEAD3'], ['OA'])
    dic['HEAD3.DA'] = get_token_by_path(dic['HEAD3'], ['DA'])
    dic['HEAD3.OP.NK'] = get_token_by_path(dic['HEAD3'], ['OP', 'NK'])
    sb = [dic['HEAD%d.SB' % i] for i in [1,2,3] if dic['HEAD%d.SB' % i]]
    oa = [dic['HEAD%d.OA' % i] for i in [1,2,3] if dic['HEAD%d.OA' % i]]
    da = [dic['HEAD%d.DA' % i] for i in [1,2,3] if dic['HEAD%d.DA' % i]]
    op = [dic['HEAD%d.OP.NK' % i] for i in [1,2,3] if dic['HEAD%d.OP.NK' % i]]
    if sb:
        dic['CLOSEST_SB'] = sb[0]
    if oa:
        dic['CLOSEST_OA'] = oa[0]
    if da:
        dic['CLOSEST_DA'] = da[0]
    if op:
        dic['CLOSEST_OP.NK'] = op[0]

    # # wrong!!!
    # for i in [1,2,3]:
    #     for role in ['OA', 'DA', 'OP.NK']:
    #         print i, role, dic['HEAD%d.%s' % (i, role)], dic['HEAD%d.SB' % i]
    #         if not dic['HEAD%d.%s' % (i, role)] and dic['HEAD%d.SB' % i]:
    #             dic['CLOSEST_SB_ONLY'] = dic['HEAD%d.SB' % i]

    return dic


# Make features for candidates of a verb in a sencondary dependency
def make_verb_feature_vector(useful_tokens, verb, sentence):   
    # print verb.form
    features = {}
    root_path = chain_to_root(verb)
    root_path_pos = map(lambda x: x.pos, root_path)
    root_path_label = map(lambda x: skip_conj_label(x), root_path)
    root_path_pos_label = map(lambda x: x[0] + '/' + x[1], zip(root_path_pos, root_path_label))
    root_path_lemma = map(lambda x: x.lemma, root_path)

    # features.append(mapfunc('SELF.LEMMA:%s' % verb.lemma)) # decresed the accuracy, try embed brown cluster

    # POS and label of the path to root
    # features.append(mapfunc('PATH.POS:%s' % '_'.join(root_path_pos)))
    # features.append(mapfunc('PATH.LABEL:%s' % '_'.join(root_path_label)))
    features['PATH.POS'] = '_'.join(root_path_pos)
    features['PATH.LABEL'] = '_'.join(root_path_label)
    features['PATH.LABEL~POS'] = '_'.join(root_path_pos_label)
    features['PATH.LEMMA'] = '_'.join(root_path_lemma)
    # prefixes of path to root
    # features.append(mapfunc('PATH.P1.POS:%s' % root_path_pos[0])) #?
    # features.append(mapfunc('PATH.P2.POS:%s' % '_'.join((root_path_pos + ['--'])[:2]))) #?
    features['PATH.P1.LABEL'] = root_path_label[0]
    features['PATH.P2.LABEL'] = '_'.join((root_path_label + ['--'])[:2])
    # features['PATH.F3.LABEL'] = '_'.join((root_path_label + ['--', '--'])[:3])))

    # lemmas of the heads
    features['HEAD1.LEMMA'] = get_lemma(useful_tokens['HEAD1'])
    features['HEAD2.LEMMA'] = get_lemma(useful_tokens['HEAD2'])
    features['HEAD3.LEMMA'] = get_lemma(useful_tokens['HEAD3'])
    features['SELF.LEMMA'] = get_lemma(useful_tokens['VERB'])

    features['SELF.LEMMA+HEAD1.LEMMA'] = features['SELF.LEMMA'] + '+' + features['HEAD1.LEMMA']
    features['SELF.LEMMA+HEAD2.LEMMA'] = features['SELF.LEMMA'] + '+' + features['HEAD2.LEMMA']
    features['SELF.LEMMA+HEAD3.LEMMA'] = features['SELF.LEMMA'] + '+' + features['HEAD3.LEMMA']


    # whether the verb is infinitive with zu
    features['ZU_INF'] = str(verb.pos == 'VVIZU' or get_token_by_path(verb, ['PM']) != None)

    # if features['ZU_INF']:
    features['ZU_INF~HEAD1.LEMMA'] = features['HEAD1.LEMMA'] + '+' + str(features['ZU_INF'])
    features['ZU_INF~HEAD2.LEMMA'] = features['HEAD2.LEMMA'] + '+' + str(features['ZU_INF']) 
    features['ZU_INF~HEAD3.LEMMA'] = features['HEAD3.LEMMA'] + '+' + str(features['ZU_INF']) 




    # POS of the verb's OC dependant if there is one
    features['SELF.OC.POS'] = get_pos(get_token_by_path(verb, ['OC']))
    # whether the verb has "wie", "weil", "um" etc

    for pos in ['KOUI', 'KOUS', 'PWAV', 'PAV', 'PRELS', 'PRELAT']:
        features['SELF.%s' % pos] = (get_deps_by_pos(verb, pos) != [])



    for role in useful_tokens:
        features[role] = get_pos(useful_tokens[role])




    return features


# Make features for candidates of a subject in a secondary dependency 
# (not necessary to be a noun, just easier to understand)
def make_noun_feature_vector(useful_tokens, noun, sentence):
    # print noun.form
    args = ['SB', 'OA', 'DA', 'OP.NK']
    features = {}
    features['NOUN_POS'] = noun.pos 
    # s = struct(useful_tokens['VERB'], noun)
    # features['STRUCT'] = s
    for role in useful_tokens:
        if (noun == useful_tokens[role]):
            features['NOUN_IS_%s' % role] = True
            head = role.split('.')[0]
            if head in ['HEAD1', 'HEAD2', 'HEAD3']:
                noun_arg = '.'.join(role.split('.')[1:])
                features['%s.LEMMA+NOUN_IS_%s' % (head, role)] = useful_tokens[head].lemma
                features['HEAD.LEMMA'] = useful_tokens[head].lemma
                features['NOUN_POS+HEAD.LEMMA'] = noun.pos + '+' + useful_tokens[head].lemma
                if head == 'HEAD1':
                    for arg in args:
                        if arg != noun_arg:
                            features['SIB_' + arg] = str(useful_tokens[head + '.' + arg]!=None)
                            features['NOUN.LABEL+SIB_' + arg] = noun_arg + '+' + features['SIB_' + arg]
                elif head == 'HEAD2':
                    for arg in args:
                        if arg != noun_arg:
                            features['SIB_' + arg] = str(useful_tokens[head + '.' + arg]!=None)
                            features['NOUN.LABEL+SIB_' + arg] = noun_arg + '+' + features['SIB_' + arg]

                        features['CLOSER_' + arg] = str(useful_tokens['HEAD1.' + arg]!=None)
                        features['NOUN.LABEL+CLOSER_' + arg] = noun_arg + '+' + features['CLOSER_' + arg]

                else:
                    for arg in args:
                        if arg != noun_arg:
                            features['SIB_' + arg] = str(useful_tokens[head + '.' + arg]!=None)
                            features['NOUN.LABEL+SIB_' + arg] = noun_arg + '+' + features['SIB_' + arg]

                        features['CLOSER_' + arg] = str(useful_tokens['HEAD1.' + arg]!=None or useful_tokens['HEAD2.' + arg]!=None)
                        features['NOUN.LABEL+CLOSER_' + arg] = noun_arg + '+' + features['CLOSER_' + arg]



    # experimental
    # features.append(mapfunc('NOUN_BEFORE_VERB:%s' % (int(noun.tid) < int(useful_tokens['VERB'].tid))))
    # if useful_tokens['HEAD1'] and str(useful_tokens['HEAD1'].tid) in noun.sec_heads:
    #     features.append(mapfunc('NOUN_IS_HEAD1.SECSUBJ'))
    # features.append(mapfunc('NOUN_IS_HEAD2.SECSUBJ:%s' % (useful_tokens['HEAD2'] and str(useful_tokens['HEAD2'].tid) in noun.sec_heads)))
    # features.append(mapfunc('NOUN_BEFORE_HEAD1:%s' % (int(noun.tid) < int(useful_tokens['HEAD1'].tid))))
    # features.append(mapfunc('NOUN_BEFORE_HEAD2:%s' % (int(noun.tid) < int(useful_tokens['HEAD2'].tid))))
    # features.append(mapfunc('NOUN_BEFORE_HEAD3:%s' % (int(noun.tid) < int(useful_tokens['HEAD3'].tid))))
    return features

def add_features(verb_features, noun_features, mapfunc, feat_filter, debug = False):
    features = []
    for k, v in filter(lambda x: all([f in feat_filter for f in x[0].split('+')]) and x[1], verb_features.items() + noun_features.items()):
        features.append(mapfunc('%s:%s' % (k, v)))
        if debug:
            print '\t', k, v
    return features

def read_feat_filter(filename):
    return [line.strip() for line in open(filename) if line.strip()]


def print_features(feattab, features, verb, noun):
    print verb.form, '-->', noun.form
    for f in features:
        print '\t', feattab.mapback_feature(f)


# Return the path of tokens from a given token(incl.) to root(excl.), skipping dependency of conjunctions
# e.g. a path "ROOT --> Verb -OA-> Noun1 -CJ-> Noun2 -CD-> und -CJ-> Noun3", 
# chain_to_root(sentence, Noun3) will return [Noun3, Verb]
def chain_to_root(token):
    # skip the CJ/CD nodes
    chain = []
    while token.pos != '-ROOT-':
        chain.append(token)
        token = skip_conj_head(token)
    return chain

# Return the head of a given token, skipping dependency of conjunctions
# setting a level higher than 1 can get the ancestor of the token
def skip_conj_head(token, level = 1):
    for i in range(level):
        while token.label in ['CD', 'CJ']:
            token = token.head
        token = token.head
        if token.pos == '-ROOT-':
            break
    return token


# Return the label of the token to its head, skipping dependency of conjunctions
def skip_conj_label(token):
    while token.label in ['CD', 'CJ']:
        token = token.head
    return token.label


# Return the first matching token of a start token and a path
# e.g. get_token_by_path(sentence, token, ['OP', 'NK'] means
# the NK dependant of the OP dependant of the given token
# Doesn't handle multiple matches and conjuncts(and mostly shouldn't), 
# but for our purpose it works in general
def get_token_by_path(token, path):
    root_path = chain_to_root(token)
    for label in path:
        token = [d for d in token.deps if d.label == label] + [d for d in token.sec_deps if token.sec_deps[d] == label]
        token = filter(lambda x: x not in root_path, token)
        if not token:
            return None
        else:
            token = token[0]
    return token




def get_deps_by_pos(token, pos):
    if type(pos) == str:
        return [dep for dep in token.deps if dep.pos == pos]
    elif type(pos) == list:
        return [dep for dep in token.deps if dep.pos in pos]



# Return the POS tag of a token
def get_pos(token):
    if token:
        return token.pos
    else:
        return None
# Return the lemma of a token
def get_lemma(token):
    if token:
        return token.lemma
    else:
        return None

def struct(verb, noun):
    found = False
    string = ''
    chain = chain_to_root(verb)
    if len(chain) > 3:
        chain = chain[1:3]
    string = '*%s(%s)' % (verb.pos, verb.label)
    for token in chain:
        string += '%s(%s)[' % (token.pos, token.label)
        sb = get_token_by_path(token, ['SB'])
        oa = get_token_by_path(token, ['OA'])
        da = get_token_by_path(token, ['DA'])
        op = get_token_by_path(token, ['OP','NK'])
        if noun in [sb, oa, da, op]:
            found = True
        if sb:
            if noun == sb:
                string += '*'
            string += '%s(%s)' % (sb.pos, sb.label)
        if oa:
            if noun == oa:
                string += '*'
            string += '%s(%s)' % (oa.pos, oa.label)
        if da:
            if noun == da:
                string += '*'
            string += '%s(%s)' % (da.pos, da.label)
        if op:
            if noun == op:
                string += '*'
            string += '%s(%s)' % (op.pos, op.label)
        string += ']'
        if found:
            break
        # print 'struct', token.pos

    return string



