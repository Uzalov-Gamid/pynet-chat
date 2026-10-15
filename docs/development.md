# Development and checks

From the repository root:

```bash
python -m unittest discover -s tests -v
```

`protocol.py` owns framing, write serialization and shared CLI options.
`server/server.py` owns connection registration, routing and shutdown.
`client/client.py` owns terminal interaction and the local friend file.

Tests use socket pairs for fragmented/coalesced frames and concurrent writers,
and loopback listeners for lifecycle checks. They verify duplicate-name handling,
stale recipients, handshake timeouts and import safety without a remote server.
The IPv6 loopback test skips only when the host cannot bind an IPv6 listener.

Keep `recv` boundaries independent from message boundaries. A protocol change
must update both endpoints and the wire documentation. Keep socket ownership
explicit: shutdown must unblock readers before joining worker threads.

This is a networking practice project with one thread per connection. It does
not provide identity verification, persistent server-side delivery or a load
balancer. CI runs the same standard-library test suite on supported Python versions.
