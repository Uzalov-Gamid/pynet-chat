# Running the chat

Use Python 3.9 or newer; no third-party runtime dependencies are needed. Run the
server and clients in separate terminals from the repository root:

```bash
python server/server.py --host 127.0.0.1 --port 23456
python client/client.py --host 127.0.0.1 --port 23456
```

For local IPv6, use `--host ::1` on both sides. Ports must be between 1 and 65535.
A username cannot contain whitespace and must be unique among active connections.
Use `/add NAME`, `/friends`, `/chat NAME`, `/back` and `/exit` in the client.
Without an active private chat, text is routed to connected friends.

The client stores friend lists in `data.json` relative to its working directory
and synchronizes the selected user's list after connecting or adding a friend.
Use a stable working directory so that this local state can be found. The server
keeps active connections in memory; restarting disconnects all participants.

The client and server must be upgraded together. Versions before JSON framing
are incompatible with the current wire format. Importing the client module is
safe for tooling; the interactive application starts only through `main()`.
