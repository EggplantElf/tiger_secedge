# -*- coding: iso-8859-1 -*-
import sys, re


def cut(input_file, head_file, output_file, start, end, reverse = False):
    o = open(output_file, 'w')
    o.write(open(head_file).read())
    o.write('<body>\r\n')
    orig_text = open(input_file).read()
    if not reverse:
        m = re.compile(r'<s id="s%d".*?(?=<s id="s%d")' % (start, end + 1), re.DOTALL).search(orig_text)
        if m:
            text = m.group(0)
            o.write(text)
    else:
        m1 = re.compile(r'<s id="s1">.*?(?=<s id="s%d">)' % (start), re.DOTALL).search(orig_text)
        if m1:
            o.write(m1.group(0))
        m2 = re.compile(r'<s id="s%d">.*?(?=</body>)' % (end + 1), re.DOTALL).search(orig_text)
        if m2:
            o.write(m2.group(0))
    o.write('</body>\r\n</corpus>\r\n')
    o.close()



if __name__ == '__main__':
    if len(sys.argv) == 6:
        cut(sys.argv[1], sys.argv[2], sys.argv[3],int(sys.argv[4]), int(sys.argv[5]))
    elif len(sys.argv) == 7 and sys.argv[1] in ['-r', '--reverse']:
        cut(sys.argv[2], sys.argv[3], sys.argv[4],int(sys.argv[5]), int(sys.argv[6]), True)
    else:
        print 'arguments: [-r/--reverse (optional)] [input_file] [xml_head_file] [output_file] [start_index (incl.)] [end_index (incl.)]'
        exit(0)



