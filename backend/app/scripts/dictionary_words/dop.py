with open('dop1.txt') as file:
    data1 = sorted(set([[el for el in elem.strip().split() if el.find('(') == -1][0] for elem in file.readlines() if elem.strip() and elem.find('.') == -1]), key=lambda x: x.lower())

with open('dop.txt') as f:
    data_compare = [elem.strip().lower() for elem in f.readlines()]
    data_dop = data_compare.copy()
    
def write_words(data, data_compare):
    print(len(data_compare))
    written = []
    for elem in data:
        if elem.lower() in data_compare:
            data_compare.pop(data_compare.index(elem.lower()))
            written.append(elem)
    print(len(written), len(data_compare))
    return written, data_compare
written1, data_compare = write_words(data1, data_compare)
#533

with open('dop2.txt') as file:
    data2 = [elem.strip() for elem in file.readlines() if elem.strip()]
    
def make_word(a: str, b: str):
    for i, elem in enumerate(a):
        if elem == '_':
            b = b[:i:] + b[i].upper() + b[i + 1::]
    return b

dop_2_to_write = []
dop2_used = []
for i in range(0, len(data2) - 1, 2):
    if data2[i] in dop2_used:
        continue
    else:
        dop2_used.append(data2[i])
        dop_2_to_write.append(make_word(data2[i], data2[i + 1]))

written2, data_compare = write_words(dop_2_to_write, data_compare)
#5
print(data_compare)
data_compare_last = ['аквАмАрин', 'бЕречь', 'кАсатка (птица)', 'кОмпания (группа людей)', 'кОсатка (млекопитающее)', 'лАдья', 'сумЕрки', 'угОстить', 'уЯзвить', 'фИгурист(ка)', 'эстАкада']
res = written1 + written2 + data_compare_last
with open('written.txt', 'w') as file:
    file.writelines([elem + '\n' for elem in sorted(set(res), key=lambda x: x.lower())])
print(set(data_dop) - set([elem.lower() for elem in res]))
    





 
    