import sys

def read(filename):
    dic = {}
    sid = 0
    for line in open(filename):
        if line.strip():
            items = line.strip().split('\t')
            if items[13] != '_':
                sid = int(items[0].split('_')[0])
                nid = items[0].split('_')[1]
                pairs = zip([nid] * len(items[13].split('|')),  items[13].split('|'), items[15].split('|'))
                for pair in pairs:
                    if pair[1] not in dic:
                        dic[pair[1]] = []
                    dic[pair[1]].append((pair[0], pair[2]))

        else:
            check(dic, sid)
            dic = {}

def check(dic, sid):
    for key in dic:
        if len(dic[key]) > 1:
            print dic[key], key ,sid



if __name__ == '__main__':
    read(sys.argv[1])
