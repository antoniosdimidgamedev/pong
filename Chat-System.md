# Chat System

The in-game chat lets players communicate during multiplayer matches.

## Using Chat

1. Press **`/`** during a multiplayer game to enter chat mode
2. The chat buffer appears at the bottom of the screen with a `/` prefix
3. Type your message (ASCII characters only)
4. Press **`Enter`** to send
5. Press **`Esc`** to cancel

Chat messages appear at the bottom of the game screen, above the chat input line. Up to **100 messages** are shown at a time.

## Server-Side Features

### Message History

The server stores the last 100 chat messages per room. When a new player joins, the server sends the full history so they can catch up on the conversation.

```python
# Server sends on player join:
{"type": "chat_history", "messages": [
    {"from": "Alice", "text": "gl hf"},
    {"from": "Bob", "text": "u2"},
    ...
]}
```

### Profanity Filter

All chat messages are filtered server-side before being relayed to other players. The filter (`_filter_chat()`) uses case-insensitive matching against a list of common profanity and replaces offensive words with asterisks.

```python
# Example: "what the f***" → "what the ****"
```

The filter runs on every chat message in `Room.handle_chat()` before broadcasting.

## Protocol

**Client sends:**
```json
{"type": "chat", "text": "hello everyone"}
```

**Server broadcasts to all players in the room (filtered):**
```json
{"type": "chat", "from": "Alice", "text": "hello everyone"}
```

## Display

- Chat messages are shown at the **bottom** of the game screen
- Each line shows: `PlayerName: message`
- The chat input area shows: `/your text here` with a cursor
- Messages older than 100 are scrolled out of view
- Chat does **not** interfere with gameplay — pressing `/` pauses input processing until chat mode is exited
