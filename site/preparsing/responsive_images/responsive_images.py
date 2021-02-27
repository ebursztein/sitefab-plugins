import pprint
import random
import time
from io import BytesIO
from itertools import repeat
from multiprocessing import Pool
from tabulate import tabulate

from diskcache import Cache as dc
from PIL import Image
from tqdm import tqdm

from sitefab.image import read_image_bytes, normalize_image_extension
from sitefab.image import convert_image, save_image
from sitefab.plugins import SitePreparsing
from sitefab.SiteFab import SiteFab


def generate_thumbnails(bundle):
    "generate thumbnails for a set of images"
    images, params = bundle
    num_errors = 0
    log = ''
    # minimal width that make sense to cache.
    MIN_CACHED_SIZE = params['min_image_width']

    start = time.time()
    # According to the doc, cache need to be open in each thread
    cache = dc(params['cache_file'])
    cache_timing = {
        'opening': time.time() - start,
        'fetching': 0,
        'writing': 0
    }

    results = []  # returned info
    log_table = []
    
    for image_info in images:
        start_process_ts = time.time()
        log_row = [image_info['disk_path']]
        resize_list = {}
        if image_info['extension'] in ['PNG', 'GIF']:
            webp_lossless = True
        else:
            webp_lossless = False

        # extensions
        requested_extensions = set()
        for f in params['requested_format_list']:
            requested_extensions.add(f)
        requested_extensions.add(image_info['extension'])

        # loading image in memory
        start = time.time()
        width = image_info['width']
        height = image_info['height']
        raw_image = read_image_bytes(image_info['disk_path'])
        img = Image.open(BytesIO(raw_image))

        # loading cache
        if width >= MIN_CACHED_SIZE:
            start = time.time()
            cached_value = cache.get(image_info['hash'])
            cache_timing['fetching'] += time.time() - start

            # cache miss!
            if not cached_value:
                log_row.append('MISS')
                cached_value = {}
            else:
                log_row.append('HIT')
        else:
            cached_value = {}
            log_row.append('SKIP')

        # add default images
        s = "%s %sw" % (image_info['web_path'], image_info['width'])
        resize_list[image_info['mime_type']] = [s]

        for requested_width in params['requested_width_list']:
            if requested_width > width:
                continue

            ratio = float(requested_width) / width
            requested_height = int(height * ratio)  # preserve the ratio

            for extension in requested_extensions:
                pil_extension_codename, web_extension = normalize_image_extension(extension)  # noqa

                if not pil_extension_codename:
                    # unknown extension marking the image as error and skipping
                    num_errors += 1
                    continue

                if web_extension not in resize_list:
                    resize_list[web_extension] = []

                # filename for the resized image
                output_filename = "%s.%s%s" % (image_info['stem'],
                                               requested_width,
                                               extension)

                output_disk_path = image_info['disk_dir'] / output_filename
                output_web_path = image_info['web_dir'] + output_filename

                # cache lookup
                cache_secondary_key = "%s-%s" % (pil_extension_codename,
                                                 requested_width)
                if cache_secondary_key in cached_value:
                    img_io = cached_value[cache_secondary_key]
                else:
                    # generate resized image as it is not in the cache.
                    resized_img = img.resize((requested_width,
                                              requested_height), Image.LANCZOS)

                    img_io = convert_image(resized_img,
                                           pil_extension_codename,
                                           webp_lossless=webp_lossless)

                    # store in the cache
                    cached_value[cache_secondary_key] = img_io

                # writing to disk
                save_image(img_io, output_disk_path)

                # add to resize list
                s = "%s %sw" % (output_web_path, requested_width)
                resize_list[web_extension].append(s)
                log_table.append(log_row)

        # caching results - we write each time to avoid the cache pruning
        if width > MIN_CACHED_SIZE:
            start = time.time()
            cache.set(image_info['hash'], cached_value)
            cache_timing["writing"] += time.time() - start

        if 'opening' in cache_timing:
            log += "<h3>Cache stats</h3>"
            log += tabulate([
                ['opening', cache_timing['opening']],
                ['fetching', cache_timing['fetching']],
                ['writing', cache_timing['writing']]
            ], tablefmt='html')

        results.append([image_info['web_path'], resize_list, width,
                        log, num_errors, image_info['hash']])

        log_row.append(round(time.time() - start_process_ts, 2))
        log_table.append(log_row)

    log += tabulate(log_table, headers=['file', 'process_time'],
                    tablefmt='html')
    if cache:
        cache.close()
    return results


class ResponsiveImages(SitePreparsing):
    """
    Create responsive images
    """

    def process(self, unused, site, config):
        log = ""
        errors = False
        plugin_name = "responsive_images"
        cache_file = site.config.root_dir / site.config.dir.cache / plugin_name

        if config.additional_formats:
            requested_format_list = config.additional_formats
        else:
            requested_format_list = []

        params = {
            "site_output_dir": site.config.dir.output,
            "requested_width_list": config.thumbnail_size,
            "requested_format_list": requested_format_list,
            "cache_file": cache_file,
            "min_image_width": config.cache_min_image_width
        }

        resize_images = {}  # store the results
        images = list(site.plugin_data['image_info'].values())
        progress_bar = tqdm(total=len(images), unit=' images',
                            desc="Generating responsive_images", leave=False)

        # ensuring that the load will be uniformly split among the threads
        random.shuffle(images)

        batch_size = 20
        batches = [images[x: x + batch_size] for x in range(0, len(images),
                                                            batch_size)]

        bundles = zip(batches, repeat(params))
        results = []

        # allows non-multithread by setting threads to 1.
        if site.config.threads > 1:
            log += "Using multithreading: %s threads<br>" % (
                site.config.threads)
            tpool = Pool()
            for data in tpool.imap_unordered(generate_thumbnails, bundles):
                results.extend(data)
                progress_bar.update(batch_size)
            tpool.close()
            tpool.join()
        else:
            for bundle in bundles:
                results.extend(generate_thumbnails(bundle))
                progress_bar.update(batch_size)

        for result in results:
            # be extra sure that windows path don't messup the thing
            web_path = result[0]
            resize_list = result[1]
            width = result[2]
            log += result[3]
            num_errors = result[4]
            img_hash = result[5]
            if num_errors:
                errors = True

            # store all the resized images info
            srcsets = {}
            allsizes = {}
            for webformat, srcset in resize_list.items():
                if webformat == "image/webp":
                    key = 'webp'
                else:
                    key = 'original'

                for img in srcset:
                    img_data = img.split(" ")
                    size = img_data[1][:-1]
                    img_path = img_data[0]
                    if size not in allsizes:
                        allsizes[size] = {}
                    if key not in allsizes[size]:
                        allsizes[size][key] = {}
                    allsizes[size][key] = img_path
                    if key == 'original':
                        last = img_path
                srcsets[key] = {
                    'srcset': ", ".join(srcset),
                    'format': webformat
                }

            resize_images[web_path] = {"srcsets": srcsets,
                                       "media": '(max-width: %spx)' % width,
                                       "sizes": '(max-width: %spx)' % width,
                                       "hash": img_hash,
                                       "allsizes": allsizes,
                                       "last": last
                                       }
        log += pprint.pformat(resize_images)
        # configuring the parser to make use of the resize images
        # expose the list of resized images
        site.plugin_data['responsive_images'] = resize_images
        if errors:
            return (SiteFab.ERROR, plugin_name, log)
        else:
            return (SiteFab.OK, plugin_name, log)
