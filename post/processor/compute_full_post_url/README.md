# Compute Full url plugin

Compute the full url of a post

## Usage

Add the following snippet to your template to get the full url.

```html
{% if post.meta.full_url %}
{{ post.meta.full_url}}
{% endif %}
```

## Changelog

- 29/12/19 Refactored for new plugin system and python 3.
- 12/27/16 initial version.

## Credits

**Author**: Celine Bursztein
