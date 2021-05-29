rectangle=[ (797, 173), (922, 89), (1099, 373), (974, 431)]

f=open('file.txt','w')
for ele in rectangle:
    print(ele)
    f.write(str(ele[0])+" ")
    f.write(str(ele[1])+" ")
f.write('\n')
f.close()

with open('file.txt') as f:
    array = []
    for line in f: # read rest of lines
        array.append([int(x) for x in line.split()])
        
print(array)