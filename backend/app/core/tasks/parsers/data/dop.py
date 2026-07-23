with open('11.txt') as file:
    data = file.readlines()
for i in range(len(data) - 1):
    ind = data[i].find('_')
    letter = data[i + 1][ind].capitalize()
    data[i] = data[i][:ind] + letter + data[i][ind + 1:]
print(*data[::2])