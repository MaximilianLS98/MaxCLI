"""ImageMagick conversion shortcuts backed by saved recipes."""
import shutil
from pathlib import Path

from .runtime import CommandError, prompt_input
from .utils.interactive import interactive_selection

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff',
                    '.heic', '.heif', '.avif', '.ico', '.tga', '.svg', '.psd'}
MANUAL_PATH = 'Enter another path…'


def pick_input_image(prompt='Input image path'):
    """Offer images directly in the invocation directory, with manual entry as a fallback."""
    directory = Path.cwd()
    names = sorted((path.name for path in directory.iterdir()
                    if not path.name.startswith('.') and path.suffix.lower() in IMAGE_EXTENSIONS and path.is_file()),
                   key=lambda name: (name.casefold(), name))
    if names:
        selected = interactive_selection('{} ({})'.format(prompt, directory), names + [MANUAL_PATH])
        if selected is None:
            raise CommandError('Image selection cancelled')
        if selected != MANUAL_PATH:
            return selected
    return prompt_input(prompt + ': ')


def conversion_tool(required=True):
    if shutil.which('magick'):
        return ['magick']
    if shutil.which('gm'):
        return ['gm', 'convert']
    if required:
        raise CommandError('ImageMagick is missing. On macOS run: brew install imagemagick. GraphicsMagick (gm) also works.')
    return ['magick']


def prepare_conversion(values, overwrite=False, dry_run=False):
    values = dict(values)
    source = Path(values['input']).expanduser().resolve()
    target = Path(values['output']).expanduser().resolve()
    if source == target or (source.exists() and target.exists() and source.samefile(target)):
        raise CommandError('Input and output must be different files')
    if not dry_run and not source.is_file():
        raise CommandError('Input image does not exist: {}'.format(source))
    if target.exists() and (not overwrite or not target.is_file()):
        raise CommandError('Output exists. Choose another path or use --overwrite for an existing file.')
    if not dry_run and not target.parent.is_dir():
        raise CommandError('Output directory does not exist: {}'.format(target.parent))
    values.update(input=str(source), output=str(target))
    return values


def appstore(args):
    from .saved_commands import execute
    supplied = {name: getattr(args, name) for name in ('input', 'output', 'size', 'background')
                if getattr(args, name) is not None}
    return execute('appstore-resize', supplied, args.dry_run, args.overwrite)


def register_commands(subparsers):
    from .saved_commands import register_commands as register_saved_commands, run_command
    group = subparsers.add_parser('gm', help='Image recipes and saved commands',
                                 description='ImageMagick/GraphicsMagick recipes and named command templates. '
                                             'Omit a subcommand to choose a recipe interactively.')
    group.set_defaults(func=run_command, name=None, values=[], dry_run=False, overwrite=False)
    subs = group.add_subparsers(dest='gm_command')
    register_saved_commands(subs)
    resize = subs.add_parser('appstore', help='Resize to 1284x2778! and flatten onto white by default',
                             description='Force exact dimensions (may stretch the image), then flatten onto a background.')
    resize.add_argument('--input', help='Input image path; offers images from the current directory when omitted')
    resize.add_argument('--output', help='Output image path; prompts when omitted')
    resize.add_argument('--size', help='ImageMagick geometry, defaults to 1284x2778!')
    resize.add_argument('--background', choices=['white', 'black'], help='Background color; offers choices when omitted')
    resize.add_argument('--dry-run', action='store_true')
    resize.add_argument('--overwrite', action='store_true')
    resize.set_defaults(func=appstore)
