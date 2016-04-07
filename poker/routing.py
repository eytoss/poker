from channels.routing import route
from .consumers import ws_connect, ws_message, ws_disconnect

channel_routing = [
    route("websocket.connect", ws_connect, path=r"^/(?P<table_guid>[0-9a-z-]+)/(?P<user_guid>[0-9a-z-]+)/$"),
    route("websocket.receive", ws_message),
    route("websocket.disconnect", ws_disconnect),
]
