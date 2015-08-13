# Factorio Log Parser
A crude log parser for Factorio.
Run this within a screen, or use the provided systemd example unit to monitor and parse your factorio log.

The script will output a status.json file containing the connected peers throughout the server sessions lifetime.
(the list of peers will be reset every time the server/script is restarted).

While the script itself only provides the information it is up to you to use it in a creative way - for example by presenting the currently online peers on your server status page, or listing the most frequently re-connecting player this session?

# JSON example
 ```JSON
{
 "generated": "2015-08-13T11:07:24.635245+00:00",
 "peers": {
  "1": {
   "connected": "2015-08-13T11:07:20.475868+00:00",
   "desyncs": [],
   "disconnected": "2015-08-13T11:07:20.481195+00:00",
   "online": false,
   "peer_ip": "X.X.X.X",
   "peer_port": 34198,
   "player_index": "0",
   "username": "RandomPlayer"
  },
  "2": {
   "connected": "2015-08-13T11:07:20.476307+00:00",
   "desyncs": [
    "2015-08-13T11:07:20.476866+00:00",
    "2015-08-13T11:07:20.477324+00:00"
   ],
   "disconnected": "2015-08-13T11:07:20.478208+00:00",
   "online": false,
   "peer_ip": "X.X.X.X",
   "peer_port": 51518,
   "player_index": "4",
   "username": "RandomGuy"
  },
  "3": {
   "connected": "2015-08-13T11:07:20.478347+00:00",
   "desyncs": [
    "2015-08-13T11:07:20.478886+00:00",
    "2015-08-13T11:07:20.479342+00:00",
    "2015-08-13T11:07:20.479851+00:00",
    "2015-08-13T11:07:20.480313+00:00",
    "2015-08-13T11:07:20.480766+00:00",
    "2015-08-13T11:07:20.481278+00:00"
   ],
   "disconnected": "2015-08-13T11:07:20.482085+00:00",
   "online": false,
   "peer_ip": "X.X.X.X",
   "peer_port": 34197,
   "player_index": "8",
   "username": "SomeOne"
  }
 }
}
