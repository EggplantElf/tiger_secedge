import sys

def evaluate(gold_file, pred_file):
    gold = [line.strip().split('\t') for line in open(gold_file)]
    pred = [int(line) for line in open(pred_file)]

    tp = len([i for i in range(len(gold)) if int(gold[i][0]) and pred[i]])
    ttp = len([i for i in range(len(gold)) if int(gold[i][0]) and pred[i] and int(gold[i][0]) == pred[i]])
    fp = len([i for i in range(len(gold)) if not int(gold[i][0]) and pred[i]])
    fn = len([i for i in range(len(gold)) if int(gold[i][0]) and not pred[i]])

    print 'tp', tp
    print 'ttp', ttp
    print 'fp', fp
    print 'fn', fn

    # pairs = zip(gold, pred)
    # for (g, p) in pairs:
    #     if int(g[0]) != p:
    #         print '\t'.join(g[1:]),'\t', p



if __name__ == '__main__':
    evaluate(sys.argv[1], sys.argv[2])
    
    


