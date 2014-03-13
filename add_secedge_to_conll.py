import sys, re
from process_tiger import *

def add_secedge(conll_file, xml_file, output_file, flag):

    g = open(output_file, 'w')

    # print 'reading conll file...'
    conll_dic = {}
    xml_dic = {}
    origin_text = open(xml_file).read()
    pattern = re.compile(r'<s id=.*?</s>', re.DOTALL)
    sents = pattern.findall(origin_text)
    pattern = re.compile(r'(?<=<s id="s)\d+(?=">)')
    for s in sents:
        m = pattern.search(s)
        if m:
            sid = m.group()
            xml_dic[int(sid)] = s

    lines = ''
    for line in open(conll_file):
        if len(line) > 2:
            lines += line
        else:
            sid = int(lines.split('_')[0])
            conll_dic[sid] = lines
            lines = ''

    for i in conll_dic.keys():
        if i in xml_dic:
            g.write(process(xml_dic[i], conll_dic[i], flag))
        # else:
            #     g.write(conll_dic[i] + '\n')
            if i % 2000 == 0:
                print '.',

    g.close()
    print 'done'


def process(xml, conll_lines, flag):

    conll = {}
    output = {}
    for line in conll_lines.split('\n'):
        if len(line) > 2:
            node = {}
            items = line.strip().split()     
            output[len(output) + 1] = items[:15] + ['_']
            node['nid'] = int(items[0].split('_')[1])
            node['form'] = items[1]
            node['head'] = int(items[8])
            node['label'] = items[10]
            conll[len(conll) + 1] = node

    graph = bs4.BeautifulSoup(xml, 'xml', from_encoding="utf-8").graph
    secedges = find_secedges(graph)
    edge_dic = {}
    for (label, fr, to) in secedges:
        fr, to = head(conll, fr), head(conll, to)
        # print '%s\t%s --> %s' % (label, conll[fr]['form'], conll[to]['form'])
        if fr not in edge_dic:
            edge_dic[fr] = []
        edge_dic[fr].append((label, to))

    for k in edge_dic:
        edge_dic[k].sort(key = lambda x: x[1])


    if flag == '-g':
        for k in output.keys():
            if k in edge_dic:
                output[k][12] = '|'.join([str(to) for (label, to) in edge_dic[k]])
                output[k][14] = '|'.join([label for (label, to) in edge_dic[k]])
                output[k][13] = '|'.join([str(to) for (label, to) in edge_dic[k] if label not in ['SBM', 'SBA', 'SBR', 'SBE']])
                output[k][15] = '|'.join([label for (label, to) in edge_dic[k] if label not in ['SBM', 'SBA', 'SBR', 'SBE']])
                if not output[k][13]:
                    output[k][13] = '_'
                    output[k][15] = '_'
    else:
        for k in output.keys():
            if k in edge_dic:
                output[k][13] = '|'.join([str(to) for (label, to) in edge_dic[k]])
                output[k][15] = '|'.join([label for (label, to) in edge_dic[k]])


    output = '\n'.join(['\t'.join(output[k]) for k in output]) + '\n\n'
    return output


def find_secedges(graph):
    secedges = []
    for n in graph.terminals:
        if type(n) == bs4.element.Tag:
            es = n.find_all('secedge')
            for e in es:
                fr = range_of_phrase(graph, n)
                to = range_of_phrase(graph, graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == e['idref']))
                secedges.append((e['label'].encode('utf-8'), fr, to))


    for n in graph.nonterminals:
        if type(n) == bs4.element.Tag:
            es = n.find_all('secedge')
            for e in es:
                fr = range_of_phrase(graph, n)
                to = range_of_phrase(graph, graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == e['idref']))
                secedges.append((e['label'].encode('utf-8'), fr, to))
    return secedges


def head(conll, id_set):
    return min(id_set, key = lambda x: len(head_chain(conll, x)))

def head_chain(conll, i):
    chain = []
    while i != 0:
        chain.append(i)
        i = conll[i]['head']
    return chain




if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] in ['-g', '-p']:
        add_secedge(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[1])
    else:
        exit(0)


