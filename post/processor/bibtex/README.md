# Bibtex Plugin

Create Bibtex info for a publication based on meta in page

## Usage

Add the following snippet to your template to display the bibtex in the page.

```html
{% if meta.bibtex %}
{{ meta.bibtex}}
{% endif %}
```

## Changelog

- 29/12/19 Refactored for new plugin system and python 3
- 03/04/16 initial version

## Credits

**Author**: Celine Bursztein
