import os
import urllib.request
import ipfshttpclient
from my_constants import app
from flask import Flask, flash, request, redirect, render_template, url_for, jsonify
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, send, emit
import socket
import pickle
from blockchain import Blockchain
import requests
import socketio

# The package requests is used in the 'hash_user_file' and 'retrieve_from hash' functions to send http post requests.
# Notice that 'requests' is different than the package 'request'.
# 'request' package is used in the 'add_file' function for multiple actions.

sio = socketio.Client() 
client_ip = app.config['NODE_ADDR']

blockchain = Blockchain()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def append_file_extension(uploaded_file, file_path):
    file_extension = uploaded_file.filename.rsplit('.', 1)[1].lower()
    user_file = open(file_path, 'a')
    user_file.write('\n' + file_extension)
    user_file.close()

def hash_user_file(user_file):
    client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
    response = client.add(user_file)
    file_hash = response['Hash']
    return file_hash

def retrieve_from_hash(file_hash):
    client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
    file_content = client.cat(file_hash)
    file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], file_hash)
    user_file = open(file_path, 'ab+')
    user_file.write(file_content)
    with open(file_path, 'rb') as f:
        lines = f.read().splitlines()
        last_line = lines[-1]
    user_file.close()
    file_extension = last_line
    saved_file = file_path + '.' + file_extension.decode()
    os.rename(file_path, saved_file)
    print(saved_file)
    return saved_file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('first.html')

@app.route('/add_file', methods=['POST'])
def add_file():
    
    is_chain_replaced = blockchain.replace_chain()

    if is_chain_replaced:
        print('The nodes had different chains so the chain was replaced by the longest one.')
    else:
        print('All good. The chain is the largest one.')

    if request.method == 'POST':
        error_flag = True
        if 'file' not in request.files:
            message = 'No file part'
        else:
            user_file = request.files['file']
            if user_file.filename == '':
                message = 'No file selected for uploading'

            if user_file and allowed_file(user_file.filename):
                filename = secure_filename(user_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                user_file.save(file_path)
                append_file_extension(user_file, file_path)
                hashed_output1 = hash_user_file(file_path)
                sender = request.form['sender_name']
                receiver = request.form['receiver_name']
                index = blockchain.add_file(sender, receiver, hashed_output1)
                message = f'File successfully uploaded to Infura. This file will be added to Block {index}'
                error_flag = False
            else:
                message = 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'
    
        if error_flag == True:
            return render_template('first.html')
        else:
            return render_template('second.html', messages = {'message1' : message , 'message2' : "Path of the uploaded file : " + file_path , 'blockchain' : blockchain.chain})

@app.route('/retrieve_file', methods=['POST'])
def retrieve_file():
    if request.method == 'POST':

        error_flag = True

        if request.form['file_hash'] == '':
            message = 'No hash entered.'
        else:
            error_flag = False
            file_hash = request.form['file_hash']
            file_path = retrieve_from_hash(file_hash)
            message = 'File successfully downloaded from infura'

        if error_flag == True:
            return render_template('second.html', messages = {'message1' : message , 'message2' : ' Use the "Add another file" button to enter the hash' , 'blockchain' : blockchain.chain})
        else:
            return render_template('second.html',messages = {'message1' : message , 'message2' : "Path of the downloaded file : " + file_path , 'blockchain' : blockchain.chain})

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

@sio.event
def connect():
    print('connected to server')

@sio.event
def disconnect():
    print('disconnected from server')

@sio.event
def my_response(message):
    print(pickle.loads(message['data']))
    blockchain.nodes = pickle.loads(message['data'])

@app.route("/connect_to_blockchain", methods=["GET"])
def connect_to_blockchain():

    sio.connect('http://'+app.config['SERVER_IP'])
    sio.emit('add_client_node', 
            {'node_address' : client_ip['Host'] + ':' + str(client_ip['Port'])}
            )
    return render_template('first.html')

if __name__ == '__main__':
    app.run(host = client_ip['Host'], port= client_ip['Port'])