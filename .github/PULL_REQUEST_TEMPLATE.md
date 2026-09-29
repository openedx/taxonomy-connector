**Merge checklist:**
- [ ] Any new requirements are in the right place (do **not** manually modify the `requirements/*.txt` files)
    - `make upgrade && make requirements` have been run to regenerate requirements
- [ ] `./manage.py makemigrations` has been run
    - Checkout the [Database Migration](https://openedx.atlassian.net/wiki/spaces/AC/pages/23003228/Everything+About+Database+Migrations) Confluence page for helpful tips on creating migrations.
    - *Note*: This **must** be run if you modified any models.
      - It may or may not make a migration depending on exactly what you modified, but it should still be run.

**Post merge:**
- [ ] PR created in [course-discovery](https://github.com/openedx/course-discovery) to upgrade dependencies (including taxonomy-connector)
    - This **must** be done after the version is visible in PyPi as `make upgrade` in course-discovery will look for the latest version in PyPi.