#!/bin/python
import os

xml_info = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>

<corpus id="Release2_1-060824">

"""



def join(output_dir, head, output_filename):
    # text = xml_info
    text = open(head).read()
    text += '<body>\r\n'
    for i in range(4,5):
        filename = os.path.join(output_dir, '%d.xml' % i)
        part = ''.join(open(filename).readlines()[2:-1])
        text += part
    text += '</body>\r\n</corpus>\r\n'
    g = open(output_filename, 'w')
    g.write(text)
    g.close()
    print 'done'


if __name__ == '__main__':
    join('../TIGER/newparts/', '../TIGER/head.xml', '../TIGER/tiger10001.xml')