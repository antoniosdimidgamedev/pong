# Save & Load

Save/Load is available in **CPU mode only** (Player vs CPU). PvP and multiplayer do not support saving to avoid state confusion and sync issues.

## Save Location

Saves are stored as JSON in:

```
~/.pong/save.json
```

## Saving

Press **`S`** during a CPU game to save your progress. The game pauses and displays a confirmation message. Press any key to continue playing.

The save file contains:

```json
{
  "mode": "cpu",
  "difficulty": "medium",
  "left_score": 2,
  "right_score": 3,
  "left_y": 5,
  "right_y": 8,
  "ball_x": 40.5,
  "ball_y": 12.0,
  "ball_dir_x": 1,
  "ball_dir_y": -1,
  "width": 80,
  "height": 24
}
```

## Loading

When you select **New Game > Player vs CPU** from the menu, if a save file exists for that difficulty, a **Load Game** option appears at the Singleplayer menu. Selecting it restores your game exactly where you left off.

```python
# Detection is automatic:
# - has_save() checks if ~/.pong/save.json exists
# - Load Game only appears in the menu if a save exists
```

## Clearing

The save file is automatically cleared when:
- You finish a game (win or loss)
- You quit a CPU game without saving
- You start a new CPU game (the old save is overwritten when you save again)

## Manual Deletion

You can also delete the save manually:

```bash
rm ~/.pong/save.json
```

## Why CPU-only?

| Mode | Save Support | Reason |
|------|-------------|--------|
| Player vs CPU | ✅ | Single player, no state sync issues |
| Player vs Player (local) | ❌ | Both players would need to agree on save/load |
| LAN Multiplayer | ❌ | Real-time sync between two machines prevents reliable save/restore |
