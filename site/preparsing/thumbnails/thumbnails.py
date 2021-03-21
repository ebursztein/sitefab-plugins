from PIL import Image
from tqdm import tqdm
import time
from diskcache import Cache as dc
from io import BytesIO
from sitefab.image import image_hash, read_image_bytes, convert_image
from sitefab.image import normalize_image_extension, save_image
from sitefab.plugins import SitePreparsing
from sitefab.SiteFab import SiteFab


class Thumbnails(SitePreparsing):
    "Generate thumbnail images"

    def process(self, unused, site, config):
        log = ""
        errors = False
        plugin_name = "thumbnails"
        thumbnail_sizes = config.thumbnail_sizes
        cache_file = site.config.root_dir / site.config.dir.cache / plugin_name

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
        images = site.plugin_data['image_info'].values()

        # processing images
        thumbs = {}
        thumbs_info = {}  # metadata added to image_info for further processing
        num_thumbs = len(images) * len(thumbnail_sizes)
        progress_bar = tqdm(total=num_thumbs,
                            unit=' thumbnails',
                            desc="Generating thumbnails",
                            leave=False)
        for img_info in images:
            thumb = {}
            log += "<br><br><h2>%s</h2>" % (img_info['disk_path'])

            # cache fetch
            start = time.time()
            cached_version = cache.get(img_info['hash'])
            cache_timing['fetching'] += time.time() - start

            # Do we have a cached version else creating it
            if cached_version:
                raw_image = cached_version['raw_image']
            else:
                start = time.time()
                raw_image = read_image_bytes(img_info['disk_path'])
                log += "Image loading time:<i>%s</i><br>" % (round(
                    time.time() - start, 5))
                cached_version = {}
                cached_version['raw_image'] = raw_image

            img = None
            for thumb_width, thumb_height in thumbnail_sizes:
                thumb_key = "%sx%s" % (thumb_width, thumb_height)
                log += "<h3>%s</h3>" % (thumb_key)
                output_filename = "%s-thumb-%s%s" % (
                    img_info['stem'], thumb_key, img_info['extension'])

                output_disk_path = img_info['disk_dir'] / output_filename
                output_web_path = img_info['web_dir'] + output_filename

                thumb[thumb_key] = output_web_path

                # generating image
                start = time.time()
                if thumb_key in cached_version:
                    log += "Cache status: HIT<br>"
                    thumb_io = cached_version[thumb_key]
                else:
                    log += "Cache status: MISS<br>"

                    # parsing image if needed
                    if not img:
                        img = Image.open(BytesIO(raw_image))
                        img_width, img_height = img.size
                        log += "img size: %sx%s<br>" % (img_width, img_height)

                    # scale on the smallest side to maximize quality
                    if img_width < img_height:
                        ratio = img_height / float(img_width)

                        # take into account thumb requested ratio
                        if thumb_width * ratio > thumb_height:
                            ratio2 = thumb_width / float(img_width)
                            tmp_height = int(img_height * ratio2)
                            thumb_img = img.resize((thumb_width, tmp_height),
                                                   Image.LANCZOS)
                        else:
                            ratio2 = thumb_height / float(img_height)
                            tmp_width = int(img_width * ratio2)
                            thumb_img = img.resize((tmp_width, thumb_height),
                                                   Image.LANCZOS)
                    else:
                        ratio = float(img_width) / img_height
                        if thumb_height * ratio > thumb_width:
                            ratio2 = thumb_height / float(img_height)
                            tmp_width = int(img_width * ratio2)
                            thumb_img = img.resize((tmp_width, thumb_height),
                                                   Image.LANCZOS)
                        else:
                            ratio2 = thumb_width / float(img_width)
                            tmp_height = int(img_height * ratio2)
                            thumb_img = img.resize((thumb_width, tmp_height),
                                                   Image.LANCZOS)

                    scaled_width = thumb_img.width
                    scaled_height = thumb_img.height
                    log += "Image scaled to %sx%s<br>" % (scaled_width,
                                                          scaled_height)

                    # cropping
                    top = 0.0
                    bottom = 1.0
                    left = 0.0
                    right = 1.0

                    # cutting the width if needed
                    ratio_width = thumb_width / float(scaled_width)
                    if ratio_width < 1:
                        reduction_factor = 1 - ratio_width
                        # FIXME: potentially compute using interest points
                        baricenter = 0.5
                        center = float(scaled_width) * baricenter
                        left = (center - thumb_width / 2) / float(scaled_width)
                        right = left + ratio_width

                        # correcting potential overflow
                        if left < 0:
                            log += "correcting overflow on the left<br>"
                            right -= left
                            left = 0.0

                        if right > 1:
                            log += "correcting overflwo on the right<br>"
                            left -= (right - 1.0)
                            right = 1.0

                        log += "baricenter:%s, reduction_factor:%s, center:%s,\
                                left:%s, right:%s<br>" % (
                            baricenter, reduction_factor, center, left, right)

                    # cut height
                    ratio_height = thumb_height / float(scaled_height)
                    if ratio_height < 1:
                        reduction_factor = 1 - ratio_height
                        baricenter = 0.5
                        # center as weight by the baricenter
                        center = float(scaled_height) * baricenter
                        top = (center - thumb_height / 2) / \
                            float(scaled_height)
                        bottom = top + ratio_height

                        # correcting for overflow
                        if top < 0:
                            log += "correcting overflow on the top<br>"
                            bottom -= top
                            top = 0.0

                        if bottom > 1:
                            log += "correcting overflow on the bottom<br>"
                            top -= (bottom - 1.0)
                            bottom = 1.0

                    log += "bounding box left: %s, top: %s, right: %s,\
                            bottom: %s<br>" % (left, top, right, bottom)

                    left_pixel = int(scaled_width * left)
                    top_pixel = int(scaled_height * top)
                    right_pixel = int(scaled_width * right)
                    bottom_pixel = int(scaled_height * bottom)

                    # happen when both are at .5
                    if right_pixel - left_pixel != thumb_width:
                        right_pixel += thumb_width - (right_pixel - left_pixel)

                    # happen when both are at .5
                    if bottom_pixel - top_pixel != thumb_height:
                        bottom_pixel += thumb_height - \
                            (bottom_pixel - top_pixel)

                    log += "crop pixel box: left %s, top: %s, right: %s,\
                            bottom: %s<br>" % (left_pixel, top_pixel,
                                               right_pixel, bottom_pixel)

                    thumb_img = thumb_img.crop(
                        [left_pixel, top_pixel, right_pixel, bottom_pixel])
                    log += "thumbnail size: %sx%s<br>" % (thumb_img.width,
                                                          thumb_img.height)

                    thumb_io = convert_image(thumb_img,
                                             img_info['pil_extension'],
                                             webp_lossless=img_info['lossless']
                                             )
                    cached_version[thumb_key] = thumb_io

                    log += "thumbnail generation:%ss<br>" % (round(
                        time.time() - start, 5))

                # write image
                save_image(thumb_io, output_disk_path)

                # write to image_info to allows to make thumbnails
                # responsive
                extension = output_disk_path.suffix
                pil_ext, web_ext = normalize_image_extension(extension)

                # should the image be considered lossless?
                if extension in ['.png', '.gif']:
                    lossless = True
                else:
                    lossless = False

                # FIXME: unify with image info plugibs
                thumbs_info[output_web_path] = {
                    "filename": output_disk_path.name,  # noqa image filename without path: photo.jpg
                    "stem": output_disk_path.stem,  # noqa image name without path and extension: photo
                    "extension": extension,  # noqa image extension: .jpg
                    "disk_path": output_disk_path,  # noqa path on disk with filename: /user/elie/site/content/img/photo.jpg
                    "disk_dir": output_disk_path.parents[0],  # noqa path on disk without filename: /user/elie/site/img/
                    "web_path": output_web_path,  # noqa image url: /static/img/photo.jpg
                    "web_dir": img_info['web_dir'],  # noqa path of the site: /static/img/
                    "pil_extension": pil_ext,  # noqa image type in PIl: JPEG
                    "mime_type": web_ext,  # noqa mime-type: image/jpeg
                    "lossless": lossless,
                    "width": thumb_width,
                    "height": thumb_height,
                    "file_size": output_disk_path.stat().st_size,
                    "hash": image_hash(thumb_io.getvalue())
                }
                progress_bar.update(1)

            # cache storing
            start_set = time.time()
            cache.set(img_info['hash'], cached_version)
            cache_timing["writing"] += time.time() - start_set

            thumbs[img_info['web_path']] = thumb
        cache.close()

        # expose the list of thumbnails images
        site.plugin_data['thumbnails'] = thumbs
        site.plugin_data['image_info'].update(thumbs_info)

        # FIXME: add counter output

        if errors:
            return (SiteFab.ERROR, plugin_name, log)
        else:
            return (SiteFab.OK, plugin_name, log)
