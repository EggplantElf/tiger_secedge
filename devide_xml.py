# -*- coding: iso-8859-1 -*-

xml_info = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\r\n'


def devide(filename, dir, sents_in_each_file = 1000):
    sents = {}
    in_body = False
    string = ''
    sid = 0
    for line in open(filename).readlines():
        if line.strip() == '<body>':
            in_body = True
            print 'body starts'
        elif line.strip() == '</body>':
            in_body = False
            print 'body ends'
        elif in_body:
            if line.strip()[:5] == '<s id':
                sid = int(line.strip()[8:-2])
                string = ''
            string += (line)
            if line.strip() == '</s>':
                sents[sid] = string
    
    for i in range(len(sents) / sents_in_each_file + 1):
        last = 0
        to_write = ''
        for j in range(sents_in_each_file):
            if i * sents_in_each_file + j + 1 in sents:
                last = i * sents_in_each_file + j + 1
                to_write += sents[last]

        g = open('%s%d.xml' % (dir, i), 'w')
        g.write(xml_info)
        g.write('<part range=%d-%d>\n' % (i * sents_in_each_file + 1, last))
        g.write(to_write)
        g.write('</part>')
        g.close()


if __name__ == '__main__':
    devide('../TIGER/tiger8.1.3.xml', '../TIGER/newparts/')