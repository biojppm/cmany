
.PHONY: all test doc deploy

all:

test:
	test/run.sh

doc:
	$(MAKE) -C doc text html
	if [ ! -d src/c4/cmany/doc ] ; then mkdir src/c4/cmany/doc ; fi
	cp -favr doc/_build/text/*.txt src/c4/cmany/doc/.

deploy:
	_version=$$(grep version= setup.py | sed 's:.*version="\(.*\)",:\1:') \
	&& rm -vf dist/cmany-$$_version* \
	&& python setup.py sdist bdist_wheel \
	&& twine upload dist/cmany-$$_version*
