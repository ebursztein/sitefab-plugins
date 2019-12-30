# Copy directories

Allows to copy sub-directories from one place to another.
Mostly used to copy assests to the release directory.

## Usage

Specify which directory to copy and its destination in the configuration file

### Configuration

For example

```yaml
copy_dir:
    - enable: True
    copy:
        - "assets/js > release/static/js"
```

will copy the content of the directory *assets/js* to  *release/static/js*

## Changlog

- 29/12/19 Refactored for new plugin system and python 3.
- 12/23/16: Documentation updated to reflect how the plugin work

## Credit

Elie Bursztein
