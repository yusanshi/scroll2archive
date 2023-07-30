import mss
import yaml
import ipdb
import numpy as np
import cv2
import subprocess
import sys
import logging
import argparse
import coloredlogs
from pathlib import Path
from PIL import Image
from PIL import ImageChops
from time import sleep
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('name', type=str, default='default')
args = parser.parse_args()

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG',
                    logger=logger,
                    fmt='%(asctime)s %(levelname)s %(message)s')

with open(Path(__file__).parent / 'config.yaml') as f:
    config = yaml.safe_load(f)


def get_screenshot():
    with mss.mss() as sct:
        sct_img = sct.grab(config['screen'])
    image = np.asarray(sct_img)[:, :, :3]
    image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    return image


def is_same(a, b):
    diff = ImageChops.difference(a, b)
    return diff.getbbox() is None


def show(image):
    if isinstance(image, Image.Image):
        image.show()
    elif isinstance(image, np.ndarray):
        Image.fromarray(image).show()
    else:
        raise ValueError


images = []
max_length = config['max-length']
if max_length <= 0:
    max_length = sys.maxsize
for i in range(max_length):
    logger.info('Taking screenshot')
    image = get_screenshot()
    if len(images) != 0 and is_same(images[-1], image):
        logger.info('Reach the end')
        break

    images.append(image)

    if len(images) == 2:
        images[0].save('images/first.png')
        images[1].save('images/second.png')

    for _ in range(config['next-frame-command-repeat']):
        subprocess.run(config['next-frame-command'], shell=True)

    sleep(config['next-frame-wait-time'])

images_stitched = [np.array(images[0])]
for i in tqdm(range(len(images) - 1)):
    first = np.array(images[i])
    second = np.array(images[i + 1])
    assert first.shape == second.shape

    for overlap in reversed(range(1, first.shape[0])):
        if (first[-overlap:] == second[:overlap]).all():
            if overlap < 200:
                logger.warning(
                    f'Image {i} and {i+1} matched with a small overlap ({overlap}) '
                )
            else:
                logger.info(f'Image {i} and {i+1} matched')
            break
    else:
        logger.error('Not matched')
        ipdb.set_trace()

    # substract first from second, save second
    images_stitched.append(second[overlap:])

image = np.vstack(images_stitched)
Image.fromarray(image).save(f'output/{args.name}.png')

with open('template.html') as f:
    html = f.read()

html = html.replace('[TITLE]', args.name)
html = html.replace('[IMG-SRC]', f"{args.name}.png")
with open(f'output/{args.name}.html', 'w') as f:
    f.write(html)

height = int(image.shape[1] * 297 / 210)  # save A4 paper
start = 0
pages = []
while True:
    if image.shape[0] - start <= height:
        pages.append(image[start:])
        break

    # find the "empty" color at the last half of the page
    average = image[start + height // 2:start + height].mean(axis=(1, 2))
    empty = max(average)
    is_empty = average == empty
    e = is_empty.nonzero()[0][-1]
    s = e
    while s - 1 >= 0 and is_empty[s - 1]:
        s -= 1
    taken = (s + e) // 2 + height // 2
    pages.append(image[start:start + taken])
    start += taken

# padding each page with (255, 255, 255)
for i in range(len(pages)):
    page = np.full((height, image.shape[1], 3), 255, dtype=image.dtype)
    page[:pages[i].shape[0]] = pages[i]
    pages[i] = page

pages = [Image.fromarray(x) for x in pages]
pages[0].save(f'output/{args.name}.pdf',
              save_all=True,
              append_images=pages[1:],
              resolution=200,
              quality=95)
