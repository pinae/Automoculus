#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

hostname_files = ["/home/jonny/Ubuntu One/hostnames 4.Stock Raum 1",
                  "/home/jonny/Ubuntu One/hostnames 5.Stock Raum 1",
                  "/home/jonny/Ubuntu One/hostnames 5.Stock Raum 2",
                  "/home/jonny/Ubuntu One/hostnames 5.Stock Raum 3",
                  "/home/jonny/Ubuntu One/hostnames 5.Stock Raum 4"]
hosts = []
for filename in hostname_files:
    h_file = open(filename, 'r')
    for line in h_file.readlines():
        if len(line) > 3:
            hosts.append(line.rstrip("\n"))
    h_file.close()
print(str(len(hosts))+" Rechner werden angepingt...")
running_machines = []
for host in hosts:
    response = os.system("ping -q -i 0.2 -w 1 -c 1 "+host)
    if response == 0:
        running_machines.append(host)
print("Folgende Rechner sind angeschaltet:")
for machine in running_machines:
    print("\t"+machine)