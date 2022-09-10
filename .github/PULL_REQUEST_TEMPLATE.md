**Merge checklist:**
- [ ] Any new requirements are in the right place (do **not** manually modify the `requirements/*.txt` files)
    - `make upgrade && make requirements` have been run to regenerate requirements
- [ ] `./manage.py makemigrations` has been run
    - Checkout the [Database Migration](https://openedx.atlassian.net/wiki/spaces/AC/pages/23003228/Everything+About+Database+Migrations) Confluence page for helpful tips on creating migrations.
    - *Note*: This **must** be run if you modified any models.
      - It may or may not make a migration depending on exactly what you modified, but it should still be run.
- [ ] [Version](https://github.com/openedx/taxonomy-connector/blob/master/taxonomy/__init__.py) bumped
- [ ] [Changelog](https://github.com/openedx/taxonomy-connector/blob/master/CHANGELOG.rst) record added

**Post merge:**
- [ ] Tag pushed and a new [version](https://github.com/openedx/taxonomy-connector/releases) released
    - *Note*: Assets will be added automatically. You just need to provide a tag (should match your version number) and title and description.
- [ ] After versioned build finishes in [GitHub Actions](https://github.com/openedx/taxonomy-connector/actions), verify version has been pushed to [PyPI](https://pypi.org/project/taxonomy-connector/)
    - Each step in the release build has a condition flag that checks if the rest of the steps are done and if so will deploy to PyPi.
    (so basically once your build finishes, after maybe a minute you should see the new version in PyPi automatically (on refresh))
- [ ] PR created in [course-discovery](https://github.com/openedx/course-discovery) to upgrade dependencies (including taxonomy-connector)
    - This **must** be done after the version is visible in PyPi as `make upgrade` in course-discovery will look for the latest version in PyPi.