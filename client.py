import socketio
import re

client = socketio.Client()


@client.on('connect')
def connect(*args):
    print(args)
    client.emit('get_updates')


@client.on('disconnect')
def disconnect(*args):
    print(args)


@client.on('message')
def message(*args):
    print("message:", args)


@client.on('update')
def update(*args):
    if 'messages':
        thisdict = args[0][0]
        for i in thisdict:
    #print("update:", args)
            print('user {} send {} message '.format(thisdict[i+1], thisdict[i]))


self_username = input('Input your username\n')
password = input('Input your password\n')

print('\n\n')
client.connect('http://127.0.0.1:5001', headers={'username': self_username, 'password': password})

while True:
    input_string = input('{message}@@{username}\n')
    message, to_username = [i.strip() for i in input_string.split('@@')]
    client.emit('message', {'from': self_username, 'to': to_username, 'message': message})

