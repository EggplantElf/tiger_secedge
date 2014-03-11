import sys

def analysis(conll_file):

    for line in open(conll_file):
        if len(line) > 2:
            tmp = line.split()
            head = tmp[10]
            sec = tmp[12]

            if sec != '_':
                secheads = sec.split('|')
                if head in secheads:
                    print line
                if len(secheads) != len(set(secheads)):
                    print line




if __name__ == '__main__':
    analysis('../TIGER/test1.conll')
