#!/usr/bin/python3

import os
import sys
import collections
import json
import pickle
import json
from flask import Flask, request, Response
from jsonrpcserver import methods
from balanceplugin import *


app = Flask(__name__)

@methods.add
def ping():
    return 'pong'

@methods.add
def getbalance(*args, **kwargs):
    #TODO validation
    #rpcchain = kwargs['chain']
    #rpcaddr = kwargs['address']
    rpcchain = args[0]
    rpcaddr = args[1]
    p = plugins[rpcchain]
    rpcbalance = p.get_balance(rpcaddr) 
    return "getbalance", rpcbalance
    
@methods.add
def getutxos(*args, **kwargs):
    #TODO validation
    #rpcchain = kwargs['chain']
    #rpcaddr = kwargs['address']
    rpcchain = args[0]
    rpcaddr = args[1]
    p = plugins[rpcchain]
    rpcutxos = p.get_utxos(rpcaddr) 
    return "getutxos", rpcutxos

@app.route('/', methods=['POST'])
def index():
    req = request.get_data().decode()
    req = json.loads(req)
    req["jsonrpc"] = "2.0"
    req = json.dumps(req)
    print (req)
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

