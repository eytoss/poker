from channels import Group
from channels.sessions import channel_session
from .models import Game, User

# Connected to websocket.connect
def ws_connect(message, table_guid, user_guid):
    # Work out room name from path (ignore slashes)
    # table_guid = message.content['path'].strip("/")
    # Save room in session and add us to the group
    # message.channel_session['room'] = room
    # check if table exists and you're allowed to be on there
    try:
        game = Game.objects.filter(guid=table_guid)[0]
        if user_guid in game.players_entered:
            Group("table-{}".format(table_guid)).add(message.reply_channel)
            print 'ws connect sent to ' + "table-{}".format(table_guid)
    except Exception as e:
        print e 
        pass

# Connected to websocket.receive
def ws_message(message):
    pass
#     Group("chat-%s" % message.channel_session['room']).send({
#         "text": message['text'],
#     })

# Connected to websocket.disconnect
def ws_disconnect(message):
    # Group("chat-%s" % message.channel_session['room']).discard(message.reply_channel)
    pass
