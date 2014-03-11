import sys, re, bs4


def diff(file1, file2, output_file):
    text1 = open(file1).read()
    text2 = open(file2).read()
    pattern = re.compile(r'<s id=.*?</s>\r\n', re.DOTALL)
    corpus1 = pattern.findall(text1)
    corpus2 = pattern.findall(text2)

    g = open(output_file, 'w')
    g.write(open('../TIGER/head.xml').read())
    g.write('<body>\r\n')

    count = 0

    for i in range(len(corpus1)):
        if corpus1[i] != corpus2[i]:
            count += 1
            print count
            g.write(corpus1[i])
            g.write(corpus2[i])



            # sent1 = bs4.BeautifulSoup(corpus1[i], 'xml')
            # sent2 = bs4.BeautifulSoup(corpus2[i], 'xml')
            # t1, t2, nt1, nt2 = [], [], [], []
            # for t in sent1.graph.terminals:
            #     if type(t) == bs4.element.Tag:
            #         t1.append(t)
            # for t in sent2.graph.terminals:
            #     if type(t) == bs4.element.Tag:
            #         t2.append(t)            
            # for nt in sent1.graph.nonterminals:
            #     if type(nt) == bs4.element.Tag:
            #         nt1.append(nt)
            # for nt in sent2.graph.nonterminals:
            #     if type(nt) == bs4.element.Tag:
            #         nt2.append(nt) 

            # for x in range(len(t1)):
            #     if t1[x] = t2[x]




    g.write('</body>\r\n</corpus>\r\n')
    g.close()


if __name__ == '__main__':
    diff(sys.argv[1],sys.argv[2], sys.argv[3])