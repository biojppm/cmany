
.PHONY: all test doc deploy package requirements

VERSION = $(shell grep version= setup.py | sed 's:.*version="\(.*\)",:\1:')

all:

test:
	test/run.sh

doc:
	$(MAKE) -C doc text html
	if [ ! -d src/c4/cmany/doc ] ; then mkdir src/c4/cmany/doc ; fi
	cp -favr doc/_build/text/*.txt src/c4/cmany/doc/.

package: doc
	@echo "packaging cmany $(VERSION)"
	rm -vf dist/cmany-$(VERSION)*
	python setup.py sdist bdist_wheel  # needs wheel installed, use make requirements for that

deploy: package
	twine upload dist/cmany-$(VERSION)*

requirements:
	pip install -r requirements.txt
	pip install -r requirements_test.txt
