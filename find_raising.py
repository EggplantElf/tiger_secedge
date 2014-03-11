#!/usr/bin/python
import sys, os, re

debug = 0


variables = {}
words = []
results = {'XCOMP':[], 'XCOMP-PRED':[], 'raising': []}
pattern1 = re.compile(r'cf\(1,(?:eq|in_set)\(.+\)\)')
pattern2 = re.compile(r'((?:fspan|surfaceform)\(.+\))\)')


def walk(dir):
    wlist = {}
    g = open('found4.txt', 'w')
    h = open('found_list.txt', 'w')
    o = open('raising_word_list.txt', 'w')
    for root, dirs, files in os.walk(dir):
        for f in files:
            filename = os.path.join(root, f)
            # print filename    
            read_lfg(os.path.join(root, f))
            reslist = find_raising(filename)
            for res in reslist:
                (str_xcomp, str_main, str_controll, v, n, xcomp, name, a, c) = res
                g.write(name + '\n')
                g.write('%d, %d, %d\n' % (v, n, xcomp))
                s = open(filename).readlines()[2][12:-3]
                g.write(s + '\n')
                g.write(a + '\t' + c + '\n')
                g.write(str_main + '\n')
                g.write(str_controll + '\n')
                g.write(str_xcomp + '\n\n')
                h.write(filename + '\n')
                if a not in wlist:
                    wlist[a] = []
                wlist[a].append(filename)
            variables.clear()
            words = []
    for w in wlist:
        o.write('%s\t%d\n' % (w, len(wlist[w])))
    o.write('\n\n')
    for w in wlist:
        o.write('-'* 20 + '\n')
        o.write(w + '\n')
        for x in wlist[w]:
            o.write('\t' + x + '\n')

    g.close()
    h.close()
    o.close()
    # statistics(results)

def walk_no_write(dir):
    global words
    g = open('raisings_all_modal0.txt', 'w')
    for root, dirs, files in os.walk(dir):
        for f in files:
            filename = os.path.join(root, f)
            # print filename    
            read_lfg(filename)
            for (subj, controllee, main) in find_raising():
                # if subj and subj[1][-1] - subj[1][0] + 1 != len(subj[1]):
                #     print 'cee', f
                #     print subj
                # if controllee[1][-1] - controllee[1][0] + 1 != len(controllee[1]):
                #     print 'cer', f
                #     print controllee
                if controllee[1] and subj[1]:
                    print f[3:-3], subj[1][0], subj[1][-1], controllee[1][0], controllee[1][-1]
                    g.write('%s\t%d\t%d\t%d\t%d\n' % (f[3:-3], subj[1][0], subj[1][-1], controllee[1][0], controllee[1][-1]))
            variables.clear()
            words = []
    g.close()


    
def find_raising():
    found = []
    res = []
    for v in variables:
        if 'PRED' in variables[v] and '_nontheme_' in variables[v]['PRED'] and variables[v]['PRED']['_nontheme_']\
         and 'VTYPE' in variables[v] and variables[v]['VTYPE'] not in ['copular']:

            if 'XCOMP-PRED' in variables[v]:
                xcomp = variables[v]['XCOMP-PRED']
            elif 'XCOMP' in variables[v]:
                xcomp = variables[v]['XCOMP']
            else:
                xcomp = -1

            for n in variables[v]['PRED']['_nontheme_']:                
                if xcomp != -1 and 'PRED' in variables[xcomp] and (n in variables[xcomp]['PRED']['_arg_'] or n in variables[xcomp]['PRED']['_nontheme_'])\
                    and 'VTYPE' in variables[xcomp] and ('PRED' in variables[n] and \
                    ('PRON-TYPE' not in variables[n] or variables[n]['PRON-TYPE'] != 'null') or 'COORD' in variables[n]):
                    # print variables[xcomp]
                    # if 'SUBJ' in variables[xcomp] and variables[xcomp]['SUBJ'] == n:
                    #     role = 'SUBJ'
                    # elif 'OBJ' in variables[xcomp] and variables[xcomp]['OBJ'] == n:
                    #     role = 'OBJ'
                    # else:
                    #     role = '???'
                    if phrase_of_var(n) and phrase_of_var(xcomp):
                        res.append((phrase_of_var(n), phrase_of_var(xcomp), variables[v]['PRED']['_lemma_']))                        
                    # results['XCOMP'].append(filename)
                    # if variables[v]['VTYPE'] == 'raising':
                    #     results['raising'].append(filename)
                    # res.append((str(variables[xcomp]), str(variables[v]), str(variables[n]), v, n, xcomp, filename,\
                    #  variables[v]['PRED']['_lemma_'], variables[xcomp]['PRED']['_lemma_']))



            # debug
            # if not res and variables[v]['VTYPE'] == 'raising':
            #     results['raising'].append(filename)
            #     print 'oops!', variables[v]['PRED']['_lemma_'], filename
            #     print open(filename).readlines()[2][12:-3]
            #     print variables[v]
            #     if 'XCOMP' in variables[v]:
            #         xcomp = variables[v]['XCOMP']
            #         print variables[xcomp]
            #     if 'XCOMP-PRED' in variables[v]:
            #         xcomp = variables[v]['XCOMP-PRED']
            #         print variables[xcomp]
            #     nt = variables[v]['PRED']['_nontheme_'][0]
            #     print variables[nt]
            #     print
    return res

def phrase_of_var(v):
    lemmas = []
    indices = []
    i = 0
    if '_range_' not in variables[v]:
        return None
    (start, end) = variables[v]['_range_']
    for (l, s, e) in words:
        if s < e:
            i += 1
            if s >= start and e <= end:
                lemmas.append(l)
                indices.append(i)
    return (lemmas, indices)


def statistics(results):
    print '\n', '-' * 30
    print 'XCOMP:', len(results['XCOMP'])
    print 'XCOMP-PRED:', len(results['XCOMP-PRED'])
    print 'raising:', len(results['raising'])
    print 'XCOMP + raising:', len(set(results['XCOMP']) & set(results['raising']))
    print 'XCOMP-PRED + raising:', len(set(results['XCOMP-PRED']) & set(results['raising']))
    print 'raising only:', len(set(results['raising']) - set(results['XCOMP']) - set(results['XCOMP-PRED']))
    print 'XCOMP only:', len(set(results['XCOMP']) - set(results['raising']))
    print 'XCOMP-PRED only:', len(set(results['XCOMP-PRED']) - set(results['raising']))

# ------------------------------
# functions to read the lfg output file

def read_lfg(filename):
    global words
    raw = open(filename).read()

    functions = re.findall(pattern1, raw)
    for f in functions:
        exec(f)
    functions = re.findall(pattern2, raw)
    for f in functions:
        exec(f)

    if debug == 2:
        for v in variables:
            print v, variables[v]
    words = process_words(words)



def cf(a,b):
    if debug == 2:
        print b
    exec(b)

def eq(a,b):
    if a == '#ignore#':
        return ''
    elif type(b) == int:
        return '%s = %d' % (a, b)
    elif type(b) == str:
        if b[0] == '{':
            return '%s = %s' % (a, b)
        else:
            return "%s = '%s'" % (a, b)
    else:
        print '\tATTENTION! eq'
        # return a + '= \'' + b + '\''

def in_set(a, b):
    if type(b) == int:
        if '_set_' not in variables[b]:
            variables[b]['_set_'] = []
        if type(a) == int:
            return "variables[%d]['_set_'].append(%d)" % (b, a)
        elif type(a) == str:
            return "variables[%d]['_set_'].append('%s')" % (b, a)
    #  some rare case
    elif type(b) == str:
        return ''

    else:
        print '\t ATTENTION! inset'

def attr(var, at):
    return "variables[%d]['%s']" %(var, at)

def var(id):
    if id not in variables:
        variables[id] = {}
        # variables[id]['_id_'] = id
    return id
 
def semform(a,b,c,d):
    a = a.replace('\'', '\\\'')
    c = str(c).replace('\'','').replace('NULL', '\'NULL\'')
    d = str(d).replace('\'','').replace('NULL', '\'NULL\'')
    return "{'_lemma_':\'%s\', '_pid_': %d, '_arg_': %s, '_nontheme_': %s}" % (a, b, c, d)

def proj(a, b):
    return '#ignore#'

def scopes(a, b):
    return '#ignore#'



# see fs_10050.pl
def fspan(var,start,end):
    if '_range_' not in variables[var] or (end - start) > (variables[var]['_range_'][1] - variables[var]['_range_'][0]):
        variables[var]['_range_'] = (start, end)

def surfaceform(x, lemma, start, end):
    words.append((lemma, start, end))

def split_words(sent):
    words = []
    s = 0
    e = 0
    wlist = sent.split(' ')
    for w in wlist:
        s = e + 1
        e = s + len(w)
        words.append((w, s, e))
    return words

def process_words(words):
    words_new = []
    for (word, s, e) in words:
        if ' ' not in word:
            words_new.append((word, s, e))
        else:
            for w in word.split(' '):
                words_new.append((w, s, e))
    return words_new



if __name__ == '__main__':
    if debug:
        read_lfg('../XLE/fs_1562.pl')
        reslist = find_raising()
        # print words
        for res in reslist:
            # (str_xcomp, str_main, str_controll, v, n, xcomp, name, a, c) = res
            # print phrase_of_var(n)[0], phrase_of_var(xcomp)[0]
            for r in res:
                print r
    else:
        walk_no_write('../bestTrain')