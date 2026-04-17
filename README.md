# Random Resolution Picker

A ComfyUI node that randomly picks a `width` and `height` from a user-defined list on every generation.

## Inputs

| Input | Type | Description |
|-------|------|-------------|
| `resolutions` | STRING (multiline) | One `width,height` per line (see format below) |
| `auto_randomize` | BOOLEAN | When `true`, picks a new pair every queue run (ignores `seed`) |
| `seed` | INT | Fixed seed for deterministic picks when `auto_randomize` is `false` |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `width` | INT | Picked width in pixels |
| `height` | INT | Picked height in pixels |
| `label` | STRING | Human-readable label, e.g. `1664x928` |

## Resolution list format

```
# Lines starting with # are comments and are ignored.
# Blank lines are also ignored.
1328,1328
1664,928
928,1664
```

### Weighted entries

Duplicate lines intentionally increase probability. List a size twice to make it twice as likely:

```
# 1328x1328 is 2× more likely than 1664x928
1328,1328
1328,1328
1664,928
```

## PNG metadata

When a **Save Image** node is downstream, this node writes its pick into the PNG metadata under the key `RandomResolutionPicker`:

```json
{
  "resolution": "1664x928",
  "resolution_width": 1664,
  "resolution_height": 928,
  "resolution_seed": 1234567
}
```

## Usage tip

Wire `width` and `height` directly into **Empty Latent Image**'s width/height inputs.  
With `auto_randomize=true`, every queue run picks a fresh resolution from your list.
