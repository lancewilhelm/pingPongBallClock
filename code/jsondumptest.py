import json

test = 2

# open output file for writing
with open('listfile.txt', 'w') as filehandle:
    json.dump(test, filehandle)
