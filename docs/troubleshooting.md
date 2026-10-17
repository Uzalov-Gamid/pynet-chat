# Troubleshooting

Connection refused: start the server first and check that both sides use the same
host and port. An address already in use usually means another process is bound
to that port; stop it or choose another port. IPv6 loopback requires OS support.

Username already connected: choose another name or close the earlier client.
Do not delete another participant's entry from a running server. A client that
never sends a username is disconnected after ten seconds.

Recipient not connected: the sender remains usable. Check the target's spelling
and whether that participant is still online. Broadcasts reach only friends who
are connected at send time; there is no offline delivery.

Unexpected disconnect: verify that both client and server use the JSON protocol.
Invalid frames and oversized messages terminate a connection. Terminal EOF or
Ctrl+C exits the client; Ctrl+C on the server closes active sockets and workers.

To reset local friends, back up `data.json` before removing it. Starting from
another directory also creates a separate local state file. Keep that file out
of version control if it contains personal contact names.
