from datetime import datetime
from pathlib import Path
from sitefab.plugins import SiteRendering
from sitefab.SiteFab import SiteFab
from sitefab import files
from sitefab.parser.parser import Parser


class Rss(SiteRendering):
    def process(self, unused, site, config):
        template_name = config.template

        config.banner = "%s%s" % (site.config.url, config.banner)
        config.icon = "%s%s" % (site.config.url, config.icon)
        config.logo_svg = "%s%s" % (site.config.url, config.logo_svg)

        # rendering template
        if template_name not in site.jinja2.list_templates():
            return SiteFab.ERROR, "rss", ("template %s not found" %
                                          template_name)
        template = site.jinja2.get_template(str(template_name))

        # custom parser
        parser_tpl_path = Path(config.parser.template_dir)
        config.parser.templates_path = (site.config.root_dir / parser_tpl_path)
        config.parser = Parser.make_config(config.parser)
        parser = Parser(config.parser, site)

        # generating feed
        rss_items = []
        count = 0
        posts = []
        for post in site.posts:
            posts.append(post)

        # sort posts from newer to older
        def k(x):
            return x.meta.creation_date_ts

        posts.sort(key=k, reverse=True)

        for post in posts:
            if (post.meta.hidden or
                ((post.meta.microdata_type != "BlogPosting")  # noqa
                 and (post.meta.microdata_type != "ScholarlyArticle")  # noqa
                 and
                 (post.meta.microdata_type != "PublicationEvent"))):  # noqa
                continue

            # parse the post with a customized parser
            file_content = files.read_file(post.filename)
            parsed_post = parser.parse(file_content)
            # adding the newly generated HTML as RSS
            post.rss = parsed_post.html

            formatted_rss_creation_date = datetime.fromtimestamp(
                int(post.meta.creation_date_ts)).strftime(
                    '%a, %d %b %Y %H:%M:%S -0800')
            if post.meta.update_date_ts:
                formatted_rss_update_date = datetime.fromtimestamp(
                    int(post.meta.update_date_ts)).strftime(
                        '%a, %d %b %Y %H:%M:%S -0800')
            else:
                formatted_rss_update_date = formatted_rss_creation_date

            post.meta.formatted_creation = formatted_rss_creation_date
            post.meta.formatted_update = formatted_rss_update_date

            # size of image
            post.meta.banner_size = site.plugin_data['image_info'][
                post.meta.banner]['file_size']
            post.meta.banner_mimetype = site.plugin_data['image_info'][
                post.meta.banner]['mime_type']
            post.meta.banner_fullurl = "%s%s" % (site.config.url,
                                                 post.meta.banner)

            post.meta.author = post.meta.authors[0].replace(",", "")
            rss_items.append(post)
            count += 1
            if count == config.num_posts:
                break
        if not len(rss_items):
            return (SiteFab.ERROR, "rss", 'no RSS items')

        config.formatted_update = rss_items[0].meta.formatted_update

        try:
            rv = template.render(site=site, rss=config, items=rss_items)
        except Exception as e:
            return (SiteFab.ERROR, "rss", e)

        # output
        path = site.get_output_dir()
        files.write_file(path, 'rss.xml', rv)

        log_info = "template used:%s<br>ouput:%srss.xml" % (template_name,
                                                            path)
        return SiteFab.OK, "rss", log_info
