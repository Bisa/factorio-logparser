# Factorio Log Parser
A crude log parser for Factorio.
Run this within a screen, or use the provided systemd example unit to monitor and parse your factorio log.

The script will output a status.json file containing the connected peers throughout the server sessions lifetime.
(the list of peers will be reset every time the server/script is restarted).

While the script itself only provides the information it is up to you to use it in a creative way - for example by presenting the currently online peers on your server status page, or listing the most frequently re-connecting player this session?
