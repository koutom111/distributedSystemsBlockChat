import os, sys

host = '127.0.0.1'
N = 4
ports = [5001, 5002, 5003, 5004, 5005]


for port in ports:
    command = f"gnome-terminal -- python3 Rest.py {port}"
    os.system(command)
