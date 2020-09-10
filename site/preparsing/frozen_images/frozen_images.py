from PIL import Image, ImageFilter
from tqdm import tqdm
import time
import base64
from diskcache import Cache as dc
from io import BytesIO
from tabulate import tabulate

from sitefab.image import read_image_bytes, convert_image, save_image
from sitefab.plugins import SitePreparsing
from sitefab.SiteFab import SiteFab


class FrozenImages(SitePreparsing):
    """
    Create frozen images
    """

    def process(self, unused, site, config):
        log = ""
        errors = False
        plugin_name = "frozen_images"
        frozen_width = 42
        cache_file = site.config.root_dir / site.config.dir.cache / plugin_name
        blur_value = 2

        # opening cache
        start = time.time()
        cache = dc(cache_file)
        cache_timing = {
            'opening': time.time() - start,
            'fetching': 0,
            'writing': 0
        }

        # using the list of images from image_info
        if 'image_info' not in site.plugin_data:
            log += 'image_info not found in plugin_data. No images?'
            return (SiteFab.ERROR, plugin_name, log)

        # processing images
        images = site.plugin_data['image_info'].values()
        frozen_images = {}
        progress_bar = tqdm(total=len(images), unit=' frozen thumb',
                            desc="Generating frozen images", leave=False)
        log_table = []
        for img_info in images:
            start_process_time_ts = time.time()
            row = [img_info['disk_path']]

            output_filename = "%s.frozen%s" % (img_info['stem'],
                                               img_info['extension'])

            output_disk_path = img_info['disk_dir'] / output_filename
            output_web_path = img_info['web_dir'] + output_filename

            # cache fetch
            start = time.time()
            cached_value = cache.get(img_info['hash'])
            cache_timing['fetching'] += time.time() - start

            # generating image
            start = time.time()
            if cached_value:
                row.append('HIT')
                img_io = cached_value
            else:
                row.append('MISS')
                # loading
                start = time.time()
                raw_image = read_image_bytes(img_info['disk_path'])

                img = Image.open(BytesIO(raw_image))

                # resize
                width, height = img.size
                ratio = float(frozen_width) / width
                frozen_height = int(height * ratio)  # preserve the ratio
                resized_img = img.resize((frozen_width, frozen_height))

                # convert to make blur working (avoid saving thus)
                resized_img = convert_image(resized_img, 'JPEG',
                                            return_as_bytesio=False)

                # blur
                resized_img = resized_img.filter(
                    ImageFilter.GaussianBlur(blur_value))

                # convert
                img_io = convert_image(resized_img, 'JPEG')

            # cache storing
            start_set = time.time()
            cache.set(img_info['hash'], img_io)
            cache_timing["writing"] += time.time() - start_set

            "IMG manipulation:%ss<br>" % (time.time() - start)

            # writing to disk
            start = time.time()
            save_image(img_io, output_disk_path)

            s = base64.b64encode(img_io.getvalue())
            # this is required due to python3 using b'
            s = str(s).replace("b'", '').replace("'", '')
            img_base64 = "data:image/jpg;base64,%s" % (s)
            # print(img_base64[:64])
            frozen_images[img_info['web_path']] = {
                "url": output_web_path,
                "base64": img_base64,
            }

            row.append('<img src="%s">' % img_base64)
            row.append(start_process_time_ts)
            progress_bar.update(1)
            log_table.append(row)

        # expose the list of resized images
        site.plugin_data['frozen_images'] = frozen_images

        log += tabulate(log_table, tablefmt='html')
        progress_bar.close()
        cache.close()

        if errors:
            return (SiteFab.ERROR, plugin_name, log)
        else:
            return (SiteFab.OK, plugin_name, log)
