import hashlib

file1 = "truc.txt"
file2 = "trux.txt"

print(hashlib.md5sum(open(file1).read().encode()).digest()) # format octal (non convertible en str)
print(hashlib.md5sum(open(file1).read().encode()).hexdigest()) # format hexa

print(hashlib.md5sum(open(file2).read().encode()).digest()) # format octal (non convertible en str)
print(hashlib.md5sum(open(file2).read().encode()).hexdigest()) # format hexa
