import base64
import pickle

import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from multiprocessing import Value, Array, Process, Manager, Lock

from BootstrapRest import read_transaction
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


def makeRSAjsonSendable(rsa):
    return rsa.exportKey("PEM").decode('ascii')


def makejsonSendableRSA(jsonSendable):
    return RSA.importKey(jsonSendable.encode('ascii'))


@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/Live', methods=['GET'])
def Live():
    return "I am alive!", 200
@app.route('/UpdateRing', methods=['POST'])
def UpdateRing():
    if request is None:
        return "Error: Please supply a valid Ring", 400
    data = request.json
    print("-----------------------")
    print(data)
    print("-----------------------")
    if data is None:
        return "Error: Please supply a valid Ring", 400
    ring = list(data.values())
    r1 = None
    for r in ring:
        r1 = r
        r1['public_key'] = makejsonSendableRSA(r1['public_key'])
    # while(not(node.current_BCCs[-1][0] == 100 or node.BCCs[-1][0] == 100)):
    #     pass
    # start_new_thread(read_transaction, ())

    print(ring)
    return "Ring Updated for node {}".format(node.id), 200

def ContactBootstrapNode(baseurl, host, port):
    public_key = node.wallet.public_key
    load = {'public_key': makeRSAjsonSendable(public_key), 'ip': host, 'port': port}
    r = requests.post(baseurl + "nodes/register", json=load)
    if (not r.status_code == 200):
        exit(1)
    rejson = r.json()
    # Deserialize the blockchain received from the server
    serialized_blockchain_b64 = rejson['blockchain']
    serialized_blockchain = base64.b64decode(serialized_blockchain_b64)
    blockchain = pickle.loads(serialized_blockchain)

    blockchain_dict = []
    for block in blockchain.chain:
        blockchain_dict.append(block.to_dict())

    # Replace 'blockchain' field with the deserialized blockchain data
    rejson['blockchain'] = blockchain_dict
    print(rejson)
    bootstrap_public_key = makejsonSendableRSA(rejson["bootstrap_public_key"])
    print(bootstrap_public_key)  # ektypwnei address epeidh einai RSA
    # an theloume na ektypwsoyme to kleidi:
    # kleidi = makeRSAjsonSendable(bootstrap_public_key)
    # print(kleidi)
    print("Successfully registered")


if __name__ == '__main__':
    from argparse import ArgumentParser

    node = Node()  # sthn arxi ola ta pedia toy node einai None h adia ektos apo to WALLET

    port = sys.argv[1]
    if len(sys.argv) > 1:
        print("Hello my port is:", port)
    else:
        print("No port was provided.")

    #
    baseurl = 'http://{}:{}/'.format("127.0.0.1", "5000")
    host = '127.0.0.1'
    ContactBootstrapNode(baseurl, host, port)
    app.run(host=host, port=int(port), debug=False, use_reloader=False)
