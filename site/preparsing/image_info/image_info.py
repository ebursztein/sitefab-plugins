import os
from PIL import Image
from tqdm import tqdm
import time
from io import BytesIO

from sitefab.plugins import SitePreparsing
from sitefab.SiteFab import SiteFab
from sitefab import files
from sitefab import utils


class ImageInfo(SitePreparsing):
    """
    Gather image info
    """

    def process(self, unused, site, config):
        log = ""
        errors = False
        plugin_name = "image_info"
        input_dir = site.config.root_dir / config.input_dir
        site_output_dir = site.config.root_dir / site.config.dir.output

        # reading images list
        if not input_dir:
            return (SiteFab.ERROR, plugin_name, "no input_dir specified")

        images = files.get_files_list(input_dir, ["*.jpg", "*.jpeg", "*.png",
                                                  "*.gif"])
        num_images = len(images)

        if num_images == 0:
            return (SiteFab.ERROR, plugin_name, "no images found")

        # processing images
        image_info = {}
        progress_bar = tqdm(total=num_images, unit=' img', leave=False,
                            desc="Generating images stats")
        for image_full_path in images:
            log += "<br><br><h2>%s</h2>" % (image_full_path)
            # Creating needed directories
            img_path, img_filename = os.path.split(image_full_path)

            # File info extraction
            img_name, img_extension = os.path.splitext(img_filename)
            pil_extension_codename, web_extension = utils.get_img_extension_alternative_naming(img_extension)  # noqa

            # directories
            web_path = str(image_full_path).replace(str(site_output_dir), "/")
            web_path = web_path.replace('\\', '/').replace('//', '/')

            # loading
            start = time.time()
            # We need the raw bytes to do the hashing
            # Doing it manually as asking PIL is 10x slower.
            f = open(image_full_path, 'rb')
            raw_image = f.read()
            f.close()

            io_img = BytesIO(raw_image)
            img = Image.open(io_img)
            log += "Image loading time:<i>%s</i><br>" % (round(time.time() -
                                                               start, 3))
            img.close()

            # width and height
            width, height = img.size
            log += "size: %sx%s<br>" % (width, height)

            # hash
            # we use the hash of the content to make sure we regnerate if
            # the image content is different
            img_hash = utils.hexdigest(raw_image)

            # FIXME dominante colors
            image_info[web_path] = {
                "filename": img_filename,       # noqa image filename without path: photo.jpg
                "name": img_name,               # noqa image name without path and extension: photo
                "extension": img_extension,     # noqa image extension: .jpg

                "full_path": image_full_path,   # noqa path on disk with filename: /user/elie/site/content/img/photo.jpg
                "path": img_path,               # noqa path on disk without filename: /user/elie/site/img/
                "web_path": web_path,           # noqa path on the site: /static/img/photo.jpg

                "pil_extension": pil_extension_codename,  # noqa image type in PIl: JPEG
                "mime_type": web_extension,               # noqa mime-type: image/jpeg
                "width": width,
                "height": height,
                "hash": img_hash
            }
            progress_bar.update(1)

        progress_bar.close()

        # reporting data
        site.plugin_data['image_info'] = image_info  # expose images info

        if errors:
            return (SiteFab.ERROR, plugin_name, log)
        else:
            return (SiteFab.OK, plugin_name, log)
