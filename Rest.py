import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from multiprocessing import Value, Array, Process, Manager, Lock
from block import Block
from node import Node
from blockchain import Blockchain
from wallet import Wallet
from _thread import *
import threading
import transaction
import json
import sys, os
import time
import jsonpickle
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from copy import deepcopy
from Crypto.Signature import PKCS1_v1_5

PRINTCHAIN = False
# CLIENT = 1                                    # read transactions from noobcash client
CLIENT = 0  # read transactions from txt

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return 'Hello, World!'


if __name__ == '__main__':
    port = sys.argv[1]
    if len(sys.argv) > 1:
        print("Hello my port is:", port)
    else:
        print("No port was provided.")

    # from argparse import ArgumentParser
    # node = Node()
    #
    #baseurl = 'http://{}:{}/'.format("192.168.1.5", "5000")
    host = '127.0.0.1'
    # ContactBootstrapNode(baseurl, host, port)
    app.run(host=host, port=int(port), debug=True)