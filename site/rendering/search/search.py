import os
import json
from tabulate import tabulate

from sitefab.plugins import SiteRendering
from sitefab.SiteFab import SiteFab
from sitefab import files


class Search(SiteRendering):

    def process(self, unused, site, config):
        plugin_name = "search"
        js_filename = "search.js"
        json_filename = "search.json"
        output_path_js = config.output_path_js
        output_path_json = config.output_path_json
        num_terms = config.num_terms_per_post

        # log_info = "base javascript: %s<br>ouput:%s%s<br>" % (
        #     js_filename, output_path, js_filename)
        log_info = ""
        # Reading the base JS
        plugin_dir = os.path.dirname(__file__)
        json_file = os.path.join(plugin_dir, json_filename)
        jsondata = files.read_file(json_file)
        jsdata = files.read_file(os.path.join(plugin_dir, js_filename))
        # if not js or len(js) < 10:
        #     err = "Base Javascript:%s not found or too small." % js_file
        #     return (SiteFab.ERROR, plugin_name, err)

        js_posts = {}
        table_data = []
        for post in site.posts:
            terms = [t[0] for t in post.nlp.terms][:num_terms]

            js_post = {
                "id": post.id,
                "template": post.meta.template, 
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
        output_string = json.dumps(js_posts)
        jsondata = jsondata.replace("SEARCH_DOC_PLUGIN_REPLACE", output_string)
        path_json = os.path.join(site.get_output_dir(), output_path_json)
        files.write_file(path_json, json_filename, jsondata)

        path_js = os.path.join(site.get_output_dir(), output_path_js)
        files.write_file(path_js, js_filename, jsdata)
        return (SiteFab.OK, plugin_name, log_info)
