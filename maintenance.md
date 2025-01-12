
# PyPi upload

Package a Python Package/ version bump See: https://packaging.python.org/tutorials/packaging-projects/

1. Update `setup.py` to new version number
2. Commit this change
3. Tag and upload

## Install dependencies:
```bash
pip install --upgrade setuptools
pip install --upgrade wheel
pip install --upgrade twine
# pip install --upgrade bleach html5lib  # some versions do not work
pip install --upgrade bump2version
```

`bump2version` takes care to increase the version number, create the commit and tag.

To add the wheels for Windows to the release, trigger the wheels_windows pipeline on Github (via the web UI or by creating a version tag) and download the wheels into the dist/ directory.

```bash
bump2version --verbose --tag patch  # major, minor or patch
python setup.py sdist  # bdist_wheel  # It is difficult to get bdist_wheel working with binary files
git push origin --tags
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
twine upload dist/*
```
