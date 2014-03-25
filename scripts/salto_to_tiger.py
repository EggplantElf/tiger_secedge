import sys, re, bs4


def convert(salto_input, tiger_input, head_file,tiger_output):
    edge_from_frames = {}
    pattern = re.compile(r'<frame name=.{5,15} id=.{5,15}>.*?</frame>\r\n', re.DOTALL)
    frames = pattern.findall(open(salto_input).read())
    for frame in frames:
        frame = bs4.BeautifulSoup(frame, 'xml').frame
        label = frame['name']
        sb = frame.find(lambda x: x.name == 'fe' and x['name'] == 'SB').fenode['idref']
        oc = frame.find(lambda x: x.name == 'fe' and x['name'] == 'OC').fenode['idref']
        sid = sb.split('_')[0]
        if sid not in edge_from_frames:
            edge_from_frames[sid] = []
        edge_from_frames[sid].append((sb, oc, label))


    # print edge_from_frames

    print 'reading corpus...'
    origin_text = open(tiger_input).read()
    pattern = re.compile(r'<s id=.*?</s>\r\n', re.DOTALL)
    corpus = pattern.findall(origin_text)
    print 'done', len(corpus)

    g = open(tiger_output, 'w')
    g.write(open(head_file).read())
    g.write('<body>\r\n')

    i = 0
    for sent in corpus:
        s = bs4.BeautifulSoup(sent, 'xml').s
        if s['id'] in edge_from_frames:
            # print s['id']
            for (sb, oc, label) in edge_from_frames[s['id']]:
                subj = s.find(lambda x: x.name in ['t', 'nt'] and x['id'] == sb)
                verb = s.find(lambda x: x.name in ['t', 'nt'] and x['id'] == oc)
                mark_helper(s.graph, subj, verb, label) 
        g.write(s.prettify('utf-8', formatter = convert_entity) + '\r\n')


    g.write('</body>\r\n</corpus>\r\n')
    g.close()



def mark_helper(graph, subj, verb, label):
    if subj and not subj.find(lambda x: x.name == 'secedge' and x['idref'] == verb['id']):
        secedge = bs4.BeautifulSoup('<secedge label="%s" idref="%s" />' % (label, verb['id']), 'xml').secedge
        subj.append(secedge)
        subj.append('\r\n')


def convert_entity(s):
    return s.replace('&','&amp;').replace('<', '&lt;').replace('>', '&gt;')



if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])