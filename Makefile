
.PHONY: all test doc deploy

all:

test:
	test/run.sh

doc:
	$(MAKE) -C doc text html

deploy:
	_version=$$(grep version= setup.py | sed 's:.*version="\(.*\)",:\1:') \
	&& rm -vf dist/cmany-$$_version* \
	&& python setup.py sdist bdist_wheel \
	&& twine upload dist/cmany-$$_version*
