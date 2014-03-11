import bs4, os, re
debug = 0

sid = 17
collect = False
TOTAL, EXCEPTION = 0, 0
STEP = '123'
# if debug == 1:
#     STEP = '123'
# elif debug in [2,3]:
#     STEP = '4'
STAT = {'SBM': 0, 'SBA': 0, 'SBR': 0, 'SBE': 0, 'SBC': 0, 'SBU': 0, 'NOR': 0, 'NOE': 0, 'NOC': 0, 'NOM': 0}
MISSED = {}
ALL = {}
COLLECTION = ''
FIRST, SECOND, THIRD, FORTH = 0, 0, 0, 0

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

    i = 0
    for sent in corpus:
        sent = bs4.BeautifulSoup(sent, 'xml', from_encoding="utf-8")
        # process(sent.graph, raising_dic, equi_dic)
        # g.write(sent.s.prettify('utf-8', formatter = convert_entity) + '\r\n')
        gid = int(sent.graph['root'].split('_')[0][1:])
        if gid >= start and gid <= end:
            process(sent.graph, raising_dic, equi_dic)
            g.write(sent.s.prettify('utf-8', formatter = convert_entity) + '\r\n')
        else:
            g.write(sent.s.prettify('utf-8', formatter = convert_entity) + '\r\n')
        # i += 1
        # if i > 500:
        #     break

    g.write('</body>\r\n</corpus>\r\n')
    g.close()
    # if collect:
        # write_collection()
    print 'SBM:', STAT['SBM']
    print 'SBA:', STAT['SBA']
    print 'SBR:', STAT['SBR']
    print 'SBE:', STAT['SBE']
    print 'SBC:', STAT['SBC']
    print 'NOR:', STAT['NOR']
    print 'NOE:', STAT['NOE']
    print 'NOC:', STAT['NOC']
    print 'NOM:', STAT['NOM']
    print 'FIRST', FIRST


    if '4' in STEP:

        f = open('missed_stats.txt', 'w')

        f.write('total: %d\n' % sum([len(ALL[l]) for l in ALL]))
        f.write('missed: %d\n\n' % sum([len(MISSED[l]) for l in MISSED]))

        for lemma in ALL:
            if lemma not in MISSED:
                MISSED[lemma] = []

        for lemma in sorted(ALL.keys(), key = lambda x: len(MISSED[x]), reverse = True):
            f.write('%s\t\t%d / %d\n' % (lemma, len(MISSED[lemma]), len(ALL[lemma])))

        f.write('\n\n\n\n\n')

        for lemma in sorted(ALL.keys(), key = lambda x: len(MISSED[x]), reverse = True):
            f.write('%s\t%d / %d\n' % (lemma, len(MISSED[lemma]), len(ALL[lemma])))
            f.write(', '.join(MISSED[lemma]) + '\n\n')
        f.close()




def process(graph, raising_dic, equi_dic):

    root = root_node(graph)
    # print sid
    sid = int(root['id'].split('_')[0][1:])
    # print sid

    # step 1: SBM, SBA
    if '1' in STEP:
        mod_aux_helper(graph, root)

    # step 2: SBR
    if '2' in STEP:
        if sid in raising_dic:
            for items in raising_dic[sid]:
                ctrl_helper(graph, items, '-r')

    # step 3: SBE
    if '3' in STEP:
        if sid in equi_dic:
            for items in equi_dic[sid]:
                ctrl_helper(graph, items, '-e')

    # if '4' in STEP:
    #     ctrl_finder_helper(graph, root)

    # step 5: ctrl_without_lfg
    if '4' in STEP:
        ctrl_without_lfg(graph, root)

    if '5' in STEP:
        vz_no_edge(graph)



#####################################


#####################################
# step 1: add secedge to SBA and SBM


# with some bug to cause inefficiency
def mod_aux_helper(graph, node, subj = None, label = ''):
    mod, aux, oc, hd = None, None, None, None
    aux_oc_wait = None

    # mark mod or wait for aux
    if label == 'm':
        # print label, phrase(graph, subj), '->', phrase(graph, node)
        mark(graph, subj, node, 'SBM')
    elif label == 'a':
        # print label, phrase(graph, subj), '->', phrase(graph, node), 'WAIT!'

        # if not OA is a VZ or VVIZU, then ignore it!!! see s277
        if not any([c for c in child_nodes(graph, node) if c.name == 't' and c['pos'] == 'VVIZU' or c.name == 'nt' and c['cat'] in ['VZ', 'CVZ']]):
            aux_oc_wait = node

    # check all children of the current node, to find new subj, mod/aux/hd, and oc
    if node.name == 'nt':
        children = child_nodes(graph, node)
        # print [c['id'] for c in children], '\n'

        # find new subj
        new_subj = child_nodes(graph, node, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE'])
        if new_subj:
            subj = new_subj[0]
            label = ''

        # find mod/aux/hd, oc
        for child in children:
            edge_label = get_label(graph, child)
            # mark mod or aux
            if edge_label == 'HD' and child.name == 't':
                if child['pos'] in ['VMINF', 'VMFIN', 'VMPP']:
                    mod = child
                elif child['pos'] in ['VAINF', 'VAFIN', 'VAPP']:
                    aux = child
                else:
                    hd = child
                mod_aux_helper(graph, child)

            elif edge_label == 'OC'\
                    and not (child.name == 'nt' and child['cat'] in ['VZ', 'CVZ']\
                            or child.name == 't' and child['pos'] == 'VVIZU'):
                oc = child
                # print 4
                mod_aux_helper(graph, child, subj)

            # rest just call helper
            else:
                mod_aux_helper(graph, child)

        # print '\t',phrase(graph, subj), ',',  phrase(graph, mod) + phrase(graph, aux) ,',',phrase(graph, oc)
        # do job
        if not label:
            if oc:
                # print phrase(graph, subj), ',',  phrase(graph, mod) + phrase(graph, aux) ,',',phrase(graph, oc)
                # black magic here, can replace by call helper several times for each conj 
                if mod and oc.name == 'nt' and oc['cat'] == 'CVP':
                    # print 1
                    mark(graph, subj, oc, 'SBM')
                else:
                    if mod:
                        # print 2
                        mod_aux_helper(graph, oc, subj, 'm')
                    elif aux:
                        # print 3
                        mod_aux_helper(graph, oc, subj, 'a')

    # if it's an aux at the end of the head chain, then mark it, otherwise search deeper
    if aux_oc_wait:
        if hd or mod or not oc:
            mark(graph, subj, aux_oc_wait, 'SBA')
        elif aux:
            mod_aux_helper(graph, oc, subj, 'a')


# original mod_aux_helper

def mod_aux_helper0(graph, node, subj = None, label = ''):
    mod, aux, oc, hd = None, None, None, None

    if node.name == 'nt':
        children = child_nodes(graph, node)
        # print [c['id'] for c in children], '\n'
        new_subj = child_nodes(graph, node, ['SB'], ['SB'])
        if new_subj:
            subj = new_subj[0]
            label = ''

        # find mod, aux, oc
        for child in children:
            edge_label = get_label(graph, child)
            # mark mod or aux
            if edge_label == 'HD' and child.name == 't':
                if child['pos'] in ['VMINF', 'VMFIN', 'VMPP']:
                    mod = child
                elif child['pos'] in ['VAINF', 'VAFIN', 'VAPP']:
                    aux = child
                else:
                    hd = child
            elif edge_label == 'OC'\
                    and not (child.name == 'nt' and child['cat'] in ['VZ', 'CVZ']\
                            or child.name == 't' and child['pos'] == 'VVIZU'):
                oc = child
                # print phrase(graph, oc)
            # rest just call helper
            # else:
            mod_aux_helper(graph, child, subj)

        print '\t',phrase(graph, subj), ',',  phrase(graph, mod) + phrase(graph, aux) ,',',phrase(graph, oc)
        # do job
        if not label:
            if oc:
                print phrase(graph, subj), ',',  phrase(graph, mod) + phrase(graph, aux) ,',',phrase(graph, oc)
                # black magic here, can replace by call helper several times for each conj 
                if mod and oc.name == 'nt' and oc['cat'] == 'CVP':
                    print 1
                    mark(graph, subj, oc, 'SBM')
                else:
                    if mod:
                        print 2
                        mod_aux_helper(graph, oc, subj, 'm')
                    elif aux:
                        print 3
                        mod_aux_helper(graph, oc, subj, 'a')
        elif label == 'm':
            # print phrase(graph, subj)
            # print phrase(graph, oc)
            if aux:
                if oc:
                    mod_aux_helper(graph, oc, subj, 'm')
                else:
                    mark(graph, subj, aux, 'SBM')
            elif mod:
                # print phrase(graph, subj)
                # print phrase(graph, mod)
                mark(graph, subj, mod, 'SBM')
                if oc:
                    mod_aux_helper(graph, oc, subj, 'm')
            elif hd:
                mark(graph, subj, hd, 'SBM')
        elif label == 'a':
            if aux:
                if oc:
                    mod_aux_helper(graph, oc, subj, 'a')
                else:
                    mark(graph, subj, aux, 'SBA')
            elif mod:
                mark(graph, subj, mod, 'SBA')
                if oc:
                    mod_aux_helper(graph, oc, subj, 'm')
            elif hd:
                mark(graph, subj, hd, 'SBA')
        else:
            print 'what?'
    else:
        if label == 'm':
            mark(graph, subj, node, 'SBM')
        elif label == 'a':
            mark(graph, subj, node, 'SBA')





#####################################


#####################################
# step 2 and 3: add secedge to SBR and SBE
def ctrl_helper(graph, items, flag):
    global TOTAL, EXCEPTION, COLLECTION, STAT

    sid, ctrl_type, ctrl_indices, main_indices, comp_indices = items

    lfg_main_set = set_without_punctuation(graph, main_indices)
    lfg_ctrl_set = set_without_punctuation(graph, ctrl_indices)
    lfg_comp_set = set_without_punctuation(graph, comp_indices)


    comp, ctrl, main = None, None, None

    # first find comp, then ctrl
    comp = find_comps(graph, lfg_comp_set)
    # print comp
    if comp:
        comp_set = range_of_phrase(graph, comp)
        # parent = find_highst_node(graph, comp_set)
        main = find_main(graph, lfg_main_set)   

        main, comp = find_real_main_comp(graph, main, comp)

        if debug:
            print phrase(graph, main)
            # print phrase(graph, comp)

        main_parent_oc_sets = map(lambda x: range_of_phrase(graph, x), child_nodes(graph, parent_node(graph, main), ['OC', 'OP', 'MO', 'PD']))
        if not any(comp_set <= s for s in main_parent_oc_sets):
            print 'exception:', sid
            EXCEPTION += 1
            return

        if flag == '-r':
            seclabel, excl = 'SBR', 'EXCL'
            ctrl, num = find_subj(graph, comp, main)
        else:
            seclabel, excl = 'SBE', 'EXCLE'
            ctrl, num = find_ctrl(graph, lfg_ctrl_set, comp, main, ctrl_type)

        if ctrl:   
            TOTAL += 1
            ctrl_set = range_of_phrase(graph, ctrl)
            if not lfg_ctrl_set & ctrl_set:
                # FORTH += 1
                num = 4

            if not ctrl_set <= comp_set and not comp_set <= ctrl_set:
                mark(graph, ctrl, comp, seclabel)
            else:
                print 'exception:', sid
                EXCEPTION += 1
                # add into collection
            # if collect:
                # do sth


            if not any(a == b for a in range_of_phrase(graph, ctrl) for b in lfg_ctrl_set):
                if flag == '-r':
                    STAT['NOR'] += 1
                else:
                    STAT['NOE'] += 1

            if not any(a == b for a in range_of_phrase(graph, comp) for b in lfg_comp_set):
                STAT['NOC'] += 1

            if not any(a == b for a in range_of_phrase(graph, main) for b in lfg_main_set):
                STAT['NOM'] += 1


        else:
            # if not comp: 
            #     print '-----COMP Not Found-----\t',sid
            # else:
            print '-----CTRL Not Found-----\t',sid
    if not comp:
        print '-----COMP Not Found-----\t',sid 

#####################################



#####################################
# functions to find specific nodes 

def find_ctrl(graph, lfg_ctrl_set, comp, main, ctrl_type):
    obj = None
    real_main, real_comp = main, comp
    subj, num = find_subj(graph, comp, main)
    if main and comp:
        # top = parent_node(graph, main)
        # # locate the real comp as bottom for search of OA
        # if get_label(graph, comp) in ['OC', 'CJ', 'RE']:
        #     bottom = comp
        # elif get_label(graph, comp) in ['HD']:
        #     bottom = parent_node(graph, comp)
        #     real_comp = bottom
        # else:
        #     bottom = None
        #     print 'Warning: label of comp is %s' % get_label(graph, comp)
        # while bottom and top and not obj and top != bottom:
        #     tmp = child_node(graph, top, ['HD'])
        #     if tmp:
        #         real_main = tmp
        #     obj = child_node(graph, top, ['OA', 'DA'])
        #     top = child_node(graph, top, ['OC', 'PD'])
        #     # print 'top',top

        # print phrase(graph, real_main)
        # if find a object which is not a reflexive pronoun, then return it as the ctrl
        # if ctrl_type == 'o' and not obj:
        #     do sth

        obj = child_node(graph, parent_node(graph, main), ['OA', 'DA'])

        if obj and (obj.name == 'nt' or obj['pos'] != 'PRF'):
            write_results('o', graph, obj, real_main, real_comp)
            return obj, 4
        elif subj:
            write_results('s', graph, subj, real_main, real_comp)
            return subj, num
    return None, -1

def find_real_main_comp(graph, main, comp):
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
    global FIRST, SECOND, THIRD
    main_subj = None
    # zero
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
        ctrl = graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == edge_sb['idref'])
        FIRST += 1
        return ctrl, 1
    if secedge_sb:
        ctrl = secedge_sb.parent
        SECOND += 1
        return ctrl, 2
    if secedge_hd_sb:
        ctrl = secedge_hd_sb.parent
        THIRD += 1
        return ctrl, 3
    return None, 0


def find_obj(graph, ctrl_set, main):
    global FORTH
    # print words_of_phrase(graph, main)
    main_obj = None
    if main:
        p = parent_node(graph, main)
        # print main['word']
        while p and not main_obj:
            main_obj = child_node(graph, p, ['OA'])
            # secedge_sb = graph.find(lambda x: x.name == 'secedge' and x['label'] in ['OA'] and x['idref'] == p['id'])
            # if secedge_sb:
            #     main_obj = secedge_sb.parent
            p = child_node(graph, p, ['OC'])
    if main_obj:
        FORTH += 1
        return main_obj, 4



def find_comps(graph, comp_set):
    cands = []
    comp = None
    # coor_comps = []
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
        # if comp.name == 'nt' and comp['cat'] in ['CVP', 'CVZ']:
        #     coor_comps = child_nodes(graph, comp, ['CJ'])
        # else:
        #     coor_comps = [comp]

    return comp




def find_main(graph, main_set):
    m, ans = None, None
    # int(x['idref'].split('_')[1]
    # print main_set
    edge_cands = graph.find_all(lambda x: x.name == 'edge' and x['label'] == 'HD' and range_of_phrase(graph, x) <= main_set)
    if edge_cands:
        ed = edge_cands[0]
        ans = graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == ed['idref'])
        # print 1, ans
        if len(edge_cands) > 1:
            for e in edge_cands[1:]:
                # print e
                m = graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == e['idref'])
                if m and range_of_phrase(graph, m) <= main_set and m not in parent_node(graph, ans):
                    ans = m
                    # print 2, ans
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

def write_collection(collection_name):
    global COLLECTION
    # COLLECTION = COLLECTION.encode('utf-8')
    text = open('../TIGER/head.xml').read()
    text += '<body>\r\n'
    text += COLLECTION
    text += '</body>\r\n</corpus>\r\n'
    g = open(collection_name, 'w')
    g.write(text)
    g.close()

#####################################


#####################################
# playground


def ctrl_without_lfg(graph, node, subj = None, label = ''):
    global FIRST
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
                        if oc_of_oa['cat'] in ['VP', 'CVP', 'VZ', 'CVZ'] and not child_node(graph, oc_of_oa, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE']):
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
                        if oc_of_pd['cat'] in ['VP', 'CVP', 'VZ', 'CVZ'] and not child_node(graph, oc_of_pd, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE']):
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
                            if re_of_mo['cat'] in ['VP', 'CVP', 'VZ', 'CVZ'] and not child_node(graph, re_of_mo, ['SB'], ['SB', 'SBM', 'SBA', 'SBR', 'SBE'])\
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







# stats about control verbs
def ctrl_finder_helper(graph, node, subj = None):
    global MISSED, ALL
    oc, hd = None, None
    # print node['id'],
    if node.name == 'nt':
        children = child_nodes(graph, node)
        # print [c['id'] for c in children], '\n'
        new_subj = child_nodes(graph, node, ['SB'])
        if new_subj:
            subj = new_subj[0]
            # label = ''

        # find hd, oc
        for child in children:
            edge_label = get_label(graph, child)
            # mark mod or aux
            if edge_label == 'HD' and child.name == 't':
                if child['pos'] not in ['VMINF', 'VMFIN', 'VMPP', 'VAINF', 'VAFIN', 'VAPP']:
                    hd = child
            elif edge_label == 'OC' and not (child.name == 'nt' and child['cat'] in ['S', 'CS']):
                oc = child
            # rest just call helper
            else:
                ctrl_finder_helper(graph, child)

        if oc:
            ctrl_finder_helper(graph, oc, subj)

    if subj and hd and oc:
        # lemma of hd
        while hd.name != 't':
            hd = child_node(graph, hd, ['HD'])

        svp = child_node(graph, parent_node(graph, hd), ['SVP'])

        hd_lemma = hd['lemma'].encode('utf-8')
        if svp:
            hd_lemma = svp['lemma'].encode('utf-8') + hd_lemma
        # print hd_lemma

        if hd_lemma not in ALL:
            ALL[hd_lemma] = []
        ALL[hd_lemma].append(subj['id'].split('_')[0][1:])

        oa = child_node(graph, parent_node(graph, subj), ['OA', 'DA'])
        if not has_secedge(graph, subj, oc) and not (oa and has_secedge(graph, oa, oc)):
            print subj['id'].split('_')[0][1:], phrase(graph, subj), '-->', phrase(graph, hd), '-->', phrase(graph, oc)
            if hd_lemma not in MISSED:
                MISSED[hd_lemma] = []
            MISSED[hd_lemma].append(subj['id'].split('_')[0][1:])





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
    if debug == 0:
        walk('../TIGER/tiger5.0.xml','../TIGER/tiger8.3.3.xml', 'raising_indices.txt', 'equi_indices.txt')
    elif debug == 1:
        test('../TIGER/tiger5.0.xml',  'raising_indices.txt', 'equi_indices.txt', sid)
    elif debug == 2:
        walk('../TIGER/tiger7.5.5.xml','../TIGER/test.xml', 'raising_indices.txt', 'equi_indices.txt')
    elif debug == 3:
        test('../TIGER/tiger7.5.5.xml',  'raising_indices.txt', 'equi_indices.txt', sid)

        

