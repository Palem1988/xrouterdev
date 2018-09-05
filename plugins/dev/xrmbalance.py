#!/usr/bin/python3

import os
import sys
import collections
import json
import pickle
import json
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
        else:
            try:
                f = open(self.chain + "-txindex.pickle", "rb")
                self.txindex = pickle.load(f)
            except:
                self.txindex = {}
            block_generator = self.blockchain.get_ordered_blocks(os.path.expanduser(self.chainpath + "/index"), start=start, end=end)
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
            
if __name__ == "__main__":
    f = open("xrmbalance.ini", "r")
    config = json.loads(f.read())
    plugins = {}
    for coin in config.keys():
        plugins[coin] = BalancePlugin(coin, config[coin])
        
    if len(sys.argv) < 3:
        print("Not enough parameters")
        sys.exit(0)
    chain = sys.argv[1]
    if not chain in plugins:
        print("This chain is not available yet")
        sys.exit(0)
    command = sys.argv[2]
    p = plugins[chain]
    if command == "scan":
        p.scan_all()
    elif command == "getbalance":
        if len(sys.argv) < 4:
            print("Address not specified")
            sys.exit(0)
        else:
            addr = sys.argv[3]
            print(p.get_balance(addr))
    #print(len(list(p.balances.keys())))
    #print(p.balances['xyLmRZxgDhnHq9xbCtV6HQQLNCDMxzJKbz'] / 100000000.0)
    '''for k in p.balances:
        if p.balances[k] > 1000000000000:
            print (k, p.balances[k] / 100000000.0)'''