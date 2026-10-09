"""Deterministic, synthetic media only. Never accepts an existing library root."""
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw


def seed_library(root: Path, count=92):
    root = root.resolve()
    if any(root.iterdir()):
        raise ValueError('Fixture root must be empty')
    gallery = root / 'images/gallery'
    gallery.mkdir(parents=True)
    (root / 'videos').mkdir()
    (root / 'static/thumbnails').mkdir(parents=True)
    for index in range(count):
        width, height = ((240, 360) if index % 3 == 0 else (480, 270))
        image = Image.new('RGB', (width, height), ((index * 47) % 210, (index * 31) % 210, (index * 13) % 210))
        ImageDraw.Draw(image).text((20, 20), f'Fixture {index:04d}', fill='white')
        image.save(gallery / f'image-{index:04d}.jpg')
    Image.new('RGBA', (120, 200), (90, 160, 240, 100)).save(gallery / 'transparent & space.png')
    Image.new('RGB', (300, 120), 'teal').save(gallery / 'static.webp')
    frames = [Image.new('RGB', (160, 100), color) for color in ['red', 'blue']]
    for extension in ['gif', 'webp']:
        frames[0].save(gallery / ('motion.' + extension), save_all=True, append_images=frames[1:], duration=150, loop=0)
    image = Image.new('RGB', (180, 120), 'orange')
    exif = Image.Exif(); exif[274] = 6
    image.save(gallery / 'rotated.jpg', exif=exif)
    # ffmpeg is a required test dependency; missing codecs must fail, not skip.
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
                    '-i', 'color=c=blue:s=320x180:r=24:d=4', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    str(root / 'videos/fixture.mp4')], check=True, timeout=30)
    Image.new('RGB', (320, 180), 'blue').save(root / 'static/thumbnails/fixture.jpg')
    import shutil
    for name in ['related', 'untagged']:
        shutil.copyfile(root / 'videos/fixture.mp4', root / ('videos/' + name + '.mp4'))
        shutil.copyfile(root / 'static/thumbnails/fixture.jpg', root / ('static/thumbnails/' + name + '.jpg'))
