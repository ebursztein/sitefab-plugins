# SiteFab plugins
List of available plugins

|Name | Description | dependencies|
|-----|:------------|:------------|
| [RSS](/site/rendering/rss/README.md) | RSS | compute_full_post_url |
| [Jsonld](/post/processor/jsonld/README.md) | Generate a Jsonld object for each page based on its meta. | compute_full_post_url |
| [Format timestamp](/templates/filters/format_ts/README.md) | Add custom filter called `format_ts` that allows to format timestamp using standard strttime() syntax. |  |
| [Frozen Images](/site/preparsing/frozen_images/README.md) | Create a frozen version of the images using gaussian blur. | image_info, copy_dir |
| [Read time](/post/processor/read_time/README.md) | Compute how long it will take to read a given post. |  |
| [JS Posts](/site/rendering/js_post/README.md) | Generate a javascript representation of the posts available in javascript via window.posts |  |
| [Sort collections](/collection/processor/sort_collection/README.md) | Sort collections by publication time to allow template to easily display post in chronological order. |  |
| [str_to_list](/templates/filters/str_to_list/README.md) | Transform a string into a list of character |  |
| [Responsive Images](/site/preparsing/responsive_images/README.md) | Create responsive images by using the picture element and creating multiple resolutions images | image_info, copy_dir, image_resizer |
| [Directory copier](/site/preparsing/copy_dir/README.md) | Copy directories |  |
| [Jsonld Collection](/collection/processor/jsonld_collection/README.md) | Compute collection jsonld object. | compute_full_collection_url |
| [Image thumbnails](/site/preparsing/thumbnails/README.md) | Create images thumbnails. | image_info, copy_dir, image_resizer |
| Related Posts | Use LSI to compute related posts. |  |
| [Image resizer](/site/preparsing/image_resizer/README.md) | Resize images that are above a given width | image_info, copy_dir |
| [Sitemap](/site/rendering/sitemap/README.md) | Generate a sitemap. | compute_full_collection_url, compute_full_post_url |
| [Collection full url](/collection/processor/compute_full_collection_url/README.md) | Compute collections fully qualified URLs. |  |
| [Image Info](/site/preparsing/image_info/README.md) | Compute various images metadata. | copy_dir |
| [Post full url](/post/processor/compute_full_post_url/README.md) | Compute each post fully qualified URL and store it in the post.meta under full_url field. |  |
| [Bibtex](/post/processor/bibtex/README.md) | Compute Bibtex info for each publication based on its meta. |  |
| [Search](/site/rendering/search/README.md) | Generate the javascript needed to implement a local search. |  |
| [Autocomplete](/site/rendering/autocomplete/README.md) | Generate a trie that is used to add autocomplete in search box. |  |
