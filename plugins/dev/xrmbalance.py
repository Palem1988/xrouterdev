#!/usr/bin/python3

import os
import sys
import collections
import json
import pickle
from blockchain_parser.blockchain import Blockchain
from blockchain_parser.script import *

class BalancePlugin:
    def __init__(self):
        try:
            f = open("txindex.pickle", "rb")
            self.txindex = pickle.load(f)
        except:
            self.txindex = {}
        try:
            f = open("balances.pickle", "rb")
            self.balances = pickle.load(f)
        except:
            self.balances = {}
        self.blockchain = Blockchain(os.path.expanduser('~/bitcoin-data/blocks'))
            
    def dump(self):
        f = open("txindex.pickle", "wb")
        pickle.dump(self.txindex, f)
        f = open("balances.pickle", "wb")
        pickle.dump(self.balances, f)
        
    def scan_all(self, start=0, end=-1):
        stop = 0
        for block in self.blockchain.get_ordered_blocks(os.path.expanduser('~/bitcoin-data/blocks/index')):
            stop = stop + 1
            if (end > 0) and (stop > end):
                break
            #print block
            print (stop)
            for transaction in block.transactions:
                self.txindex[transaction.hash] = {}
                output_i = 0
                for output in transaction.outputs:
                    self.txindex[transaction.hash][output_i] = [output.value, []]
                    for address in output.addresses:
                        self.txindex[transaction.hash][output_i][1].append(address.address)
                        if not address.address in self.balances:
                            self.balances[address.address] = output.value
                        else:
                            self.balances[address.address] += output.value
                    output_i += 1
                for inp in transaction.inputs:
                    try:
                        tx = self.txindex[inp.transaction_hash][inp.transaction_index]
                        for address in tx[1]:
                            self.balances[address] -= tx[0]
                    except:
                        pass
        self.dump()
            

p = BalancePlugin()
#p.scan_all(0, 50000)
print(len(list(p.balances.keys())))
for k in p.balances:
    if p.balances[k] > 1000000000:
        print (k, p.balances[k] / 100000000.0)