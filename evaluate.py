import bs4, re, sys


def evaluate(mode, gold_file, pred_file):
    result = {  'SBM':{'tp': 0, 'fp': 0, 'fn': 0}, 
                'SBA':{'tp': 0, 'fp': 0, 'fn': 0}, 
                'SBR':{'tp': 0, 'fp': 0, 'fn': 0}, 
                'SBE':{'tp': 0, 'fp': 0, 'fn': 0}}
    gold_dic = {'SBM': [], 'SBA': [], 'SBR': [], 'SBE': []}
    pred_dic = {'SBM': [], 'SBA': [], 'SBR': [], 'SBE': []}


    if mode not in ['-tt', '-st', '-ss']:
        print 'please select the format of gold and pred file'
        print 'mode:\t -tt : TIGER vs TIGER\n\t -st : SALTO vs TIGER \n\t -ss : SALTO vs SALTO'
        exit(0)

    if mode[1] == 't':
        gold_dic = read_tiger(gold_file)
    else:
        gold_dic = read_salto(gold_file)

    if mode[2] == 't':
        pred_dic = read_tiger(pred_file)
    else:
        pred_dic = read_salto(pred_file)


    print 'label\ttp\tfp\tfn'
    for label in gold_dic:
        for pair in gold_dic[label]:
            if pair in pred_dic[label]:
                result[label]['tp'] += 1
            else:
                result[label]['fn'] += 1
        for pair in pred_dic[label]:
            if pair not in gold_dic[label]:
                result[label]['fp'] += 1

        print '%s\t%d\t%d\t%d' % (label, result[label]['tp'], result[label]['fp'], result[label]['fn'])

    origin_text = open(pred_file).read()

    for label in gold_dic:
        for pair in gold_dic[label]:
            if pair not in pred_dic[label]:
                sid = pair[0].split('_')[0]
                pattern = re.compile(r'<s id="%s".*?</s>\r\n' % sid, re.DOTALL)
                m = pattern.search(origin_text)
                if m:
                    sent = m.group()
                    graph = bs4.BeautifulSoup(sent, 'xml').graph
                    sb = phrase(graph, graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == pair[0]))
                    oc = phrase(graph, graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == pair[1]))

                    print label, '\t', sid ,'\tFN\t', sb, '\t', oc

        for pair in pred_dic[label]:
            if pair not in gold_dic[label]:
                sid = pair[0].split('_')[0]
                pattern = re.compile(r'<s id="%s".*?</s>\r\n' % sid, re.DOTALL)
                m = pattern.search(origin_text)
                if m:
                    sent = m.group()
                    graph = bs4.BeautifulSoup(sent, 'xml').graph
                    sb = phrase(graph, graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == pair[0]))
                    oc = phrase(graph, graph.find(lambda x: x.name in ['t', 'nt'] and x['id'] == pair[1]))

                    print label, '\t', sid, '\tFP\t', sb, '\t', oc








def read_salto(salto_file):
    dic = {'SBM': [], 'SBA': [], 'SBR': [], 'SBE': []}
    pattern = re.compile(r'<frame name=.{5,15} id=.{5,15}>.*?</frame>\r\n', re.DOTALL)
    frames = pattern.findall(open(salto_file).read())
    for frame in frames:
        frame = bs4.BeautifulSoup(frame, 'xml').frame
        label = frame['name']
        sb = frame.find(lambda x: x.name == 'fe' and x['name'] == 'SB').fenode['idref']
        oc = frame.find(lambda x: x.name == 'fe' and x['name'] == 'OC').fenode['idref']
        dic[label].append((sb, oc))
    # for k in dic.keys():
    #     print k, dic[k]
    return dic

def read_tiger(tiger_file):
    dic = {'SBM': [], 'SBA': [], 'SBR': [], 'SBE': []}
    pattern = re.compile(r'<s id=.*?</s>\r\n', re.DOTALL)
    sents = pattern.findall(open(tiger_file).read())
    for sent in sents:
        graph = bs4.BeautifulSoup(sent, 'xml').s.graph
        for t in graph.terminals:
            if type(t) == bs4.element.Tag:
                for secedge in t.find_all(lambda x: x.name == 'secedge' and x['label'] in ['SBM', 'SBA', 'SBR', 'SBE']):
                    sb, oc, label = t['id'], secedge['idref'], secedge['label']
                    dic[label].append((sb, oc))

        for nt in graph.nonterminals:
            if type(nt) == bs4.element.Tag:
                for secedge in nt.find_all(lambda x: x.name == 'secedge' and x['label'] in ['SBM', 'SBA', 'SBR', 'SBE']):
                    sb, oc, label =  nt['id'], secedge['idref'], secedge['label']
                    dic[label].append((sb, oc))
    # print '-'* 20
    # for k in dic.keys():
    #     print k, dic[k]        
    return dic

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




if __name__ == '__main__':
    evaluate('-tt','test/tiger10001-15000.gold.xml', 'test/tiger10001-15000.pred.xml')

