lst1 = ["a","b"]
lst2 = [1,2]

dct = dict(zip(lst1,lst2))
dct1 = dict(zip(lst2,lst1))

merge_dicts = dct | dct1
print(merge_dicts)