with open('format1.txt') as file:
    raw = [elem.strip() for elem in file.readlines()]
    print(len(raw))
    data = sorted(set(raw))
    print(len(data))
print(*data, sep='\n')