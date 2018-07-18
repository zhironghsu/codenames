"""Flask server for Codenames"""
# pylint: disable=C0103

import eventlet
import os
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from .codenames import game

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = b'FF\x90}\xdc\xc5\xaeaT\xd6\xbc\x86O\xa6B\xdd\xa2qp\x9e\xd2f\xe8\xe8'

ROOMS = {}

# @app.route('/purge')
# def purge():
#     """Delete all rooms"""
#     purged = ROOMS.keys()
#     total = len(purged)
#     ROOMS.clear()
#     return jsonify({
#         "purged": purged,
#         "total": total
#     })

@app.route('/stats')
def stats():
    """display room stats"""
    resp = {
        "total": len(ROOMS.keys())
    }
    if 'rooms' in request.args:
        resp["rooms"] = sorted(ROOMS, lambda k: k['date_modified'], reverse=True)
    return jsonify(resp)

@socketio.on('create')
def on_create(data):
    """Create a game lobby"""
    # username = data['username']
    # create the game
    # handle custom wordbanks
    if data['dictionaryOptions']['useCustom']:
        gm = game.Info(
            size=data['size'],
            teams=data['teams'],
            wordbank=data['dictionaryOptions']['customWordbank'])
    # dict mixer
    elif data['dictionaryOptions']['mix']:
        gm = game.Info(
            size=data['size'],
            teams=data['teams'],
            mix=data['dictionaryOptions']['mixPercentages'])
    # handle standard single dictionary
    else:
        gm = game.Info(
            size=data['size'],
            teams=data['teams'],
            dictionary=data['dictionaryOptions']['dictionaries'])

    room = gm.game_id
    ROOMS[room] = gm
    join_room(room)
    # rooms[room].add_player(username)
    emit('join_room', {'room': room})

@socketio.on('join')
def on_join(data):
    """Join a game lobby"""
    # username = data['username']
    room = data['room']
    if room in ROOMS:
        # add player and rebroadcast game object
        # rooms[room].add_player(username)
        join_room(room)
        send(ROOMS[room].to_json(), room=room)
    else:
        emit('error', {'error': 'Unable to join room. Room does not exist.'})

@socketio.on('leave')
def on_leave(data):
    """Leave the game lobby"""
    # username = data['username']
    room = data['room']
    # add player and rebroadcast game object
    # rooms[room].remove_player(username)
    leave_room(room)
    send(ROOMS[room].to_json(), room=room)

@socketio.on('flip_card')
def on_flip_card(data):
    """flip card and rebroadcast game object"""
    room = data['room']
    card = data['card']
    ROOMS[room].flip_card(card)
    send(ROOMS[room].to_json(), room=room)

@socketio.on('regenerate')
def on_regenerate(data):
    """regenerate the words list"""
    room = data['room']
    ROOMS[room].generate_board()
    send(ROOMS[room].to_json(), room=room)

@socketio.on('list_dictionaries')
def list_dictionaries():
    """send a list of dictionary names"""
    # send dict list to client
    emit('list_dictionaries', {'dictionaries': list(game.DICTIONARIES.keys())})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
