#!/bin/python
# -*- coding: utf-8 -*-


import bs4, sys, re
debug = 0
sid = 17

STEP = '1'
STAT = {'SBM': 0, 'SBA': 0, 'SBR': 0, 'SBE': 0, 'SBC': 0, 'SBU': 0}


#####################################
# walk through all sents or debug
# todo: pickle instead of dic

def test(input_file, raising_file, equi_file, sid):
    raising_dic = read_dic(raising_file)
    equi_dic = read_dic(equi_file)
    print 'reading corpus...'
    origin_text = open(input_file).read()
    pattern = re.compile(r'<s id="s%d".*?</s>\r\n' % sid, re.DOTALL)
    m = pattern.search(origin_text)
    if m:
        sent = m.group()
        sent = bs4.BeautifulSoup(sent, 'xml')
        process(sent.graph, raising_dic, equi_dic)

    write_soup('test.xml', sent.prettify('utf-8', formatter = convert_entity))


def walk(input_file, output_file, raising_file, equi_file, start = 0, end = 60000):
    raising_dic = read_dic(raising_file)
    equi_dic = read_dic(equi_file)
    print 'reading corpus...'
    origin_text = open(input_file).read() # del .decode()
    pattern = re.compile(r'<s id=.*?</s>\r\n', re.DOTALL)
    corpus = pattern.findall(origin_text)
    print 'done', len(corpus)

    g = open(output_file, 'w')
    g.write(open('../TIGER/head.xml').read())
    g.write('<body>\r\n')

    for sent in corpus:
        sent = bs4.BeautifulSoup(sent, 'xml', from_encoding="utf-8")
        sid = int(sent.graph['root'].split('_')[0][1:])
        if sid >= start and sid <= end:
            process(sent.graph, raising_dic, equi_dic)
        g.write(sent.s.prettify('utf-8', formatter = convert_entity) + '\r\n')


    g.write('</body>\r\n</corpus>\r\n')
    g.close()
    print 'SBM:', STAT['SBM']
    print 'SBA:', STAT['SBA']
    print 'SBR:', STAT['SBR']
    print 'SBE:', STAT['SBE']
    print 'SBC:', STAT['SBC']
    # print 'NOR:', STAT['NOR']
    # print 'NOE:', STAT['NOE']
    # print 'NOC:', STAT['NOC']
    # print 'NOM:', STAT['NOM']




def process(graph, raising_dic, equi_dic):
    root = root_node(graph)
    sid = int(root['id'].split('_')[0][1:])
    if sid %2000 == 0:
        print '.',


    # step 1: find SBM, SBA
    if '1' in STEP:
        mod_aux_helper(graph, root)

    # step 2: find SBR using informations from LFG
    if '2' in STEP:
        if sid in raising_dic:
            for items in raising_dic[sid]:
                ctrl_helper(graph, items, '-r')

    # step 3: find SBE using informations from LFG
    if '3' in STEP:
        if sid in equi_dic:
            for items in equi_dic[sid]:
                ctrl_helper(graph, items, '-e')

    # (optional) find control(SBC) without information from LFG
    if '4' in STEP:
        ctrl_without_lfg(graph, root)

    # (optional) ???
    if '5' in STEP:
        ctrl_finder_helper(graph, root)

    # (optional) inspect the zu-infinitive verb which has no secondary edges
    if '6' in STEP:
        vz_no_edge(graph)



#####################################


#####################################

def mod_aux_helper(graph, node, subj = None, label = ''):
    """
    step 1: add secedge to SBA and SBM
    Recursively find modal verbs and auxiliaries and mark them
    """
    mod, aux, oc, verb = None, None, None, None
    aux_oc_wait = None

    # mark mod or wait for aux
    if label == 'm':
        mark(graph, subj, node, 'SBM')
    elif label == 'a':
        # if OA is a VZ or VVIZU, then ignore it, it might be a case of raising (see s277),
        # otherwise, keep it as candidate of auxiliary, but only mark it if it's the end 
        # of the auxliary verb chain
        if not any([c for c in child_nodes(graph, node) if c.name == 't' and c['pos'] == 'VVIZU' \
                                                                or c.name == 'nt' and c['cat'] in ['VZ', 'CVZ']]):
            aux_oc_wait = node

    # check all children of the current node, to find new subj, mod/aux/verb, and oc
    if node.name == 'nt':
        children = child_nodes(graph, node)

        # first, find new subj, a subject closer to the verb can replace the more distanced one
        new_subj = child_nodes(graph, node, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE'])
        if new_subj:
            subj = new_subj[0]
            label = ''

        # find mod/aux/verb, oc
        for child in children:
            edge_label = get_label(graph, child)
            # mark mod or aux
            if edge_label == 'HD' and child.name == 't':
                if child['pos'] in ['VMINF', 'VMFIN', 'VMPP']:
                    mod = child
                elif child['pos'] in ['VAINF', 'VAFIN', 'VAPP']:
                    aux = child
                else:
                    verb = child
                # mod_aux_helper(graph, child)

            # ?
            elif edge_label == 'OC' and not (child.name == 'nt' and child['cat'] in ['VZ', 'CVZ']\
                                             or child.name == 't' and child['pos'] == 'VVIZU'):
                oc = child
                mod_aux_helper(graph, child, subj)

            # rest just call helper
            else:
                mod_aux_helper(graph, child)

        if not label:
            if oc:
                # # print phrase(graph, subj), ',',  phrase(graph, mod) + phrase(graph, aux) ,',',phrase(graph, oc)
                # # black magic here, can replace by call helper several times for each conj 
                # if mod and oc.name == 'nt' and oc['cat'] == 'CVP':
                #     # print 1
                #     mark(graph, subj, oc, 'SBM')
                # else:
                if mod:
                    # print 2
                    mod_aux_helper(graph, oc, subj, 'm')
                elif aux:
                    # print 3
                    mod_aux_helper(graph, oc, subj, 'a')

    # if it's an aux at the end of the chain, then mark it, otherwise search deeper
    if aux_oc_wait:
        if verb or mod or not oc:
            mark(graph, subj, aux_oc_wait, 'SBA')
        elif aux:
            mod_aux_helper(graph, oc, subj, 'a')



#####################################


#####################################

def ctrl_helper(graph, items, flag):
    """
    step 2 and 3: add secedge to SBR and SBE
    """
    sid, ctrl_type, ctrl_indices, main_indices, comp_indices = items

    lfg_main_set = set_without_punctuation(graph, main_indices)
    lfg_ctrl_set = set_without_punctuation(graph, ctrl_indices)
    lfg_comp_set = set_without_punctuation(graph, comp_indices)


    comp, ctrl, main = None, None, None

    # first find comp, then ctrl
    comp = find_comp(graph, lfg_comp_set)
    # print comp
    if comp:
        comp_set = range_of_phrase(graph, comp)
        # parent = find_highst_node(graph, comp_set)
        main = find_main(graph, lfg_main_set)   

        main, comp = find_real_main_comp(graph, main, comp)

        if debug:
            print phrase(graph, main)
            # print phrase(graph, comp)

        # ?
        main_parent_oc_sets = map(lambda x: range_of_phrase(graph, x), child_nodes(graph, parent_node(graph, main), ['OC', 'OP', 'MO', 'PD']))
        if not any(comp_set <= s for s in main_parent_oc_sets):
            print 'exception:', sid
            return

        if flag == '-r':
            label = 'SBR'
            ctrl = find_subj(graph, comp, main)
        else:
            label = 'SBE'
            ctrl = find_ctrl(graph, lfg_ctrl_set, comp, main, ctrl_type)

        if ctrl:   
            ctrl_set = range_of_phrase(graph, ctrl)
            # two sets not contain each other
            # in other words, a node cannot attached to its ancestor, vice versa
            if not ctrl_set <= comp_set and not comp_set <= ctrl_set:
                mark(graph, ctrl, comp, label)
            else:
                print 'exception:', sid

        else:
            print '-----CTRL Not Found-----\t',sid
    if not comp:
        print '-----COMP Not Found-----\t',sid 

#####################################



#####################################
# functions to find specific nodes 


def find_ctrl(graph, lfg_ctrl_set, comp, main, ctrl_type):
    """
    find controller, namely subject or object.
    argument ctrl_type is not used, which is part of the result from LFG, not very reliable
    here simply uses the heuristics that if there is an object which is not reflexive pronoun,
    then select it as the controller, otherwise select the subject.
    in experiment can combine the heuristics and ctrl_type to make a conservative choice
    by only assign the cases where they agree, otherwise discard. 
    """
    subj = find_subj(graph, comp, main)
    if main and comp:
        obj = child_node(graph, parent_node(graph, main), ['OA', 'DA'])

        if obj and (obj.name == 'nt' or obj['pos'] != 'PRF'):
            # write_results('o', graph, obj, main, comp)
            return obj
        elif subj:
            # write_results('s', graph, subj, main, comp)
            return subj
    return None



def find_real_main_comp(graph, main, comp):
    """
    !!!!!!
    find the real main verb and comp, given those from LFG
    little bit messy, try to leave it and see if anything changes    
    """
    # obj = None
    real_main, real_comp = main, comp
    if main and comp:
        top = parent_node(graph, main)
        # locate the real comp as bottom for search of OA
        if get_label(graph, comp) in ['OC', 'CJ', 'RE']:
            bottom = comp
        elif get_label(graph, comp) in ['HD']:
            bottom = parent_node(graph, comp)
            real_comp = bottom
        else:
            bottom = None
            print 'Warning: label of comp is %s' % get_label(graph, comp)
        while bottom and top and top != bottom:
            tmp = child_node(graph, top, ['HD'])
            if tmp:
                real_main = tmp
            # obj = child_node(graph, top, ['OA', 'DA'])
            top = child_node(graph, top, ['OC', 'PD'])
    return real_main, real_comp



def find_subj(graph, comp, main):
    """
    find the subject of the main verb
    including secondary edges of verb complement or main verb
    """
    tmp = comp
    edge_sb = tmp.find(lambda x: x.name == 'edge' and x['label'] in ['SB'])
    secedge_sb = graph.find(lambda x: x.name == 'secedge' and x['label'].startswith('SB') and x['idref'] == tmp['id'])
    secedge_hd_sb = None
    while tmp and not edge_sb and not secedge_sb and not secedge_hd_sb:
        edge_sb = tmp.find(lambda x: x.name == 'edge' and x['label'] in ['SB'])
        secedge_sb = graph.find(lambda x: x.name == 'secedge' and x['label'].startswith('SB') and x['idref'] == tmp['id'])
        edge_hd = tmp.find(lambda x: x.name == 'edge' and x['label'] == 'HD')
        if edge_hd:
            secedge_hd_sb = graph.find(lambda x: x.name == 'secedge' and x['label'].startswith('SB') and x['idref'] == edge_hd['idref'])
        tmp = parent_node(graph, tmp)

    if edge_sb:
        return graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == edge_sb['idref'])
    if secedge_sb:
        return secedge_sb.parent
    if secedge_hd_sb:
        return secedge_hd_sb.parent
    return None


def find_comp(graph, comp_set):
    """
    find the phrase of the verb complement 
    """
    cands = []
    comp = None

    for t in graph.terminals:
        if type(t) == bs4.element.Tag:
            s = range_of_phrase(graph, t)
            if range_of_phrase(graph, t) <= comp_set and t['pos'][0] == 'V':
                cands.append(t)
    if cands:
        comp = highest_node(graph, cands)

        parent = parent_node(graph, comp)
        while parent and parent['cat'] in ['CVP', 'CVZ', 'VZ', 'VP'] and not range_of_phrase(graph, parent) > comp_set:
            comp = parent
            parent = parent_node(graph, comp)

        if get_label(graph, comp) == 'CJ':
            parent = parent_node(graph, comp)
            if get_label(graph, parent) in ['OC', 'PD']:
                comp = parent
    return comp




def find_main(graph, main_set):
    """
    find the main verb phrase of the controll construction 
    """
    m, ans = None, None
    edge_cands = graph.find_all(lambda x: x.name == 'edge' and x['label'] == 'HD' and range_of_phrase(graph, x) <= main_set)
    if edge_cands:
        edge = edge_cands[0]
        ans = graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == edge['idref'])
        if len(edge_cands) > 1:
            for e in edge_cands[1:]:
                m = graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == e['idref'])
                if m and range_of_phrase(graph, m) <= main_set and m not in parent_node(graph, ans):
                    ans = m
    else:
        print 'oops, no main'
    return ans


#####################################







#####################################
# helper functions to deal with xml 



def mark(graph, subj, verb, label):
    if verb.name == 'nt' and verb['cat'] in ['CVP', 'CVZ']:
        for conj in child_nodes(graph, verb, ['CJ']):
            mark_helper(graph, subj, conj, label)
    else:
        mark_helper(graph, subj, verb, label)


def mark_helper(graph, subj, verb, label):
    global STAT
    if subj and not subj.find(lambda x: x.name == 'secedge' and x['idref'] == verb['id']) and not cover(graph, subj, verb):
        print subj['id'].split('_')[0],
        print '\t%s\t%s --> %s' % (label, phrase(graph, subj), phrase(graph, verb))
        secedge = bs4.BeautifulSoup('<secedge label="%s" idref="%s" />' % (label, verb['id']), 'xml').secedge
        subj.append(secedge)
        subj.append('\r\n')
        STAT[label] += 1


def convert_entity(s):
    return s.replace('&','&amp;').replace('<', '&lt;').replace('>', '&gt;')


def parent_node(graph, tag):
    edge = graph.find(lambda x: x.name == 'edge' and x['idref'] == tag['id'])
    if edge:
        return edge.parent

def get_label(graph, tag):
    return graph.find(lambda x: x.name == 'edge' and x['idref'] == tag['id'])['label']


def child_node(graph, tag, child_labels, preference = False):
    if preference:
        for label in child_labels:
            edge = tag.find(lambda x: x.name == 'edge' and x['label'] == label)
            if edge:
                return graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == edge['idref'])
               
    else:
        edge = tag.find(lambda x: x.name == 'edge' and x['label'] in child_labels)
        if edge:
            return graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == edge['idref'])

def child_nodes(graph, tag, child_labels = [], secedge_labels = []):
    nodes = []
    edges = tag.find_all(lambda x: x.name == 'edge' and (not child_labels or x['label'] in child_labels))
    if edges:
        nodes += map(lambda e: graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == e['idref']), edges)
    if secedge_labels:
        secedges = graph.find_all(lambda x: x.name == 'secedge' and x['idref'] == tag['id'] and x['label'] in secedge_labels)
        nodes += map(lambda e: e.parent, secedges)
    return nodes

def root_node(graph):
    root = graph.find(lambda x: x.name == 'nt' and x['cat'] == 'VROOT')
    if not root:
        for nt in graph.nonterminals:
            if type(nt) == bs4.element.Tag and not graph.find(lambda x: x.name == 'edge' and x['idref'] == nt['id']):
                root = nt
                break
    if not root:
        root = graph.find(lambda x: x.name in ['t', 'nt'])
    return root

def highest_node(graph, nodes):
    return max(nodes, key = lambda x: range_of_phrase(graph, hd_chain_parent(graph, x)))

def hd_chain_parent(graph, node):
    while get_label(graph, node) == 'HD':
        node = parent_node(graph, node)
    return node


def range_of_phrase(graph, tag):
    if not tag:
        return set()
    s = set()
    if tag.name == 't':
        s = set([int(tag['id'].split('_')[1])])
    elif tag.name == 'nt':
        for child in tag.children:
            if type(child) == bs4.element.Tag and child.name == 'edge':
                idref = child['idref']
                s |= range_of_phrase(graph, graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == idref))
    return s


def words_of_phrase(graph, tag):
    if not tag:
        return []
    s = []
    if tag.name == 't':
        s = [tag['word']]
    elif tag.name == 'nt':
        for child in tag.children:
            if type(child) == bs4.element.Tag and child.name == 'edge':
                idref = child['idref']
                s += words_of_phrase(graph, graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == idref))
    return s

def phrase(graph, tag):
    return ' '.join(words_of_phrase(graph, tag)).encode('utf-8')


def set_without_punctuation(graph, indices):
    result = set(indices)
    # delete the punctuations from set!
    for t in graph.terminals:
        if type(t) == bs4.element.Tag and t['pos'][0] == '$':
            wid = int(t['id'].split('_')[1])
            result -= set([wid]) 
    return result   

def is_ancestor(graph, node1, node2):
    while node1 and node1['id'].split('_')[1] != 'VROOT':
        if node1['id'] == node2['id']:
            return True
        node1 = parent_node(graph, node1)
    return False

def cover(graph, node1, node2):
    return is_ancestor(graph, node1, node2) or is_ancestor(graph, node2, node1)

#####################################


#####################################
# functions to read an write

def read_dic(filename):
    ctrl_dic = {}
    for line in open(filename).readlines():
        tmp = line.strip().split(' | ')
        # tmp = line.decode('utf-8').strip().split(' | ')
        if int(tmp[0]) not in ctrl_dic:
            ctrl_dic[int(tmp[0])] = []
        ctrl_dic[int(tmp[0])].append((int(tmp[0]), tmp[1], map(int, tmp[2].split()), map(int, tmp[3].split()), map(int, tmp[4].split())))
    return ctrl_dic


def write_results(ctrl_type, graph, ctrl, main, comp):
    f = open('cmc.txt', 'a')
    f.write('%s | %s | %s | %s\n' % (ctrl_type, phrase(graph, ctrl), phrase(graph, main), phrase(graph, comp)))
    f.close()

def write_soup(output_name, text):
    g = open(output_name, 'w')
    g.write(text)
    g.close()

#####################################


#####################################
# playground

def ctrl_without_lfg(graph, node, subj = None, label = ''):
    if node.name == 'nt':
        children = child_nodes(graph, node)
        # find new subj
        new_subj = child_nodes(graph, node, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE'])
        if new_subj:
            subj = new_subj[0]
        if subj:
            obj = child_node(graph, node, ['DA', 'OA']) # sequence matters! 
            if obj.name == 't' and obj['pos'] == 'PRF':
                obj = None


            oa = child_node(graph, node, ['OA'])
            if oa and oa.name == 'nt' and oa['cat'] in ['NP']:
                oc_of_oa = child_node(graph, oa, ['OC', 'RE', 'MNR'])
                if oc_of_oa:
                    if oc_of_oa.name == 'nt':
                        if oc_of_oa['cat'] in ['VP', 'CVP', 'VZ', 'CVZ'] \
                            and not child_node(graph, oc_of_oa, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE']):
                            print 'OA', int(node['id'].split('_')[0][1:])
                            if obj and obj != oa:
                                print 'OBJ marked'
                                mark(graph, obj, oc_of_oa, 'SBE')
                            else:   
                                mark(graph, subj, oc_of_oa, 'SBC')
                    else:
                        if oc_of_oa['pos'] in ['VVIZU']:
                            print 'OA', int(node['id'].split('_')[0][1:])
                            if obj and obj != oa:
                                print 'OBJ marked'
                                mark(graph, obj, oc_of_oa, 'SBE')
                            else:   
                                mark(graph, subj, oc_of_oa, 'SBC')


            pd = child_node(graph, node, ['PD'])
            if pd and pd.name == 'nt' and pd['cat'] in ['AP']:
                oc_of_pd = child_node(graph, pd, ['OC'])
                if oc_of_pd:
                    if oc_of_pd.name == 'nt':
                        if oc_of_pd['cat'] in ['VP', 'CVP', 'VZ', 'CVZ'] \
                            and not child_node(graph, oc_of_pd, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE']):
                            print 'PD', int(node['id'].split('_')[0][1:])

                            mark(graph, subj, oc_of_pd, 'SBC')

                    else:
                        if oc_of_pd['pos'] in ['VVIZU']:
                            print 'OA', int(node['id'].split('_')[0][1:])

                            mark(graph, subj, oc_of_pd, 'SBC')

            mos = child_nodes(graph, node, ['MO'])
            for mo in mos:
                if mo.name == 'nt' and mo['cat'] in ['PP']:
                    re_of_mo = child_node(graph, mo, ['RE'])
                    if re_of_mo:
                        if re_of_mo.name == 'nt':
                            if re_of_mo['cat'] in ['VP', 'CVP', 'VZ', 'CVZ'] \
                                and not child_node(graph, re_of_mo, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE'])\
                                and not child_node(graph, re_of_mo, ['CP']):
                                print 'MO', int(node['id'].split('_')[0][1:])
                                if obj and obj != oa:
                                    print 'OBJ marked'
                                    mark(graph, obj, re_of_mo, 'SBE')
                                else:   
                                    mark(graph, subj, re_of_mo, 'SBC')
                        else:
                            if re_of_mo['pos'] in ['VVIZU'] and not child_node(graph, re_of_mo, ['CP']):
                                print 'MO', int(node['id'].split('_')[0][1:])
                                if obj and obj != oa:
                                    print 'OBJ marked'
                                    mark(graph, obj, re_of_mo, 'SBE')
                                else:   
                                    mark(graph, subj, re_of_mo, 'SBC')


            # for all other possible ctrl, ignored for now, but quite important
            # oc = child_node(graph, node, ['OC'])
            # if oc and (oc.name == 'nt' and oc['cat'] in ['VP', 'CVP', 'VZ','CVZ'] or oc.name == 't' and oc['pos'] == 'VVIZU')\
            # and not has_secedge(graph, subj, oc):
            #     print 'OC', int(node['id'].split('_')[0][1:])
            #     mark(graph, subj, oc, 'SBU')
            #     FIRST += 1


        # find other 
        for child in children:
            ctrl_without_lfg(graph, child, subj)


def vz_no_edge(graph):
    for nt in graph.nonterminals:
        if type(nt) == bs4.element.Tag and nt['cat'] == 'VZ':
            ori_nt = nt
            edge = incomming_secedge(graph, nt)
            while not edge:
                nt = parent_node(graph, nt)
                edge = incomming_secedge(graph, nt)
                if nt['id'].split('_')[1] == 'VROOT' or get_label(graph, nt) in ['OC']:
                    break
            if not edge:
                print nt['id'][1:].split('_')[0]
                print phrase(graph, ori_nt)
                # root = root_node(graph)
                # mark(graph, ori_nt, ori_nt, 'SBU')

    for nt in graph.terminals:
        if type(nt) == bs4.element.Tag and nt['pos'] == 'VVIZU':
            ori_nt = nt
            edge = incomming_secedge(graph, nt)
            while not edge:
                nt = parent_node(graph, nt)
                edge = incomming_secedge(graph, nt)
                if nt['id'].split('_')[1] == 'VROOT' or get_label(graph, nt) in ['OC']:
                    break
            if not edge:
                print nt['id'][1:].split('_')[0]
                print phrase(graph, ori_nt)
                # root = root_node(graph)
                # mark(graph, ori_nt, ori_nt, 'SBU')




def has_secedge(graph, fr, to):
    edges = fr.find_all('secedge')
    hd_bottom = child_node(graph, to, ['HD'])
    # print hd_bottom
    for edge in edges:
        node = graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == edge['idref'])
        # print node
        if get_label(graph, node) == 'CJ':
            node = parent_node(graph, node)
        # print node
        if (node == to or node == hd_bottom):
            return True
    return False


def incomming_secedge(graph, node):
    edge = graph.find(lambda x: x.name == 'secedge'  and x['idref'] == node['id'])
    return edge


#####################################


if __name__ == '__main__':
    # if debug == 0:
    #     walk('../TIGER/tiger5.0.xml','../TIGER/tiger9.1.1.xml', 'raising_indices.txt', 'equi_indices.txt')
    # elif debug == 1:
    #     test('../TIGER/tiger5.0.xml',  'raising_indices.txt', 'equi_indices.txt', sid)

    if len(sys.argv) == 6:
        STEP = sys.argv[5]
        walk(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print 'args: [input_file] [output_file] [rasing_file] [equi_file] [steps]'
        

