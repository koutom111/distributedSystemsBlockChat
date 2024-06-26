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
CLIENT = 1                                    # read transactions from blockchat client
#CLIENT = 0
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
    rejson = request.json
    # Deserialize the blockchain received from the server
    serialized_data = base64.b64decode(rejson)
    data = pickle.loads(serialized_data)
    if data is None:
        return "Error: Please supply a valid Ring", 400
    ring = list(data.values())
    for r in ring:
        r1 = r
        r1['public_key'] = makejsonSendableRSA(r1['public_key'])
        node.ring.append(r)
    # print(ring)
    #print("------------------------")
    #print(node.ring)
    UpdateState(node.ring)
    #node.stake(10)
    #print("&&&&&&&&&&&&&")
    #print(node.staking)
    #GIA NA TESTARW AN DOYLEVEI TO BROADCAST_TRANSACTION
    # pub_key = node.ring[0]['public_key']
    # transaction = node.create_transaction(node.wallet.public_key, node.wallet.private_key, pub_key,
    #                                       'payment', node.nonce, 500,
    #                                       'your first money')

    # while(not(node.balance == 1000)):
    #     pass
    start_new_thread(read_transaction, (node,))

    return "Ring Updated for node {}".format(node.id), 200


# @app.route('/ValidateTransaction', methods=['POST'])
# def ValidateTransaction():
#     if request is None:
#         return "Error: Please supply a valid Transaction", 400
#     data = request.json
#     if data is None:
#         return "Error: Please supply a valid Transaction", 400
#     print(f'Received  ValidateTransaction data: {data}')
#     return data
#     # trans = jsonpickle.decode(data["transaction"])
#     # valid = node.validate_transaction(trans)                        #to be fixed!!!
#     # if(valid):
#     #     node.add_transaction_to_block(transaction)                  #to be fixed!!!!!!!
#     #
#     #     return "Transaction Validated by Node {} !".format(node.id), 200
#     # else:
#     #     return "Error: Not valid!", 400



@app.route('/ValidateTransaction', methods=['POST'])
def ValidateTransaction():
    if request is None:
        return "Error: Please supply a valid Transaction", 400
    rejson = request.json
    # Deserialize transaction received from the server
    data = rejson["transaction"]
    serialized_data = base64.b64decode(data)
    trans = pickle.loads(serialized_data)
    if trans is None:
        return "Error: Please supply a valid Transaction", 400
    # den me enoxlei to receiver_address na einai json PROS TO PARON
    if isinstance(trans.sender_address, str):
        trans.sender_address = makejsonSendableRSA(trans.sender_address)
    if isinstance(trans.receiver_address, str):
        trans.receiver_address = makejsonSendableRSA(trans.receiver_address)
    print("BROADCASTED TRANSACTION!!!!!!!!!!!!!!")

    valid, message = node.validate_transaction(trans)
    if valid:

        node.temp_transactions.append(trans)

        node.all_lock.acquire()

        if node.wallet.public_key == trans.sender_address: #an eimai o sender
            if (type(trans.receiver_address) == type(0)):
                node.staking = trans.amount                 #an exw kanei egw stake
            else:
                node.balance -= trans.calculate_charge()        #an egw exw xrewsei kapoion
        elif not (type(trans.receiver_address) == type(0)):   #an den einai stake kai kapoios allos einai o sender
            for r in node.state:
                if r['public_key'] == trans.sender_address:         #vres poios einai o sender kai afairesai poso
                    r['balance'] -= trans.calculate_charge()
                    r['nonce'] = trans.nonce
        else:
            for r in node.state:                            #vres poios exei balei na kanei stake
                if r['public_key'] == trans.sender_address:
                  r['staking'] = trans.amount
                  r['nonce'] = trans.nonce

        if trans.transaction_type == 'coins':
            recipient = trans.receiver_address
            amount = float(trans.amount)
            # Update recipient balance
            if node.wallet.public_key == recipient:
                node.balance += amount
                print()
                print('-------------------------------------------------')
                print(f'I received message: {amount} from {trans.sender_address}')
                print('-------------------------------------------------')
            else:
                for r in node.state:
                    if r['public_key'] == recipient:
                        r['balance'] += amount

        node.all_lock.release()

        if trans.transaction_type == 'message':
            recipient = trans.receiver_address
            message = trans.message
            # Update recipient balance
            if node.wallet.public_key == recipient:
                print()
                print('-------------------------------------------------')
                print(f'I received message: {message} from {trans.sender_address}')
                print('-------------------------------------------------')

        if len(node.temp_transactions) == node.block_capacity:
            print("I will try to mint")
            minted, message = node.mint_block()
            print(f"Message from mint <{message}> ")
            if minted is not None:
                node.chain.add_block_to_chain(minted)
                print(f"\n------I added block to chain----------\n")
                print(f'Length of chain: {len(node.chain.chain)}')
                node.temp_transactions = []
                node.add_my_fees(minted)
                for r in node.ring:
                    start_new_thread(node.broadcast_block, (minted, r,))

            node.current_block = node.create_new_block(node.current_block.index + 1,
                                                       node.current_block.compute_current_hash, time.time(),
                                                       node.current_block.capacity, None)
            print("Transaction Validated and New Block Created by Node {} !".format(node.id))
            return "Transaction Validated and New Block Created by Node {} !".format(node.id), 200
        print("Transaction Validated")
        return "Transaction Validated by Node {} !".format(node.id), 200
    else:
        print("Invalid Transaction")
        return "Error: Not valid!", 400

@app.route('/AddBlock', methods=['POST'])
def AddBlock():
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ADD BLOCK!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    if request is None:
        return "Error: Please supply a valid Block", 400
    rejson = request.json
    # Deserialize transaction received from the server
    data = rejson["block"]
    serialized_data = base64.b64decode(data)
    block = pickle.loads(serialized_data)
    if block is None:
        return "Error: Please supply a valid Block", 400

    block.revert_transactions()
    if isinstance(block.validator, str):
        block.validator = makejsonSendableRSA(block.validator)
    if(block.index > 0):
        valid = node.validate_block(block)

        if(valid):
            node.update_recipient_balances(block)
            node.traceback_transaction()
            node.chain.add_block_to_chain(block)
        else:
            print('\nI did NOT validate the block\n')
            return "Error: Invalid Block", 400
    print()
    print('I validate and added the block')
    return "OK", 200

@app.route('/AddGenesisBlock', methods=['POST'])
def AddGenesisBlock():
    if request is None:
        return "Error: Please supply a valid Block", 400
    rejson = request.json
    # Deserialize transaction received from the server
    data = rejson["block"]
    serialized_data = base64.b64decode(data)
    block = pickle.loads(serialized_data)
    if block is None:
        return "Error: Please supply a valid Block", 400

    block.revert_transactions()
    node.chain.add_block_to_chain(block)

    return "OK", 200
def UpdateState(ring):
    for r in ring:
        node.state.append({
            'id': r['id'],
            'public_key': r['public_key'],
            'balance': float(r['balance']),
            'staking': 0,
            'nonce': 0
        })
    # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    # print(node.state)
    return node.state
def ContactBootstrapNode(baseurl, host, port):
    public_key = node.wallet.public_key
    load = {'public_key': makeRSAjsonSendable(public_key), 'ip': node.myip, 'port': node.myport}
    # print('\n load pub key\n')
    # print(load['public_key'])
    r = requests.post(baseurl + "nodes/register", json=load)
    if (not r.status_code == 200):
        exit(1)
    rejson = r.json()

    # Deserialize the blockchain received from the server
    serialized_blockchain_b64 = rejson['blockchain']
    serialized_blockchain = base64.b64decode(serialized_blockchain_b64)
    blockchain = pickle.loads(serialized_blockchain)

    if node.validate_chain(blockchain):
        print("Blockchain is valid.")
    else:
        print("Blockchain is invalid.")
    node.id = rejson['id']
    node.chain = blockchain
    node.block_capacity = rejson['block_capacity']
    rejson['start_ring']['public_key'] = makejsonSendableRSA(rejson['start_ring']['public_key'])
    node.ring.append(rejson['start_ring'])

    serialized_current_block_b64 = rejson['current_block']
    serialized_current_block = base64.b64decode(serialized_current_block_b64)
    current_block = pickle.loads(serialized_current_block)

    node.current_block = current_block
    node.balance = rejson['balance']
    node.balance = float(node.balance)

    # blockchain_dict = []
    # for block in blockchain.chain:
    #     blockchain_dict.append(block.to_dict())
    #
    # # Replace 'blockchain' field with the deserialized blockchain data
    # rejson['blockchain'] = blockchain_dict
    # print('\nBlockchain after to_dict\n')
    # print(rejson['blockchain'])

    bootstrap_public_key = makejsonSendableRSA(rejson["bootstrap_public_key"])  # ti to 8eloyme????

    # print(bootstrap_public_key)  # ektypwnei address epeidh einai RSA
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
        node.myport = port
    else:
        print("No port was provided.")
    #
    baseurl = 'http://{}:{}/'.format("127.0.0.1", "5000")
    host = '127.0.0.1'
    node.myip = host
    ContactBootstrapNode(baseurl, host, port)
    app.run(host=host, port=int(port), debug=False, use_reloader=False)
