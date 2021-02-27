import json
from collections import defaultdict
from pathlib import Path

from tabulate import tabulate

from sitefab import files
from sitefab.plugins import SiteRendering
from sitefab.SiteFab import SiteFab


class Autocomplete(SiteRendering):

    # @profile
    def process(self, unused, site, config):
        plugin_name = "autocomplete"
        json_filename = "autocomplete.json"
        js_filename = "autocomplete.js"
        # configuration
        output_path_js = config.output_path_js
        output_path_json = config.output_path_json
        num_suggestions = config.num_suggestions
        excluded_terms = config.excluded_terms

        log_info = ""
        # log_info = "base javascript: %s<br>ouput:%s%s" % (
        #     js_filename, output_path_js, js_filename)

        # Reading the base JS
        plugin_dir = Path(__file__).parent
        json_file = plugin_dir / json_filename
        jsondata = files.read_file(json_file)
        
        js_file = plugin_dir / js_filename
        jsdata = files.read_file(js_file)
      
        term_post_frequency = defaultdict(int)
        term_score = defaultdict(float)
        for post in site.posts:
            # authors
            for author in post.nlp.clean_fields.authors:
                term_post_frequency[author] += 1
                term_score[author] += 1  # ensure authors always first
                for part in author.split(' '):
                    if len(part) < 2:
                        continue
                    term_post_frequency[part] += 1
                    term_score[part] += 1

            # title terms
            for term in post.nlp.title_terms:
                if term in excluded_terms:
                    continue
                term_post_frequency[term[0]] += 1
                term_score[term[0]] += term[1] * 2

            # other terms
            for term in post.nlp.terms:
                if term in excluded_terms:
                    continue
                term_post_frequency[term[0]] += 1
                term_score[term[0]] += term[1]

        output = []
        log_info += "num of terms considered: %s<br>" % len(term_score)

        top_terms = sorted(term_score, key=term_score.get, reverse=True)
        for term in top_terms[:num_suggestions]:
            score = term_score[term]
            post_frequency = term_post_frequency[term]
            output.append([term, post_frequency, score])

        # log results
        log_info += tabulate(output,
                             headers=['term', 'post frequency', 'score'],
                             tablefmt='html')

        # replacing placeholder with computation result
        output_string = json.dumps(output)
        jsondata = jsondata.replace("AUTOCOMPLETE_PLUGIN_REPLACE", output_string)

        # output
        path_js = site.get_output_dir() / output_path_js
        path_json = site.get_output_dir() / output_path_json
        log_info += "<br> output directory for js: %s" % path_js
        log_info += "<br> output directory for json: %s" % path_json
        # write js data file
        files.write_file(path_js, js_filename, jsdata)
        # write code file
        files.write_file(path_json, json_filename, jsondata)

        return (SiteFab.OK, plugin_name, log_info)
