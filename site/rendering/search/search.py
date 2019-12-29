import os
import json
from tabulate import tabulate

from sitefab.Plugins import SiteRendering
from sitefab.SiteFab import SiteFab
from sitefab import files


class Search(SiteRendering):

    def process(self, unused, site, config):
        plugin_name = "search"
        js_filename = "search.js"
        output_path = config.output_path
        num_terms = config.num_terms

        log_info = "base javascript: %s<br>ouput:%s%s<br>" % (
            js_filename, output_path, js_filename)

        # Reading the base JS
        plugin_dir = os.path.dirname(__file__)
        js_file = os.path.join(plugin_dir, js_filename)
        js = files.read_file(js_file)
        if not js or len(js) < 10:
            err = "Base Javascript:%s not found or too small." % js_file
            return (SiteFab.ERROR, plugin_name, err)

        js_posts = {}
        table_data = []
        for post in site.posts:
            terms = [t[0] for t in post.nlp.terms][:num_terms]

            js_post = {
                "id": post.id,
                "title": post.nlp.clean_fields.title,
                "authors": post.nlp.clean_fields.authors,
                "conference": "%s %s" % (post.nlp.clean_fields.conference_short_name, # noqa
                                         post.nlp.clean_fields.conference_name),  # noqa
                "terms": terms
            }

            js_posts[post.id] = js_post
            table_data.append([js_post['title'], js_post['terms']])

        log_info += tabulate(table_data, tablefmt='html',
                             headers=['title', 'terms'])

        # output
        js = str(js)
        output_string = json.dumps(js_posts)
        js = js.replace("SEARCH_DOC_PLUGIN_REPLACE", output_string)
        path = os.path.join(site.get_output_dir(), output_path)
        files.write_file(path, js_filename, js)
        return (SiteFab.OK, plugin_name, log_info)
