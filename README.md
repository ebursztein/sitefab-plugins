# SiteFab plugins
List of available plugins

|Name | Description | dependencies|
|-----|:------------|:------------|
| [Image thumbnails](tree/master/site/preparsing/thumbnails/README.md) | Create images thumbnails. | image_resizer, copy_dir, image_info |
| [Image Info](tree/master/site/preparsing/image_info/README.md) | Compute various images metadata. | copy_dir |
| [Autocomplete](tree/master/site/rendering/autocomplete/README.md) | Generate a trie that is used to add autocomplete in search box. |  |
| [Collection full url](tree/master/collection/processor/compute_full_collection_url/README.md) | Compute collections fully qualified URLs. |  |
| [Frozen Images](tree/master/site/preparsing/frozen_images/README.md) | Create a frozen version of the images using gaussian blur. | copy_dir, image_info |
| [Post full url](tree/master/post/processor/compute_full_post_url/README.md) | Compute each post fully qualified URL and store it in the post.meta under full_url field. |  |
| [Jsonld Collection](tree/master/collection/processor/jsonld_collection/README.md) | Compute collection jsonld object. | compute_full_collection_url |
| [str_to_list](tree/master/templates/filters/str_to_list/README.md) | Transform a string into a list of character |  |
| [Sitemap](tree/master/site/rendering/sitemap/README.md) | Generate a sitemap. | compute_full_post_url, compute_full_collection_url |
| [Directory copier](tree/master/site/preparsing/copy_dir/README.md) | Copy directories |  |
| [Format timestamp](tree/master/templates/filters/format_ts/README.md) | Add custom filter called `format_ts` that allows to format timestamp using standard strttime() syntax. |  |
| Related Posts | Use LSI to compute related posts. |  |
| [Read time](tree/master/post/processor/read_time/README.md) | Compute how long it will take to read a given post. |  |
| [Search](tree/master/site/rendering/search/README.md) | Generate the javascript needed to implement a local search. |  |
| [Sort collections](tree/master/collection/processor/sort_collection/README.md) | Sort collections by publication time to allow template to easily display post in chronological order. |  |
| [Responsive Images](tree/master/site/preparsing/responsive_images/README.md) | Create responsive images by using the picture element and creating multiple resolutions images | image_resizer, copy_dir, image_info |
| [RSS](tree/master/site/rendering/rss/README.md) | RSS | compute_full_post_url |
| [JS Posts](tree/master/site/rendering/js_post/README.md) | Generate a javascript representation of the posts available in javascript via window.posts |  |
| [Bibtex](tree/master/post/processor/bibtex/README.md) | Compute Bibtex info for each publication based on its meta. |  |
| [Jsonld](tree/master/post/processor/jsonld/README.md) | Generate a Jsonld object for each page based on its meta. | compute_full_post_url |
| [Image resizer](tree/master/site/preparsing/image_resizer/README.md) | Resize images that are above a given width | copy_dir, image_info |
