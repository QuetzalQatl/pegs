from flask import Flask, render_template, request, send_file,abort, redirect
from flask_socketio import SocketIO, join_room, leave_room, emit, send
from urllib.request import urlopen
from base64 import b64decode, decodebytes
from urllib.parse import unquote

#from codenames import game
import time
import random
import traceback
import socket
import sys
import os
import json

#this program needs:
#pip install flask flask-socketio eventlet

PORT=5000 # default, can be set at startup by setting the environment variable 'PORT'
LANIP='192.168.99.100' # default, can be set at startup by setting the environment variable 'LANIP'

locationBoardFiles="/boards/"
locationPrivateFiles="/private/"
boardNames={}
#characters allowed in boardnames:
allowed='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_'
maxnamelen=32

localIP='127.0.0.1'
WANIP=''

# initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(512)
socketio = SocketIO(app)

def getWideIpAdres():
    try:
        html = urlopen("https://whatsmyip.com/")
        lines=html.readlines()
        html = ''
        for l in lines:
            if l.find(b'Your IP') != -1 and l.find(b'is:') != -1:
                lines2=l.split(b'><')
                for l2 in lines2:
                    if l2.find(b'p class="h1 boldAndShadow">') !=-1 and l2.find(b'</p') !=-1:
                        return l2[27:-3].decode('ascii')
    except:
        traceback.print_exc()
        # perhaps try one or two others
    print ('OMG!!!! Could not find wide ip adres.... Is internet connected/working?')
    return ''

def checkName(strName):
	strName=str(strName)
	if len(strName)==0 or len(strName)>maxnamelen:
		return False
	foundIllegalChar=False
	for s in strName:
		if not s in allowed:
			foundIllegalChar=True
	if foundIllegalChar:
		return False
	if strName.upper()=='ADMIN':
		return False
	if strName.upper()=='BOARDS':
		return False
	if strName.upper()=='STATIC':
		return False
	return True

def stripName(name):
	name=name.strip()
	newname=''
	counter=0
	for n in name:
		if n in allowed:
			newname=newname+n
			counter=counter+1
			if counter==maxnamelen:
				break
	return newname
	
def GetConnectTo(remote_address):
    if (remote_address==localIP):
        return localIP+':'+str(PORT)
    elif (remote_address[:4]=='192.'):
        return LANIP+':'+str(PORT)
    else:
        return WANIP+':'+str(PORT)

def readRecords(boardname):
	with open(locationBoardFiles+boardname+'.txt', "r") as f:
		lines=f.readlines()
	args=json.loads(lines[0])
	return (args['recordLeft'],args['recordSeconds'],args['recordHolder'])	

def getRecord(strBoardName):
	try:
		pegsleft, seconds, recordholder=boardNames[strBoardName]
		if pegsleft==0:
			return recordholder # 'Nobody'
		else:
			return str(pegsleft)+' left in '+str(seconds)+' seconds by: '+recordholder
	except Exception as x:
		print(x)
		traceback.print_exc()
		return (0,0,'')

def saveRecord(strBoardName, newLeft, newSeconds, newRecordholder):
	result=False
	try:
		with open(locationBoardFiles+strBoardName+'.txt', "r") as f:
			lines=f.readlines()
		args=json.loads(lines[0])
		newRecord=False
		oldLeft=int(args['recordLeft'])
		oldSeconds=float(args['recordSeconds'])
		if (oldLeft==0 or oldLeft>newLeft):
			newRecord=True
		else:
			if oldLeft==newLeft and oldSeconds>newSeconds:
				newRecord=True
				
		if newRecord:
			args['recordHolder']=newRecordholder
			args['recordLeft']=newLeft
			args['recordSeconds']=newSeconds
			boardNames[strBoardName]=(newLeft, newSeconds, newRecordholder)
			with open(locationBoardFiles+strBoardName+'.txt', "w") as f:
				f.write(json.dumps(args))
	except Exception as x:
		print(x)
		traceback.print_exc()	

def pegIndex(request):
	userConnectsTo=GetConnectTo(request.remote_addr)
	strPics='<center><table style="width:100%"><tr valign="middle"><th>name:</th><th>preview:</th><th>record:</th></tr>\n'
	for name in boardNames:
		strPics=strPics+'<tr valign="middle"><td align="center">'+name+'</td><td align="center"><a href="/peg/'+name+'"><img src="/boards/'+name+'.png" /></a></td><td align="center">'+getRecord(name)+'</td></tr>\n'
	strPics=strPics+'</table></center>'
	a= render_template('peg.html')
	a=a.replace('%%CONNECTTO%%',userConnectsTo)
	a=a.replace('%%PICS%%',strPics)
	return a

@app.route('/')
def app_index():
	print (request.remote_addr,'/')
	return pegIndex(request)
	
@app.route('/peg')
def app_peg():
	print (request.remote_addr,'/peg')
	return pegIndex(request)  

@app.route('/peg/')
def app_pegslash():
	print (request.remote_addr,'/peg/')
	return pegIndex(request)  

@app.route('/peg/<boardname>')
def app_pegboardname(boardname):
	print (request.remote_addr,'peg', boardname)
	if checkName(boardname) and boardname in boardNames:
		userConnectsTo=GetConnectTo(request.remote_addr)
		lines=''
		ls=[]
		with open(locationBoardFiles+boardname+'.txt', "r") as f:
			ls=f.readlines()
		for l in ls:
			lines=lines+str(l)
		args=json.loads(lines)
		
		strVARS="""		boardName='"""+boardname+"""';
		var boardSize="""+str(args['size'])+""";
		var boardIsHexagon='"""+str(args['isHexagon'])+"""';
		var boardRecordLeft='"""+str(args['recordLeft'])+"""';
		var boardRecordSeconds='"""+str(args['recordSeconds'])+"""';
		var boardRecordName='"""+str(args['recordHolder'])+"""';
		var boardArray=["""
		counter=0
		nrOfSpots=len(args['board'])/3
		strboard=str(args['board'])
		strboard=strboard[2:-2].split('),(')
		first=True
		while counter<len(strboard):
			thisboard=strboard[counter].split(',')
			x=thisboard[0]
			y=thisboard[1]
			type=thisboard[2]
			if first:
				first=False
			else:
				strVARS=strVARS+','
			strVARS=strVARS+'['+str(x)+','+str(y)+',"'+type.strip()+'", false]'
			counter=counter+1
		strVARS=strVARS+'];'
		a= render_template('peggame.html')
		a=a.replace('%%CONNECTTO%%',userConnectsTo)
		a=a.replace('%%VARS%%',strVARS)
		return a
	else:
		return pegIndex(request)

@app.route('/boards/<boardname>')
def app_boards(boardname):
	if boardname[:-4] in boardNames:
		return send_file(locationBoardFiles+boardname, mimetype='image/png')
		print('/boards/<boardname>', boardname)
	else:
		print('not found', '/boards/<boardname>', boardname)
		return abort(404) 

@app.route('/peggame')
def app_peggame():
    a= render_template('peggame.html')
    a=a.replace('%%CONNECTTO%%',GetConnectTo(request.remote_addr))
    print (request.remote_addr, '/peggame --> /peggame.html')
    return a

@app.route('/pegadmin')
def app_pegadmin():
    a= render_template('pegadmin.html')
    a=a.replace('%%CONNECTTO%%',GetConnectTo(request.remote_addr))
    print (request.remote_addr, '/pegadmin --> /pegadmin.html')
    return a

@app.route('/babylon.js')
def app_babylon():
	print (request.remote_addr, locationPrivateFiles+'/babylon.js --> /babylon.js')
	return send_file(locationPrivateFiles+'/babylon.js', mimetype='application/javascript')

@app.route('/favicon.ico')
def app_favicon():
	print (request.remote_addr, locationPrivateFiles+'/favicon.ico --> /favicon.png')
	return send_file(locationPrivateFiles+'/favicon.png', mimetype='image/ico')
   
@socketio.on('savepeg', namespace='/peglobbie')
def on_savepeg(args):
	try:
		name=stripName(args['name'])
		boardName=args['boardName']
		if boardName in boardNames:
			left=int(args['left'])
			seconds=float(args['seconds'])
			name=stripName(args['name'])
			saveRecord(boardName, left, seconds, name)
			print('newrecord: ', boardName, left, seconds, name)
	except:
		traceback.print_exc()
		print('well that went kinda wrong in savepeg')
		
@socketio.on('pegnewboard', namespace='/peglobbie')
def on_pegnewboard(args):
	print (request.sid,'on_pegnewboard: ')
	try:
		args2=args.copy()
		args2.pop('name')
		args2.pop('png')
		
		jargs=json.dumps(args2)
		name=stripName(args['name'])
		png=args['png']
		if (checkName(name)):
			try:
				with open(locationBoardFiles+name+'.txt', "w") as f:
					f.write(jargs)
			except:
				print ('file error saving: '+locationBoardFiles+name+'.txt')
				print ('disk full? writing rights ok?')
				traceback.print_exc()
			
			try:
				data=png.split(';')[1]
				data=png.split(',')[1]
				while len(data)%4>0:
					data=data+'='
				data = b64decode(data)
				with open(locationBoardFiles+name+'.png', "wb") as f:
					f.write(data)
			except:
				print ('file error saving: '+locationBoardFiles+name+'.png')
				print ('disk full? writing rights ok?')
				traceback.print_exc()
				
			boardNames[name]=(args['recordLeft'], args['recordSeconds'], args['recordHolder'])
			with open(locationPrivateFiles+'boardnames.txt', "w") as f:
				for dd in boardNames:
					f.write(dd+'\n')
	except:
		traceback.print_exc()
		print('well that went kinda wrong in on_pegnewboard')
	
	
@socketio.on('connect', namespace='/peglobbie')
def on_connect():
	print('Client '+request.sid+' connected')
	currentSocketId = request.sid

@socketio.on('disconnect', namespace='/peglobbie')
def on_disconnect():
	print('Client '+request.sid+' disconnected')
	currentSocketId = request.sid

if __name__ == '__main__':
	try:
		PORT=abs(int(os.getenv('PORT')))
	except:
		pass
	LANIP=os.getenv('LANIP', LANIP)
	WANIP=getWideIpAdres()
	print ()
	print ("Peg Solitaire")
	print ("v0.05")
	print ("localIP="+localIP)
	print ("LANIP="+LANIP)
	print ("WANIP="+WANIP)
	print ("PORT="+str(PORT))
	print ()
		
	try:
		print ('Boards:')
		with open(locationPrivateFiles+'boardnames.txt', "r") as f:
			strBoardNames=f.readlines()
		for strBoardName in strBoardNames:
			if checkName(strBoardName.strip()):
				print('ADDED: '+strBoardName.strip())	
				
				boardNames[strBoardName.strip()]=readRecords(strBoardName.strip())#left, seconds, recordholder
			else:
				if len(strBoardName.strip()):
					print('REJECTED: '+strBoardName.strip())			
	except:
		pass
	if len(boardNames)==0:
		print ('none found. Goto /pegadmin to create some!')
		
	try:
		socketio.run(app, debug=False, port=PORT, host="0.0.0.0")
	except Exception as x:
		print(x)
		traceback.print_exc()
		