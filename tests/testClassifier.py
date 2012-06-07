import subprocess
from os import path
import sys
sys.path.append("..")

from Config import PROJECT_PATH

def readLine(filehandle):
    #byteline = []
    #while True:
    #    byte = filehandle.read(1)
    #    print(byte)
    #    if byte == bytes('\n', 'UTF-8'):
    #        break
    #    byteline.append(byte)
    #return str(byteline, encoding='utf8')
    return filehandle.read().rstrip()

beatscriptFile = PROJECT_PATH + '/beatscripts/The Mighty Hugo - Testszene.csv'
classifier_process_filename = path.join(PROJECT_PATH, "ClassificationProcess.py")
prozess = subprocess.Popen(
    [classifier_process_filename,
     beatscriptFile], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
while True:
#for i in range(0,10):
    input = prozess.stdout.readline().rstrip()
    print(str(input, 'utf8'))
    if str(input, 'utf8') == "Training finished.":
        break
#diststr = str(prozess.stdout.readline().rstrip(), encoding='utf8')
dist = []
#for valstr in diststr.split('\t'):
#    dist.append(float(valstr))
print(dist)
prozess.stdin.write(bytes("c\n", 'utf-8'))
prozess.stdin.flush()
print(str(prozess.stdout.readline(), 'utf-8'))
prozess.stdin.write(bytes("d\n", 'utf-8'))
prozess.stdin.flush()
prozess.stdin.write(bytes("2\n", 'utf-8'))
prozess.stdin.flush()
print(str(prozess.stdout.readline(), 'utf-8'))
prozess.stdin.write(bytes("p\n", 'utf-8'))
prozess.stdin.flush()
print(str(prozess.stdout.readline(), 'utf-8'))
prozess.stdin.write(bytes("t\n", 'utf-8'))
prozess.stdin.flush()
print(str(prozess.stdout.readline(), 'utf-8'))
for frame in range(1, 200):
    prozess.stdin.write(bytes("f\n", 'utf-8'))
    prozess.stdin.flush()
    prozess.stdin.write(bytes(str(frame) + "\n", 'utf-8'))
    prozess.stdin.flush()
    newBlockStr = str(prozess.stdout.readline().rstrip(), 'utf-8')
    prozess.stdin.write(bytes("t\n", 'utf-8'))
    prozess.stdin.flush()
    print("Frame no. " + str(frame) + " neuer Block: " + newBlockStr + "\tTargets: " + str(prozess.stdout.readline(),
                                                                                           'utf-8').rstrip())
    if newBlockStr == "yes":
        prozess.stdin.write(bytes("p\n", 'utf-8'))
        prozess.stdin.flush()
        print(str(prozess.stdout.readline(), 'utf-8').rstrip())
        prozess.stdin.write(bytes("c\n", 'utf-8'))
        prozess.stdin.flush()
        print(str(prozess.stdout.readline(), 'utf-8').rstrip())
prozess.stdin.write(bytes("q\n", 'utf-8'))
prozess.stdin.flush()
print(str(prozess.stdout.readline(), 'utf-8'))
