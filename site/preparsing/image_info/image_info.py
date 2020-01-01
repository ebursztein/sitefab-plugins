import time
from io import BytesIO

from PIL import Image
from tabulate import tabulate
from tqdm import tqdm

from sitefab import files
from sitefab.image import normalize_image_extension, read_image_bytes
from sitefab.image import image_hash
from sitefab.plugins import SitePreparsing
from sitefab.SiteFab import SiteFab


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
        log_table = []
        for image_full_path in images:
            row = [image_full_path]

            disk_dir = image_full_path.parents[0]
            img_filename = image_full_path.name
            file_size = image_full_path.stat().st_size
            # File info extraction
            img_stem = image_full_path.stem
            img_extension = image_full_path.suffix
            pil_extension_codename, web_extension = normalize_image_extension(img_extension)  # noqa

            # directories
            web_path = str(image_full_path).replace(str(site_output_dir), "/")
            web_path = web_path.replace('\\', '/').replace('//', '/')
            web_dir = web_path.replace(img_filename, '')

            # loading
            start = time.time()
            raw_image = read_image_bytes(image_full_path)

            io_img = BytesIO(raw_image)
            img = Image.open(io_img)
            # width and height
            width, height = img.size
            row.append("%sx%s" % (width, height))
            img.close()

            # hash
            # we use the hash of the content to make sure we regnerate if
            # the image content is different
            img_hash = image_hash(raw_image)
            row.append(img_hash)

            # FIXME add dominante colors
            image_info[web_path] = {
                "filename": img_filename,       # noqa image filename without path: photo.jpg
                "stem": img_stem,               # noqa image name without path and extension: photo
                "extension": img_extension,     # noqa image extension: .jpg

                "disk_path": image_full_path,   # noqa path on disk with filename: /user/elie/site/content/img/photo.jpg
                "disk_dir": disk_dir,               # noqa path on disk without filename: /user/elie/site/img/

                "web_path": web_path,           # noqa image url: /static/img/photo.jpg
                "web_dir": web_dir,             # noqa path of the site: /static/img/

                "pil_extension": pil_extension_codename,  # noqa image type in PIl: JPEG
                "mime_type": web_extension,               # noqa mime-type: image/jpeg
                "width": width,
                "height": height,
                "file_size": file_size,
                "hash": img_hash
            }
            progress_bar.update(1)
            log_table.append(row)

            # logging
            row.append(round(time.time() - start, 3))

        log += tabulate(log_table, headers=['filename', 'size', 'hash',
                                            'process time'], tablefmt='html')
        progress_bar.close()

        # make image info available to subsequent plugins
        site.plugin_data['image_info'] = image_info  # expose images info

        if errors:
            return (SiteFab.ERROR, plugin_name, log)
        else:
            return (SiteFab.OK, plugin_name, log)
