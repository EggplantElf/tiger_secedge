import sys

def evaluate(gold_file, pred_file):
    gold_dic = {'SBM': [], 'SBA': [], 'SBR': [], 'SBE': []}
    pred_dic = {'SBM': [], 'SBA': [], 'SBR': [], 'SBE': []}
    gold_inv_dic = {}
    pred_inv_dic = {}

    for line in open(gold_file):
        if line.strip():
            items = line.strip().split('\t')
            if items[12] != '_':
                sid = int(items[0].split('_')[0])
                nid = int(items[0].split('_')[1])
                pairs = zip(items[12].split('|'), items[14].split('|'))
                for (vid, label) in pairs:
                    if label in gold_dic:
                        gold_dic[label].append((sid, nid, int(vid)))
                        gold_inv_dic[(sid, nid, int(vid))] = label


    for line in open(pred_file):
        if line.strip():
            items = line.strip().split('\t')
            if items[12] != '_':
                sid = int(items[0].split('_')[0])
                nid = int(items[0].split('_')[1])
                pairs = zip(items[12].split('|'), items[14].split('|'))
                for (vid, label) in pairs:
                    if label in pred_dic:
                        pred_dic[label].append((sid, nid, int(vid)))
                        pred_inv_dic[(sid, nid, int(vid))] = label


    print 'Gold:'
    for label in gold_dic:
        print label + ':\t', len(gold_dic[label])

    print 'total:\t', sum([len(gold_dic[l])for l in gold_dic])

    print '\nFalse negative:'
    for label in gold_dic:  
        print label, [p for p in gold_dic[label] if p not in pred_dic[label]]

    print '\nFalse positive:'
    for label in pred_dic:  
        print label, [p for p in pred_dic[label] if p not in gold_dic[label]]



    print '\nDetails:'
    details = set()
    for key in gold_inv_dic:
        glabel = gold_inv_dic[key]
        if key not in pred_inv_dic:
            plabel = 'XXX'
        else:
            plabel = pred_inv_dic[key]
        if glabel != plabel:
            details.add((key, glabel, plabel))

    for key in pred_inv_dic:
        plabel = pred_inv_dic[key]
        if key not in gold_inv_dic:
            glabel = 'XXX'
        else:
            glabel = gold_inv_dic[key]
        if glabel != plabel:
            details.add((key, glabel, plabel))

    for (index, glabel, plabel) in sorted(details, key = lambda x: int(x[0][0])):
        print '%s\t%s --> %s' % (index, glabel, plabel)



if __name__ == '__main__':
    evaluate(sys.argv[1], sys.argv[2])
