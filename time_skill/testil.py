import pymorphy2

morph = pymorphy2.MorphAnalyzer()

saved_version = "вырвать траву в грядки"
check_version = "вырвать траву в d 2 грядке"

s = [morph.parse(x)[0].normal_form for x in saved_version.split()]
c = [morph.parse(x)[0].normal_form for x in check_version.split()]

print(s, c, sep='\n')

if all(word in c for word in s):
    print(1)
