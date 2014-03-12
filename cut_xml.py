# -*- coding: iso-8859-1 -*-
import sys, re


def cut(input_file, head_file, output_file, start, end):
    o = open(output_file, 'w')
    o.write(open(head_file).read())
    o.write('<body>\r\n')
    m = re.compile(r'<s id="s%d".*?(?=<s id="s%d")' % (start, end + 1), re.DOTALL).search(open(input_file).read())
    if m:
        text = m.group(0)
        o.write(text)
    o.write('</body>\r\n</corpus>\r\n')
    o.close()



if __name__ == '__main__':
    if len(sys.argv) == 6:
        cut(sys.argv[1], sys.argv[2], sys.argv[3],int(sys.argv[4]), int(sys.argv[5]))
    else:
        print 'arguments: [input_file] [xml_head_file] [output_file] [start_index] [end_index] (both inclusive)'
        exit(0)



