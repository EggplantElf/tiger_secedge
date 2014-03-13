#!/usr/bin/python
import sys, os, re

debug = 0
varis = {}
words = []
pattern1 = re.compile(r'cf\(1,(?:eq|in_set)\(.+\)\)')
pattern2 = re.compile(r'((?:fspan|surfaceform)\(.+\))\)')
punctuations = ['``', '\'\'', ',', '.', '_,', ':', ';', '-', '(',')', '\'', '/', '?', '...', '!', '`']

def walk(flag, input_dir, output_dir):
    global words
    if flag == '-r':
        g = open(os.path.join(output_dir,'raising_words.txt'), 'w')
        h = open(os.path.join(output_dir,'raising_indices.txt'), 'w')
    else:
        g = open(os.path.join(output_dir,'equi_words.txt'), 'w')
        h = open(os.path.join(output_dir,'equi_indices.txt'), 'w')
    # i = 0
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            filename = os.path.join(root, f)
            # print filename    
            read_lfg(filename)
            if flag == '-r':
                ans = find_raising(filename)
            else:
                ans = find_equi(filename)

            for items in ans:
                if flag == '-r':
                    (ctrl, comp, main) = items
                    ctrl_type = 'r'
                else:
                    (ctrl_type, ctrl, comp, main) = items

                if ctrl[1] and comp[1]:
                    gline = '%s | %s | %s | %s | %s\n' % (f[3:-3], ctrl_type, ' '.join(ctrl[0]), ' '.join(main[0]), ' '.join(comp[0]))
                    hline = '%s | %s | %s | %s | %s\n' % \
                     (f[3:-3], ctrl_type, ' '.join(map(str,ctrl[1])), ' '.join(map(str,main[1])), ' '.join(map(str,comp[1])))
                    g.write(gline)
                    h.write(hline)
            varis.clear()
            words = []
    g.close()
    h.close()
    

def find_raising(filename):
    found = []
    res = []
    for v in varis:
        if 'PRED' in varis[v] and '_nontheme_' in varis[v]['PRED'] and varis[v]['PRED']['_nontheme_']\
         and 'VTYPE' in varis[v] and varis[v]['VTYPE'] not in ['copular', 'modal']:

            if 'XCOMP-PRED' in varis[v]:
                xcomp = varis[v]['XCOMP-PRED']
            elif 'XCOMP' in varis[v]:
                xcomp = varis[v]['XCOMP']
            else:
                xcomp = -1

            for n in varis[v]['PRED']['_nontheme_']:                
                if xcomp != -1 and 'PRED' in varis[xcomp] and (n in varis[xcomp]['PRED']['_arg_'] or n in varis[xcomp]['PRED']['_nontheme_'])\
                    and 'VTYPE' in varis[xcomp] and ('PRED' in varis[n] and \
                    ('PRON-TYPE' not in varis[n] or varis[n]['PRON-TYPE'] != 'null') or 'COORD' in varis[n]):
                    if phrase_of_var(n) and phrase_of_var(xcomp) and phrase_of_var(v):
                        ctrl_phrase = phrase_of_var(n)
                        xcomp_phrase = phrase_of_var(xcomp)
                        main_phrase = phrase_of_var(v)
                        # main_phrase = rest_of_phrase(phrase_of_var(v), ctrl_phrase, xcomp_phrase)
                        res.append((ctrl_phrase, xcomp_phrase, main_phrase))      
                        # print filename
                        # print 's\t', ' '.join(ctrl_phrase[0])
                        # print 'v\t', ' '.join(main_phrase[0])
                        # print 'c\t', ' '.join(xcomp_phrase[0])
                        # print                  
    return res

def find_equi(filename):
    # print filename
    found = []
    res = []
    if debug:
        for v in varis:
            print v, varis[v]

    for v in varis:
        subj, obj, vcomp = None, None, None
        coord_vcomp, coord_subj, coord_obj = [], [], []
        if 'PRED' in varis[v] and 'VTYPE' in varis[v] and 'VCOMP' in varis[v]:
            # find vcomp or coord of vcomp
            vcomp = varis[v]['VCOMP']
            if 'COORD' in varis[vcomp]:
                coord_vcomp = varis[vcomp]['_set_']              

            # find subj or coord of subj
            if 'SUBJ' in varis[v] and varis[v]['SUBJ'] in varis[v]['PRED']['_arg_']:
                subj = varis[v]['SUBJ']
                if not 'PRED' in varis[subj] or ('PRON-TYPE' in varis[subj] and varis[subj]['PRON-TYPE'] == 'null'):
                    subj = None
                if subj and 'COORD' in varis[subj]:
                    coord_subj = varis[subj]['_set_']

            # find obj or coord of obj
            if 'OBJ' in varis[v]:
                obj = varis[v]['OBJ']
                if not 'PRED' in varis[obj] or ('PRON-TYPE' in varis[obj] and varis[obj]['PRON-TYPE'] != 'null'):
                    obj = None
                if obj and 'COORD' in varis[obj]:
                    coord_obj = varis[obj]['_set_']

            # determine if the controller is subj or obj of main verb
            if obj and ((not coord_vcomp and 'SUBJ' in varis[vcomp] and varis[vcomp]['SUBJ'] == obj)\
             or any([('SUBJ' in varis[vc] and varis[vc]['SUBJ'] == obj) for vc in coord_vcomp])):
                ctrl_type = 'o'
                ctrl = obj
            elif subj:
                ctrl_type = 's'
                ctrl = subj
            else:
                ctrl_type = 'x'
                ctrl = None


            if ctrl and vcomp:
                if debug:
                    print ctrl_type
                    print v, varis[v]
                    print ctrl, varis[ctrl]
                    print vcomp, varis[vcomp]
                # print filename
                ctrl_phrase = phrase_of_var(ctrl)
                vcomp_phrase = phrase_of_var(vcomp)
                main_phrase = rest_of_phrase(phrase_of_var(v), ctrl_phrase, vcomp_phrase)
 
                res.append((ctrl_type, ctrl_phrase, vcomp_phrase, main_phrase))
    return res


def rest_of_phrase(phrase, *excl):
    dic = dict(zip(phrase[1], phrase[0]))
    # print dic
    for e in excl:
        # print e
        if e:
            for i in e[1]:
                if i in dic:
                    tmp = dic.pop(i)
    # print dic
    return dic.values(), dic.keys()


def phrase_of_var(v):
    phrase = []
    indices = []
    i = 0
    if '_range_' not in varis[v]:
        return None
    (start, end) = varis[v]['_range_']
    # print start, end
    for (w, s, e) in words:
        if s < e:
            i += 1
            if s >= start and e <= end and w not in punctuations:
                phrase.append(w)
                indices.append(i)
    # print phrase, indices
    return (phrase, indices)


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

    pattern = re.compile(r'(?<=\'markup_free_sentence\'\(\').*?\'\)')
    raw_sent = re.search(pattern, raw).group()[:-2]
    if debug:
        print raw_sent
    wlist = map(lambda x: x.lower().replace(r'\'\'', '\'\''), raw_sent.split(' '))
    words = process_words(words, wlist)


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
        if '_set_' not in varis[b]:
            varis[b]['_set_'] = []
        if type(a) == int:
            return "varis[%d]['_set_'].append(%d)" % (b, a)
        elif type(a) == str:
            return "varis[%d]['_set_'].append('%s')" % (b, a)
    #  some rare case
    elif type(b) == str:
        return ''

    else:
        print '\t ATTENTION! inset'

def attr(var, at):
    return "varis[%d]['%s']" %(var, at)

def var(id):
    if id not in varis:
        varis[id] = {}
        # varis[id]['_id_'] = id
    return id
 
def semform(a,b,c,d):
    a = a.replace('\'', '\\\'')
    c = str(c).replace('\'','').replace('NULL', '\'NULL\'')
    d = str(d).replace('\'','').replace('NULL', '\'NULL\'')
    return "{'_word_':\'%s\', '_pid_': %d, '_arg_': %s, '_nontheme_': %s}" % (a, b, c, d)

def proj(a, b):
    return '#ignore#'

def scopes(a, b):
    return '#ignore#'



def fspan(var,start,end):
    if '_range_' not in varis[var] or (end - start) > (varis[var]['_range_'][1] - varis[var]['_range_'][0]):
        varis[var]['_range_'] = (start, end)

def surfaceform(x, word, start, end):
    if end > start:
        words.append((word.lower(), start, end))


def process_words(words_old, wlist):
    if not words_old:
        return words_old

    words = []
    words_new = []
    for exp, a, b in words_old:
        for w in exp.split():
            words.append((w, a, b))

    j = 0
    for i in range(len(wlist)):
        # print wlist[i], words[j]
        if wlist[i] == words[j][0]:
            words_new.append(words[j])
            j += 1
        else:
            # print '',wlist[i], words[j][0], i, j, wlist[i+1], words[j][0]
            words_new.append((wlist[i], words[j][1], words[j][2]))
            if i + 1 < len(wlist) and wlist[i+1] not in words[j][0]:
                j += 1
    return words_new



if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] not in ['-r', '-e']:
        print 'i have a pancake on my head, your argument is invalid!'
        print 'arguments: [-r/-e] [LFG directory] [output_directory]'
        exit(0)
    else:
        walk(sys.argv[1], sys.argv[2], sys.argv[3])
   



