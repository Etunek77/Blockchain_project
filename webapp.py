from uuid import uuid4
from flask import Flask, jsonify, request, render_template, session
from flask_bower import Bower
from argparse import ArgumentParser, ArgumentTypeError
from classes.blockchain import Blockchain


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
# Instantiate the Blockchain
blockchain = Blockchain()

@app.route("/")
def main():
    if not session.get('logged_in'):
        return render_template('views/login.html')
    else:
        return "Hello Boss!"
    

@app.route('/api/mine', methods=['POST'])
def mine(): 
    if not all(k in values for k in required):
        return 'Missing values', 400

    if not blockchain.verify_transactions():
        # if there are no transactions in queue (or) if there are no non-invalid transactions
        # return status code 406: Not Acceptable    
        print("ERROR: Invalid transaction")
        return jsonify("Transaction Error: Queue either empty or invalid trasnactions"), 406
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/api/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['voter', 'voted_for', 'private_key']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['voter'], values['vote_for'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/api/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/api/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/api/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type= int, help='port to listen on')
args = parser.parse_args()
port = args.port    
app.run(host='0.0.0.0', port=port)