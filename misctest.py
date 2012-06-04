import subprocess, time
p=subprocess.Popen(['cat'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
for i in 'abcd':
    p.stdin.write(str.encode(i+'\n'))
    p.stdin.flush()
    output=p.stdout.readline()
    print(str(output, 'utf8'))
    time.sleep(1)
