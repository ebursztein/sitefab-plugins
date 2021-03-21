from multiprocessing import Pool
from itertools import repeat

from PIL import Image
from tqdm import tqdm
import time
from diskcache import Cache as dc
from io import BytesIO
from tabulate import tabulate

from sitefab.image import save_image, convert_image, read_image_bytes
from sitefab.image import image_hash
from sitefab.plugins import SitePreparsing
from sitefab.SiteFab import SiteFab


def resize_image(data):
    img_info, site_data = data
    img_path = img_info['web_path']
    log_str = ""
    width = 0
    height = 0
    file_size = 0
    file_hash = ""
    cache_file, max_width, jpeg_quality, webp_quality = site_data
    cache = dc(cache_file)

    process_start_ts = time.time()
    row = [img_info['disk_path']]

    if img_info['width'] < max_width:
        log_str = "Width %s < max_width: %s skipping" % (img_info['width'],
                                                         max_width)
        return img_path, log_str, row, width, height, file_size, file_hash

    # cache fetch
    # start = time.time()
    cached_version = cache.get(img_info['hash'])

    # Do we have a cached version else creating it
    if cached_version:
        raw_image = cached_version['raw_image']
        row.append(0)
    else:
        start = time.time()
        raw_image = read_image_bytes(img_info['disk_path'])
        row.append((round(time.time() - start, 5)))

        cached_version = {}
        cached_version['raw_image'] = raw_image
        cached_version['max_width'] = -1

    # Is the cached version have the right size?
    if cached_version['max_width'] == max_width:
        row.append('HIT')
        resized_img_io = cached_version['resized_img']
        resized_img = Image.open(resized_img_io)
    else:
        row.append('MISS')
        img = Image.open(BytesIO(raw_image))
        img_width, img_height = img.size

        ratio = max_width / float(img_width)
        new_height = int(img_height * ratio)
        resized_img = img.resize((max_width, new_height),
                                 Image.LANCZOS)
        img.close()

        extension_codename = img_info['pil_extension']
        resized_img_io = convert_image(resized_img, extension_codename,
                                       jpeg_quality=jpeg_quality,
                                       webp_quality=webp_quality,
                                       webp_lossless=img_info['lossless'])

        cached_version['max_width'] = max_width
        cached_version['resized_img'] = resized_img_io

    # writing to disk
    start = time.time()
    save_image(resized_img_io, img_info['disk_path'])

    # update image info to reflect new image info
    # it is mandatory to update the hash as other plugins rely on
    # it to detect change
    width, height = resized_img.size
    file_size = resized_img_io.getbuffer().nbytes
    file_hash = image_hash(resized_img_io.getbuffer())
    # cache storing
    cache.set(img_info['hash'], cached_version)
    cache.close()
    row.append(round(time.time() - process_start_ts, 2))
    return img_path, log_str, row, width, height, file_size, file_hash


class ImageResizer(SitePreparsing):
    "Resize images"

    def process(self, unused, site, config):
        log = ""
        errors = False
        plugin_name = "image_resizer"
        cache_file = site.config.root_dir / site.config.dir.cache / plugin_name

        # using the list of images from image_info
        if 'image_info' not in site.plugin_data:
            log += 'image_info not found in plugin_data. No images?'
            return (SiteFab.ERROR, plugin_name, log)

        # processing images
        images = site.plugin_data['image_info'].values()
        progress_bar = tqdm(total=len(images), unit=' image',
                            desc="Resizing images", leave=False)

        log_table = []
        cpu_count = config.threads
        p = Pool(cpu_count)

        site_data = (cache_file, config.max_width, config.jpeg_quality,
                     config.webp_quality)

        # multithreaded loop
        for img_path, log_str, row, width, height, file_size, file_hash in p.imap_unordered(resize_image, zip(images, repeat(site_data))):  # noqa
            log += log_str
            log_table.append(row)
            if width != 0:
                site.plugin_data['image_info'][img_path]['width'] = width  # noqa
                site.plugin_data['image_info'][img_path]['height'] = height  # noqa
                site.plugin_data['image_info'][img_path]['file_size'] = file_size  # noqa
                site.plugin_data['image_info'][img_path]['hash'] = file_hash  # noqa
            progress_bar.update(1)
        p.close()
        p.join()
        progress_bar.close()

        log += tabulate(log_table, tablefmt='html')
        if errors:
            return (SiteFab.ERROR, plugin_name, log)
        else:
            return (SiteFab.OK, plugin_name, log)
