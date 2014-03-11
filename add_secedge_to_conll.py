import sys, re
from process_tiger import *

def add_secedge(conll_file, xml_file, output_file, sid = None):

    g = open(output_file, 'w')
    if sid:
        m1 = re.compile(r'<s id="s%d".*?</s>' % sid, re.DOTALL).search(open(xml_file).read())
        m2 = re.compile(r'%d_1.*?\n\n' % sid, re.DOTALL).search(open(conll_file).read())
        if m1 and m2:
            print 'a'
            xml = m1.group()
            conll_lines = m2.group()
            conll = {}
            g.write(process(xml, conll_lines))





    else:        
        # read the files
        print 'reading xml file...'
        origin_text = open(xml_file).read()
        # print origin_text
        pattern = re.compile(r'<s id=.*?</s>', re.DOTALL)
        res = pattern.findall(origin_text)
        print len(res)
        xml_dic = dict(zip(range(1, len(res) + 1), res))
        print 'done'


        for i in xml_dic.keys()[:5]:
            print i, xml_dic[i]

        print 'reading conll file...'
        conll_dic = {}
        lines = ''
        for line in open(conll_file):
            if len(line) > 2:
                lines += line
            else:
                conll_dic[len(conll_dic) + 1] = lines
                lines = ''
        print 'done'

        for i in conll_dic.keys()[:5]:
            print i, conll_dic[i]




        for i in conll_dic.keys():
            g.write(process(xml_dic[i], conll_dic[i]))
            if i % 1000 == 0:
                print i

    g.close()


def process(xml, conll_lines):

    conll = {}
    output = {}
    for line in conll_lines.split('\n'):
        if len(line) > 2:
            node = {}
            items = line.strip().split()     
            output[len(output) + 1] = items
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


    for k in output.keys():
        if k in edge_dic:
            output[k][12] = '|'.join([str(to) for (label, to) in edge_dic[k]])
            output[k][14] = '|'.join([label for (label, to) in edge_dic[k]])
        else:
            output[k][14] = '_'
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
    add_secedge('evaluation/tiger10001-11000.orig.conll09', 'evaluation/tiger10001-11000.gold.xml', 'evaluation/tiger10001-11000.gold.conll09')



