# Images and saved commands

These core utilities are always available without enabling a module. Use
`max-dev` for a development installation; `max` uses your installed stable release.
The `gm` namespace groups image recipes and saved command management; it uses
ImageMagick when installed and falls back to GraphicsMagick.

## Resize App Store screenshots

```sh
max gm appstore --input 'input file.png' --output 'appstore screenshot.png'
max gm appstore                       # Prompt for paths, geometry, and background
max gm                                # Choose a recipe, then enter its variables
max gm appstore --input input.png --output output.png --dry-run
max gm appstore --input input.png --output output.png --overwrite
```

The packaged `appstore-resize` recipe executes the equivalent of:

```sh
magick input.png -resize '1284x2778!' -background white -flatten output.png
# If only GraphicsMagick is installed:
gm convert input.png -resize '1284x2778!' -background white -flatten output.png
```

The exclamation mark forces the exact dimensions, potentially stretching the
image. This is the requested size, not a claim that it is suitable for every
App Store device listing. `--size` accepts other ImageMagick geometry strings.
The default background is white; interactive invocation offers white and black.
`--background white` explicitly skips that menu.

ImageMagick 7 (`magick`) is preferred; GraphicsMagick (`gm convert`) is a fallback.
If neither exists, conversion prints installation instructions. On macOS run
`brew install imagemagick`. MaxCLI never installs dependencies during a conversion.
A dry run can preview a command even without an installed engine or input file.

Input and output must be different files. Existing output files require
`--overwrite`; the output directory must already exist. Image paths are expanded
and resolved before execution, so paths with spaces and leading dashes stay single
file arguments. These checks also apply to saved recipes using the `imagemagick`
engine, which must declare `{input}` and `{output}`.

## Save and invoke commands

```sh
max gm commands save 'Resize thumbnail' \
  --description 'Resize an image while preserving aspect ratio' \
  --command 'magick "{input}" -resize "{size}" "{output}"' \
  --default 'size=256x256' --engine imagemagick
max gm commands save 'List files' --command 'ls {style}' \
  --default 'style=-l' --choice 'style=-l' --choice 'style=-la'
max gm commands list
max gm commands list --json
max gm commands show 'List files'
max gm commands run 'List files'
max gm commands run 'List files' --set 'style=-la' --dry-run
max gm commands run                         # Select a recipe by name
max gm commands                             # Also opens the recipe picker
max gm commands save 'List files' --command 'ls -la' --replace
max gm commands remove 'List files'
```

Names may be human-readable strings with spaces. Omit `--command` to enter the
template at a prompt. Placeholders are inferred from the template; use simple
`{variable}` names. Repeat `--default NAME=VALUE` for variable defaults and
`--choice NAME=VALUE` for each allowed choice. A default must be an allowed choice
when choices are specified. Use `{{` and `}}` for literal braces in templates.

Templates are split once with shell-style quoting, stored as argument arrays,
and run without a shell. Variable values remain literal, single arguments even
when they contain spaces or shell punctuation. Pipes, redirects, globbing, shell
expansion, and command substitution are not interpreted. Recipes still run the
chosen executable with your permissions; inspect imported recipes before running.
All commands run in the directory where you invoke MaxCLI.

`--set NAME=VALUE` supplies a variable without a prompt. Interactive runs offer
choice menus or text prompts showing defaults. In scripts or with the global
`--non-interactive` option, omitted variables use defaults or fail with an
instruction to supply `--set`. Child exit codes propagate to MaxCLI.
`--dry-run` prints the resolved argument array as JSON and never launches the recipe.

Recipes are stored atomically with owner-only file permissions in
`~/.config/maxcli/saved_commands.json`, or the development channel's configuration
folder. `MAXCLI_CONFIG_DIR` and `XDG_CONFIG_HOME` work as usual. Existing commands
require `--replace` to update. Replacing a packaged command creates a user override;
removing that override reveals the original packaged preset again.

## Share packs

```sh
max gm commands export image-recipes.json appstore-resize 'Resize thumbnail'
max gm commands export all-recipes.json
max gm commands import image-recipes.json
max gm commands import image-recipes.json --replace
```

Exports contain the selected recipes, or all recipes when names are omitted.
Exports include literal command arguments and defaults: inspect them before
sharing if you store sensitive values. Existing export files require `--replace`.
Import validates the entire pack before writing, never executes commands, and
rejects name collisions unless `--replace` is specified.

A pack is ordinary editable JSON. For example:

```json
{
  "version": 1,
  "commands": {
    "List files": {
      "description": "Choose a listing format",
      "command": ["ls", "{style}"],
      "variables": {
        "style": {
          "prompt": "Listing format",
          "default": "-l",
          "choices": ["-l", "-la"]
        }
      }
    }
  }
}
```

Set `"engine": "imagemagick"` on conversion recipes whose argument array starts
with `"magick"` and includes `{input}` and `{output}` to enable engine fallback and
file checks. Other recipes use the default `command` engine and execute their
argument arrays directly.

Saved commands are included in GPG-encrypted configuration backups and validated
on restore. Merging a backup retains local-only recipes and replaces matching
recipes with the complete incoming definition. Ordinary unencrypted backups omit
saved commands because arbitrary arguments or defaults may contain secrets. Use an encrypted backup for full
recovery, or explicitly export recipes. A full restore from an unencrypted backup
therefore has no user recipes; `--merge` retains local recipes, and the recovery
copy preserves the previous settings. `max doctor` checks the registry format.
