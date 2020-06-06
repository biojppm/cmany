
.PHONY: all test doc deploy package requirements

ALLOW_DIRTY ?= 0
VERSION_RE = cmanyversion_str[ \t]*=[ \t]*"\(.*\)"\(.*\)
VERSION_CURR = $(shell grep 'cmanyversion_str[ \t]*=' setup.py | sed 's:$(VERSION_RE):\1:')
VERSION ?= $(VERSION_CURR)
VERSION_REPL = cmanyversion_str = "$(VERSION)"

all:

requirements:
	pip install -r requirements.txt
	pip install -r requirements_test.txt

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

show_version:
	grep 'cmanyversion_str[ \t]*=' setup.py | sed "s:$(VERSION_RE):\1:"
	@echo "version_curr=$(VERSION_CURR)"
	@echo "version=$(VERSION)"

# examples:
#  make set_version VERSION=1.2.3
#  make set_version VERSION=1.2.3 ALLOW_DIRTY=1
set_version:
	@echo "setting version: $(VERSION_CURR) --> $(VERSION)"
	$(MAKE) doc
	@if [ "$(shell git diff --stat)" != "" ] ; then \
          if [ $(ALLOW_DIRTY) == 1 ] ; then \
	    echo "adding dirty files: $(VERSION_CURR) --> $(VERSION)" ; \
            git diff --stat ; \
            git add -u ; \
          else \
            echo ; echo ; \
	    echo "ERROR: Refuse to set version $(VERSION_CURR) -> $(VERSION): Local directory is dirty" ; \
            exit 1 ; \
	  fi ; \
        fi
	@echo "setting version: $(VERSION)"
	sed 's:$(VERSION_RE):$(VERSION_REPL):' -i setup.py
	git commit -am "version $(VERSION)"
	@echo "tagging commit: $(VERSION)"
	git tag -d $(VERSION) || echo "tag does not exist yet: $(VERSION)"
	git tag -m "version $(VERSION)" $(VERSION)
