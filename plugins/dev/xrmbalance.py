#!/usr/bin/python3

import os
import sys
import collections
import json
import pickle
import json
from flask import Flask, request, Response
from jsonrpcserver import methods
from blockchain_parser.blockchain import Blockchain
from blockchain_parser.script import *

chain_const = {"BTC":{"pch": b"\xf9\xbe\xb4\xd9", "vb":[b'\x00', b'\x05']},
         "BLOCK":{"pch": b"\xa1\xa0\xa2\xa3", "vb":[b'\x1a', b'\x1c']},
         "BLOCKTEST":{"pch": b"\x45\x76\x65\xba", "vb":[b'\x8b', b'\x13']}
         }


class BalancePlugin:
    def __init__(self, chain, chainpath):
        self.chain = chain
        self.chainpath = chainpath
        try:
            f = open(self.chain + "-balances.pickle", "rb")
            self.balances = pickle.load(f)
        except:
            self.balances = {}
        self.blockchain = Blockchain(os.path.expanduser(self.chainpath), chain_const[self.chain]["pch"])
            
    def dump(self):
        f = open(self.chain + "-txindex.pickle", "wb")
        pickle.dump(self.txindex, f)
        f = open(self.chain + "-balances.pickle", "wb")
        pickle.dump(self.balances, f)
        
    def scan_all(self, start=0, end=None):
        stop = 0
        self.txindex = {}
        if (start == 0) and (end is None):
            block_generator = self.blockchain.get_unordered_blocks()
            self.balances = {}
        else:
            try:
                f = open(self.chain + "-txindex.pickle", "rb")
                self.txindex = pickle.load(f)
            except:
                self.txindex = {}
            block_generator = self.blockchain.get_ordered_blocks(os.path.expanduser(self.chainpath + "/index"), start=start, end=end)
        unresolved = []
        for block in block_generator:
            stop = stop + 1
            if not (end is None) and (stop > end):
                break
            #print block
            if stop % 1000 == 0:
                print (stop)
            for transaction in block.transactions:
                self.txindex[transaction.hash] = {}
                output_i = 0
                for output in transaction.outputs:
                    self.txindex[transaction.hash][output_i] = [output.value, []]
                    for address in output.addresses:
                        addr = address.get_address(version_bytes=chain_const[self.chain]["vb"])
                        self.txindex[transaction.hash][output_i][1].append(addr)
                        if not addr in self.balances:
                            self.balances[addr] = output.value
                        else:
                            self.balances[addr] += output.value
                    output_i += 1
                for inp in transaction.inputs:
                    try:
                        tx = self.txindex[inp.transaction_hash][inp.transaction_index]
                        for address in tx[1]:
                            if not address in self.balances:
                                self.balances[address] = -tx[0]
                            else:
                                self.balances[address] -= tx[0]
                    except:
                        unresolved.append([inp.transaction_hash, inp.transaction_index])
        for txd in unresolved:
            try:
                tx = self.txindex[txd[0]][txd[1]]
                for address in tx[1]:
                    if not address in self.balances:
                        self.balances[address] = -tx[0]
                    else:
                        self.balances[address] -= tx[0]
            except:
                pass
        self.dump()
        del self.txindex
        self.txindex = {}
        
    def get_balance(self, address):
        if address in self.balances:
            return self.balances[address] / 100000000.0
        else:
            return "Unknown address"

app = Flask(__name__)

@methods.add
def ping():
    return 'pong'

@methods.add
def getbalance(*args, **kwargs):
    #TODO validation
    rpcchain = kwargs['chain']
    rpcaddr = kwargs['address']
    p = plugins[rpcchain]
    rpcbalance = p.get_balance(rpcaddr) 
    return "getbalance", rpcbalance

@app.route('/', methods=['POST'])
def index():
    req = request.get_data().decode()
    response = methods.dispatch(req)
    return Response(str(response), response.http_status,
                    mimetype='application/json')

#@app.route("/api/v1/status")
#def v1status():
#    return "Status Check"

if __name__ == "__main__":
    f = open("xrmbalance.ini", "r")
    config = json.loads(f.read())
    plugins = {}
    for coin in config.keys():
        plugins[coin] = BalancePlugin(coin, config[coin])

    print (config.keys())
    print ( len(sys.argv) )
    if len(sys.argv) < 2:
        app.run(host="0.0.0.0", port=int("5000"), debug=True)
    elif len(sys.argv) < 4:
        command = sys.argv[1]
        chain = sys.argv[2]
        #TODO if adding more commands refactor
        if command == "scan":
            print ('Scanning Blockchain: %s' % chain)
            p = plugins[chain]
            p.scan_all()

