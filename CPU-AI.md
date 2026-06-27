# CPU AI

The CPU opponent uses a configurable ball-tracking AI with three parameters: **threshold**, **speed**, and **jitter**. These combine to create three distinct difficulty levels.

## AI Mechanics

The CPU only moves when the ball is heading toward its paddle (ball direction `dir_x > 0`) or when the ball is within 15 pixels of the paddle. This prevents the CPU from chasing the ball away from the play area.

### Decision Logic

```
if ball_dir_x > 0 OR ball is within 15px of paddle:
    distance = abs(paddle_center - ball_y)
    if distance > threshold:
        move paddle toward ball at `speed` pixels/tick
    add random jitter (±jitter % chance to reverse direction)
else:
    drift slowly back to center (random walk)
```

## Difficulty Parameters

| Difficulty | Threshold | Speed | Jitter | Behavior |
|------------|-----------|-------|--------|----------|
| **Easy** | 3.0 | 1 | 30% | Slow, imprecise, often misses — good for beginners |
| **Medium** | 1.5 | 2 | 10% | Balanced — competitive for most players |
| **Hard** | 0.5 | 3 | 2% | Fast, precise, rarely misses — challenging |

- **Threshold**: how far off-center the ball must be before the CPU reacts (higher = lazier)
- **Speed**: pixels per tick the paddle moves (higher = faster)
- **Jitter**: percentage chance per tick that the CPU moves the wrong direction (higher = more erratic)

## Implementation

The AI runs in `cpu_inputs(game, difficulty, tick)` and returns a set of actions (`up`, `down`) that are fed into the standard `update()` method alongside human inputs. The CPU's tick counter is used for random seeding to avoid deterministic-but-identical behavior across runs.

```python
def cpu_inputs(game, difficulty, tick):
    params = {
        "easy":   {"thresh": 3.0, "speed": 1, "jitter": 0.30},
        "medium": {"thresh": 1.5, "speed": 2, "jitter": 0.10},
        "hard":   {"thresh": 0.5, "speed": 3, "jitter": 0.02},
    }[difficulty]
    # ... ball-tracking logic with random jitter
```
