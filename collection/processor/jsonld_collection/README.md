# Jsonld_collection Plugin

Create Jsonld object based on meta in collection

## Usage

Add the following snippet to your template to display the jsonld of the page.

```html
{% if collection.meta.jsonld %}
{{ collection.meta.jsonld}}
{% endif %}
```

## Changelog

- 29/12/19 Refactored for new plugin system and python 3
- 12/08/16 intial version

## Credits

**Author**: Celine Bursztein, Elie Bursztein
