import sys


# need change


def evaluate(pred_file):
    gold_dic = {'SBM': [], 'SBA': [], 'SBR': [], 'SBE': [], 'SBC': []}
    pred_dic = {'SBM': [], 'SBA': [], 'SBR': [], 'SBE': [], 'SBC': []}
    gold_inv_dic = {}
    pred_inv_dic = {}

    for line in open(pred_file):
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
            if items[13] != '_':
                sid = int(items[0].split('_')[0])
                nid = int(items[0].split('_')[1])
                pairs = zip(items[13].split('|'), items[15].split('|'))
                for (vid, label) in pairs:
                    if label in pred_dic:
                        pred_dic[label].append((sid, nid, int(vid)))
                        pred_inv_dic[(sid, nid, int(vid))] = label


    # print 'Gold:'
    # for label in gold_dic:
    #     print label + ':\t', len(gold_dic[label])

    # print 'total:\t', sum([len(gold_dic[l])for l in gold_dic])


    # tp = sum([len([p for p in gold_dic[label] if p in pred_dic[label]]) for label in gold_dic])
    # fn = sum([len([p for p in gold_dic[label] if p not in pred_dic[label]]) for label in gold_dic])
    # fp = sum([len([p for p in pred_dic[label] if p not in gold_dic[label]]) for label in gold_dic])
    # precision = 1.0 * tp / (tp + fp)
    # recall = 1.0 * tp / (tp + fn)
    # f_score = 2.0 * tp / (2.0 * tp + fn + fp)

    # print 'precision:\t%.4f' % precision
    # print 'recall:\t\t%.4f' % recall
    # print 'f-score:\t%.4f' % f_score

    for label in gold_dic:
        tp = len([p for p in gold_dic[label] if p in pred_dic[label]])
        fn = len([p for p in gold_dic[label] if p not in pred_dic[label]])
        fp = len([p for p in pred_dic[label] if p not in gold_dic[label]])
        if tp:
            precision = 1.0 * tp / (tp + fp)
            recall = 1.0 * tp / (tp + fn)
            f_score = 2.0 * tp / (2.0 * tp + fn + fp)
            print '%s:\n  p: %.4f\tr: %.4f\tf: %.4f' % (label, precision, recall, f_score)


    # print '\nTrue positive:'
    # for label in gold_dic:
    #     print label, len([p for p in gold_dic[label] if p in pred_dic[label]])

    # print '\nFalse negative:'
    # for label in gold_dic:  
    #     print label, len([p for p in gold_dic[label] if p not in pred_dic[label]])

    # print '\nFalse positive:'
    # for label in pred_dic:  
    #     print label, len([p for p in pred_dic[label] if p not in gold_dic[label]])



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

    print len(details)
    for (index, glabel, plabel) in sorted(details, key = lambda x: int(x[0][0])):
        if glabel in ['SBE', 'SBR', 'SBC'] or plabel in ['SBE', 'SBR', 'SBC']:
            print '%s\t%s --> %s' % (index, glabel, plabel)



if __name__ == '__main__':
    evaluate(sys.argv[1])
