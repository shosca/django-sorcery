Changelog
=========


0.10.2 (2019-11-07)
-----------------------------
- Adding check-manifest in pre-commit (#150) [Miroslav Shubernetskiy]


0.10.1 (2019-08-31)
-------------------
- Drop py2 from setup.py. [Serkan Hosca]


0.10.0 (2019-08-31)
-------------------
- Drop py2 support (#149) [Serkan Hosca]
- Make model meta look like django meta (#148) [Serkan Hosca]
- Simplify column meta info (#147) [Serkan Hosca]
- Fix ModelChoiceField.get_object and make ModelForm inherit
  BaseModelForm (#146) [Serkan Hosca]


0.9.4 (2019-07-14)
------------------
- Fix middleware response return (#143) [Serkan Hosca]
- Use python/black (#141) [Serkan Hosca]


0.9.3 (2019-06-27)
------------------
- Defining test matrix in tox and switchint to tox-travis (#140)
  [Miroslav Shubernetskiy]
- Increase build matrix (#139) [Serkan Hosca]
- Update pre-commit (#138) [Serkan Hosca]


0.9.2 (2019-05-10)
------------------
- Drop trailing zeros on float to decimal conversion (#137) [Serkan
  Hosca]


0.9.1 (2019-04-28)
------------------
- Track committed models (#136) [Serkan Hosca]
- Fix topic. [Serkan Hosca]


0.9.0 (2019-04-23)
------------------
- Trigger configure_mappers before commands (#135) [Serkan Hosca]
- Add migrations on tutorial (#134) [Serkan Hosca]
- Drop sqlalchemy init django dependency (#133) [Serkan Hosca]
- Drop deprecated functions (#132) [Serkan Hosca]
- Raising in middleware on error (#131) [Miroslav Shubernetskiy]
- Allow limit_choices_to to be callable (#130) [Serkan Hosca]
- Add a bunch of docs and fix lint issues (#129) [Serkan Hosca]


0.8.12 (2019-03-15)
-------------------
- Fix field run_validator (#128) [Serkan Hosca]


0.8.11 (2019-02-15)
-------------------
- Fix db operations import from django for db ranges (#127) [Serkan
  Hosca]
- Adding black badge (#126) [Miroslav Shubernetskiy]


0.8.10 (2019-02-06)
-------------------
- Fixing test_site to allow to create test migrations (#125) [Miroslav
  Shubernetskiy]


0.8.9 (2019-02-05)
------------------
- Adding default maxlength/min/maxvalue validators to CharField/IntField
  (#124) [Miroslav Shubernetskiy]
- Include migration mako script (#123) [Serkan Hosca]


0.8.8 (2019-01-29)
------------------
- Raise validation error with field name on coersion (#121) [Serkan
  Hosca]
- Add docs for testing. [Serkan Hosca]


0.8.7 (2019-01-26)
------------------
- Add autogenerate foreign key indexes (#118) [Serkan Hosca]
- Adding Transact testing utility with transact pytest fixture (#119)
  [Miroslav Shubernetskiy]


0.8.6 (2019-01-11)
------------------
- Added signals for create_all and drop_all (#117) [Miroslav
  Shubernetskiy]


0.8.5 (2019-01-10)
------------------
- Fixing composite field validation (#116) [Miroslav Shubernetskiy]


0.8.4 (2019-01-09)
------------------
- Adding OneToOne relationship shortcut (#115) [Miroslav Shubernetskiy]


0.8.3 (2019-01-08)
------------------
- Validate only pre-loaded models (#114) [Miroslav Shubernetskiy]


0.8.2 (2019-01-04)
------------------
- Fix decimal cleaning with thousand separator (#113) [Serkan Hosca]


0.8.1 (2019-01-04)
------------------
- Split choice from enum column info (#111) [Serkan Hosca]
- Regenerate docs. [Serkan Hosca]


0.8.0 (2019-01-02)
------------------
- Refactor coercers (#110) [Serkan Hosca]
- Added django-like filtering support to Query (#108) [Miroslav
  Shubernetskiy]


0.7.7 (2018-12-11)
------------------
- Make statement recording optional (#107) [Serkan Hosca]


0.7.6 (2018-12-10)
------------------
- Add query recording to profiler (#106) [Serkan Hosca]


0.7.5 (2018-12-04)
------------------
- Fix field column naming (#105) [Serkan Hosca]
- Parallel resetdb (#104) [Serkan Hosca]
- Refactor full_clean validation (#103) [Serkan Hosca]


0.7.4 (2018-11-29)
------------------
- Add validation runner and refactor validation (#102) [Serkan Hosca]


0.7.3 (2018-11-28)
------------------
- Fix event deque mutation (#101) [Serkan Hosca]


0.7.2 (2018-11-25)
------------------
- Add more tests (#100) [Serkan Hosca]


0.7.1 (2018-11-24)
------------------
- Fix boolean field constraint name (#99) [Serkan Hosca]
- Meta docs and more meta usage (#98) [Serkan Hosca]
- Nicer meta reprs (#97) [Serkan Hosca]


0.7.0 (2018-11-23)
------------------
- Refactor formfield mapping (#95) [Serkan Hosca]







0.6.18 (2018-11-20)
-------------------
- Added full_clean(recursive=True) for adhoc full tree validation (#96)
  [Miroslav Shubernetskiy]


0.6.17 (2018-11-19)
-------------------
- Implement formfield support in fields (#93) [Serkan Hosca]
- Remove yapf config. [Serkan Hosca]


0.6.16 (2018-11-16)
-------------------
- Fix docs build. [Serkan Hosca]
- Add TimestampField (#74) [Serkan Hosca]


0.6.15 (2018-11-14)
-------------------
- Fix edge case with enum field (#69) [Serkan Hosca]


0.6.14 (2018-11-14)
-------------------
- Refactor autocoercers to allow coerce individual attrs (#68) [Serkan
  Hosca]
- Bump pre-commit check versions (#67) [Serkan Hosca]
- Caching pip and pre-commit. [Miroslav Shubernetskiy]
- Tiny fixup (#65) [Anthony Sottile]


0.6.13 (2018-11-08)
-------------------
- Fixing DecimalField not honoring max_digits and decimal_places (#64)
  [Miroslav Shubernetskiy]









0.6.12 (2018-11-07)
-------------------
- Allowing to set if field is required separately from nullable (#63)
  [Miroslav Shubernetskiy]
- Fix coercer issues (#62) [Serkan Hosca]


0.6.11 (2018-11-05)
-------------------
- Implement autocoerce using form fields (#61) [Serkan Hosca]
- Update lock. [Serkan Hosca]
- Adding more validators (#60) [Miroslav Shubernetskiy]


0.6.10 (2018-10-31)
-------------------
- List primary keys directly (#59) [Serkan Hosca]
- Passing model-defined validators to field_kwargs (#58) [Miroslav
  Shubernetskiy]
- Ignoring schema names in alembic version table for sqlite (#57)
  [Miroslav Shubernetskiy]


0.6.9 (2018-10-17)
------------------
- Not running field validations when column has default value (#56)
  [Miroslav Shubernetskiy]


0.6.8 (2018-10-16)
------------------
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


