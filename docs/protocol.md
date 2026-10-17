# Wire protocol

A frame is one JSON string encoded as UTF-8 followed by a newline byte. Embedded
newlines are JSON escapes, so they do not split frames. The limit is 1 MiB
including the terminating newline. Only strings are accepted in either direction.
The reader distinguishes an empty string message from a clean end of stream.
Malformed JSON, invalid UTF-8, incomplete frames and oversized frames close the
connection. Writes on the same socket are serialized between worker threads.

The first client frame is its username: nonempty, at most 64 characters and no
whitespace. The server waits up to ten seconds for that frame. Duplicate active
names are rejected without replacing the original connection.

Subsequent client frames are plain messages or reserved commands:

* `/msg USER TEXT` routes a private message.
* `/friends JSON` replaces the current user's friend list. JSON must be an array
  of at most 1,000 valid names. Duplicate entries are removed.

A missing private recipient produces an error frame, without closing the sender.
Plain messages are delivered to the sender's current connected friends. Friend
selection is not an authentication or authorization boundary. The protocol has
no delivery acknowledgements, offline queue or end-to-end encryption.
