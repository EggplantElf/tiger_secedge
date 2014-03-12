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

    g.write('</body>\r\n</corpus>\r\n')
    g.close()


if __name__ == '__main__':
    diff(sys.argv[1],sys.argv[2], sys.argv[3])