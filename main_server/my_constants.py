from flask import Flask

UPLOAD_FOLDER = '/Users/souviksaha/Desktop/IPFSUploads'
DOWNLOAD_FOLDER = '/Users/souviksaha/Desktop/IPFSDownloads'
app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
