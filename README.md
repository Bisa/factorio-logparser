# Factorio Log Parser
A crude log parser for Factorio.
Run this within a screen, or use the provided systemd example unit to monitor and parse your factorio log.

The script will output a status.json file containing the connected peers throughout the server sessions lifetime.
(the list of peers will be reset every time the server/script is restarted).

While the script itself only provides the information it is up to you to use it in a creative way - for example by presenting the currently online peers on your server status page, or listing the most frequently re-connecting player this session?

# Output (JSON)
The output file presents you with continous parsing result of the servers "current" state.
Using this information we can see that since the server started, peer 3 desynced 6 times in short sequence - perhaps a temporary ban is in order? With both peer ip and port at hand you could easily parse this file and adjust your firewall rules to prevent peer 3 from reconnecting for a while.

Example:
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
```

# Versioning
The code adheres to Semantic Versioning v2.0.0 http://semver.org/spec/v2.0.0.html
A release is denoted by the github release system using git tags.

# License
This code is realeased with the MIT license, see LICENSE.md
