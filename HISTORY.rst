Changelog
=========


0.6.8 (2018-10-16)
-----------------------------
- Rename OPTIONS to ALCHEMY_OPTIONS (#55) [Serkan Hosca]
- Relock (#54) [Serkan Hosca]


0.6.7 (2018-10-03)
------------------
- Allowing to customize whether to log or add headers in profiler (#53)
  [Miroslav Shubernetskiy]


0.6.6 (2018-09-27)
------------------
- Merge pull request #51 from shosca/fields. [Serkan Hosca]
- Django-like fields. [Serkan Hosca]


0.6.5 (2018-09-21)
------------------
- Merge pull request #52 from shosca/engine_options. [Serkan Hosca]
- Support for more engine options in url. [Miroslav Shubernetskiy]


0.6.4 (2018-09-18)
------------------
- Merge pull request #49 from shosca/deserialize. [Serkan Hosca]
- Added tests for relation_info. [Miroslav Shubernetskiy]







- Using local_remote_pairs_for_identity_key to backfill models relations
  in deserialize. [Miroslav Shubernetskiy]
- Try backpopulate by fk's on deserialize. [Serkan Hosca]
- Deserialize model instance. [Serkan Hosca]
- Merge pull request #50 from shosca/refactor-fieldmapper. [Serkan
  Hosca]
- Refactor field mapping. [Serkan Hosca]


0.6.3 (2018-09-04)
------------------
- Merge pull request #48 from shosca/url. [Serkan Hosca]
- Only popping custom engine parameters from url. [Miroslav
  Shubernetskiy]


0.6.2 (2018-08-31)
------------------
- Merge pull request #47 from shosca/signals. [Serkan Hosca]
- Fix profile middleware bug by lazily attaching signals. [Miroslav
  Shubernetskiy]


0.6.1 (2018-08-28)
------------------
- Merge pull request #46 from shosca/query-options. [Serkan Hosca]
- Add get query options. [Serkan Hosca]
- Merge pull request #45 from shosca/profiler-middleware. [Serkan Hosca]
- Start/stop in profiler middleware. [Serkan Hosca]


0.6.0 (2018-08-25)
------------------
- Merge pull request #40 from shosca/alembic. [Serkan Hosca]
- Fixing import issue after rebase. [Miroslav Shubernetskiy]
- Fixing test_sql not expecting "Running migrations..." messages.
  [Miroslav Shubernetskiy]
- Not printing "Running migrations..." message when --sql is used.
  [Miroslav Shubernetskiy]
- Removing import hook. instead adding alembic_app_created signal.
  [Miroslav Shubernetskiy]
- Checking if migrations are present before configuring alembic.
  [Miroslav Shubernetskiy]
- Renaming makemigrations to revision and importing migrations.__init__
  [Miroslav Shubernetskiy]
- Matching parameters to alembic and minor improvements. [Miroslav
  Shubernetskiy]
- Added --no-color to all ./manage.py sorcery command in tests.
  [Miroslav Shubernetskiy]
- Added SQLAlchemy.models_registry. [Miroslav Shubernetskiy]
- Add alembic support. [Serkan Hosca]
- Added prefix to composite columns constraint names. [Miroslav
  Shubernetskiy]
- Added way to customize metadata options via config. (#43) [Miroslav
  Shubernetskiy]
- Run tests on pg (#42) [Serkan Hosca]


0.5.5 (2018-07-28)
------------------
- Fix scoped session proxying (#41) [Serkan Hosca]


0.5.4 (2018-07-19)
------------------
- Adding profiler with middleware and pytest plugin (#39) [Miroslav
  Shubernetskiy]











0.5.3 (2018-07-18)
------------------
- Multi db transaction (#36) [Serkan Hosca]


0.5.2 (2018-07-17)
------------------
- Added sane CompositeBase.__bool__ which checks all attributes (#38)
  [Miroslav Shubernetskiy]


0.5.1 (2018-07-16)
------------------
- Allowing to specify via env var some engine options (#37) [Miroslav
  Shubernetskiy]







0.5.0 (2018-07-05)
------------------
- Add namespaced command (#35) [Serkan Hosca]
- Fix unique validator and add declare last signal (#34) [Serkan Hosca]


0.4.13 (2018-07-03)
-------------------
- Fix unique column validator (#32) [Serkan Hosca]
- Refactored all relations to separate module. also moving declare_first
  as signal (#31) [Miroslav Shubernetskiy]


0.4.12 (2018-06-30)
-------------------
- Fix packaging. [Serkan Hosca]


0.4.11 (2018-06-30)
-------------------
- Snakify table names (#30) [Serkan Hosca]


0.4.10 (2018-06-28)
-------------------
- Add Unique validator (#29) [Serkan Hosca]


0.4.9 (2018-06-26)
------------------
- Fix init kwargs (#28) [Serkan Hosca]
- Add composite cloning and serialization (#27) [Serkan Hosca]


0.4.8 (2018-06-23)
------------------
- Add docs (#26) [Serkan Hosca]
- Wire up form to do model clean (#25) [Serkan Hosca]


0.4.7 (2018-06-23)
------------------
- Drop drf dependency (#24) [Serkan Hosca]


0.4.6 (2018-06-22)
------------------
- Added CompositeField and all related goodies (#23) [Miroslav
  Shubernetskiy]



























0.4.5 (2018-06-14)
------------------
- Merge pull request #22 from shosca/config_refactor. [Serkan Hosca]
- Pass along kwargs with custom sqla class. [Serkan Hosca]


0.4.4 (2018-06-13)
------------------
- Merge pull request #21 from shosca/config_refactor. [Serkan Hosca]
- Grab only custom sqla class from config. [Serkan Hosca]


0.4.3 (2018-06-09)
------------------
- Merge pull request #20 from shosca/config_refactor. [Serkan Hosca]
- Remove engine hacks and refactor config for custom sqla class. [Serkan
  Hosca]


0.4.2 (2018-06-04)
------------------
- 0.4.2. [Serkan Hosca]
- Merge pull request #19 from shosca/inlineformset. [Serkan Hosca]
- Inline formsets. [Serkan Hosca]


0.4.1 (2018-05-31)
------------------
- 0.4.1. [Serkan Hosca]
- Merge pull request #18 from shosca/docs. [Serkan Hosca]
- Add more docs for viewsets. [Serkan Hosca]


0.4.0 (2018-05-31)
------------------
- 0.4.0. [Serkan Hosca]
- Add basic viewset support. [Serkan Hosca]


0.3.3 (2018-05-21)
------------------
- 0.3.3. [Serkan Hosca]
- Merge pull request #15 from shosca/middleware-logger. [Serkan Hosca]
- Add middleware logger. [Serkan Hosca]
- Merge pull request #14 from shosca/docs. [Serkan Hosca]
- More docs. [Serkan Hosca]
- Merge pull request #13 from shosca/docs. [Serkan Hosca]
- Add a test_site and docs. [Serkan Hosca]


0.3.2 (2018-05-17)
------------------
- 0.3.2. [Serkan Hosca]
- Merge pull request #12 from shosca/middleware. [Serkan Hosca]
- Refactor middleware. [Serkan Hosca]


0.3.1 (2018-05-17)
------------------
- 0.3.1. [Serkan Hosca]
- Merge pull request #11 from shosca/shortcuts. [Serkan Hosca]
- Add get_list_or_404 shortcut. [Serkan Hosca]
- Add get_object_or_404 shortcut. [Serkan Hosca]


0.3.0 (2018-05-16)
------------------
- 0.3.0. [Serkan Hosca]
- Merge pull request #10 from shosca/url-refactory. [Serkan Hosca]
- Refactor url generation and allow query settings. [Serkan Hosca]


0.2.8 (2018-05-14)
------------------
- 0.2.8. [Serkan Hosca]
- Merge pull request #9 from shosca/refactor-enum. [Serkan Hosca]
- Refactor enum field. [Serkan Hosca]


0.2.7 (2018-05-12)
------------------
- 0.2.7. [Serkan Hosca]
- Merge pull request #8 from shosca/enum-field. [Serkan Hosca]
- Enum field fixes. [Serkan Hosca]


0.2.6 (2018-05-09)
------------------
- 0.2.6. [Serkan Hosca]
- Merge pull request #7 from shosca/middeware-signals. [Serkan Hosca]
- Add middleware signals. [Serkan Hosca]


0.2.5 (2018-05-09)
------------------
- 0.2.5. [Serkan Hosca]
- Merge pull request #6 from shosca/lazy-init. [Serkan Hosca]
- Lazy create engine. [Serkan Hosca]


0.2.4 (2018-05-08)
------------------
- 0.2.4. [Serkan Hosca]
- Merge pull request #5 from shosca/field-map. [Serkan Hosca]
- Use mro in python_type field mapping. [Serkan Hosca]


0.2.3 (2018-05-08)
------------------
- 0.2.3. [Serkan Hosca]


0.2.2 (2018-05-08)
------------------
- 0.2.2. [Serkan Hosca]
- Merge pull request #4 from shosca/app-label-template. [Serkan Hosca]
- Use app config label in template name. [Serkan Hosca]


0.2.1 (2018-05-07)
------------------
- 0.2.1. [Serkan Hosca]
- Merge pull request #3 from shosca/transaction. [Serkan Hosca]
- Add transaction tests. [Serkan Hosca]
- Merge pull request #2 from shosca/proxy. [Serkan Hosca]
- Refactor scoped session proxy. [Serkan Hosca]
- Merge pull request #1 from shosca/field-mapping. [Serkan Hosca]
- More field mapping coverage. [Serkan Hosca]


0.2.0 (2018-05-07)
------------------

Fix
~~~
- Model choice field iterator. [Serkan Hosca]

Other
~~~~~
- 0.2.0. [Serkan Hosca]
- Increase test coverage. [Serkan Hosca]
- Increase test coverage. [Serkan Hosca]


0.1.1 (2018-05-05)
------------------
- Fix meta test. [Serkan Hosca]


0.1.0 (2018-05-05)
------------------
- Initial commit. [Serkan Hosca]


