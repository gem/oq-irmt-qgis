# Copyright (c) 2013-2015, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

#################################################
# Edit the following to match your sources lists
#################################################
#Add iso code for any locales you want to support here (space separated)
LOCALES = it

PLUGINNAME = svir

EXTRAS = resources/start_plugin_icon.png metadata.txt

COMPILED_RESOURCE_FILES = resources_rc.py

PEP8EXCLUDE=pydev,resources_rc.py,conf.py,third_party,ui

#################################################
# Normally you would not need to edit below here
#################################################

RESOURCE_SRC=$(shell grep '^ *<file' resources.qrc | sed 's@</file>@@g;s/.*>//g' | tr '\n' ' ')


HELP = help/build/html

PLUGIN_UPLOAD = ../scripts/plugin_upload.py

QGISDIR=.qgis2

ifndef VERSION
	VERSION="v$(shell grep 'version=' metadata.txt | cut -d '=' -f 2)"
endif

default: compile

compile: $(COMPILED_RESOURCE_FILES)

%_rc.py : %.qrc $(RESOURCE_SRC)
	pyrcc5 -o $*_rc.py  $<

%.py : %.ui
	pyuic5 -o $@ $<

%.qm : %.ts
	lrelease $<

deploy: compile doc transcompile
	@echo
	@echo "------------------------------------------"
	@echo "Deploying plugin to your .qgis2 directory."
	@echo "------------------------------------------"
	# The deploy  target only works on unix like operating system where
	# the Python plugin directory is located at:
	# $HOME/$(QGISDIR)/python/plugins
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(COMPILED_UI_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(COMPILED_RESOURCE_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vfr i18n $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vfr $(HELP) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/help

# The dclean target removes compiled python files from plugin directory
# also deletes any .svn entry
dclean:
	@echo
	@echo "-----------------------------------"
	@echo "Removing any compiled python files."
	@echo "-----------------------------------"
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname "*.pyc" -delete
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname ".svn" -prune -exec rm -Rf {} \;

derase:
	@echo
	@echo "-------------------------"
	@echo "Removing deployed plugin."
	@echo "-------------------------"
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

zip: deploy dclean
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	# The zip target deploys the plugin and creates a zip file with the deployed
	# content. You can then upload the zip file on http://plugins.qgis.org
	rm -f $(PLUGINNAME).zip
	cd $(HOME)/$(QGISDIR)/python/plugins; zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)

package: compile doc
	# Create a zip package of the plugin named $(PLUGINNAME).zip.
	# This requires use of git (your plugin development directory must be a
	# git repository).
	# To use, pass a valid commit or tag as follows:
	#   make package VERSION=Version_0.3.2
	@echo
	@echo usage: make package VERSION=HEAD
	@echo or: make package VERSION=Version_0.3.2
	@echo or: make package VERSION=YOUR_TAG_OR_COMMIT
	@echo
	@echo "------------------------------------"
	@echo "Exporting plugin to zip package.	"
	@echo "------------------------------------"
	rm -f $(PLUGINNAME)/$(PLUGINNAME).zip
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip HEAD
	# to save more space, we can use /ebook instead of /printer (but it would reduce the resolution of images)
	gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=resized-irmt.pdf help/build/latex/irmt.pdf
	# NOTE: assuming that _downloads contains a single folder with a unique name (otherwise you must identify the right folder and delete the others manually)
	mv -f resized-irmt.pdf $(shell ls -d help/build/html/_downloads/*/)irmt.pdf
	mkdir -p $(PLUGINNAME)/help/build; rm -r $(PLUGINNAME)/help/build/html; cp -r help/build/html $(PLUGINNAME)/help/build/html;
	# mkdir -p $(PLUGINNAME)/apidoc/_build; rm -r $(PLUGINNAME)/apidoc/_build/html; cp -r apidoc/_build/html $(PLUGINNAME)/apidoc/_build/html
	zip -r $(PLUGINNAME).zip $(PLUGINNAME)/help/build/html
	# zip -r $(PLUGINNAME).zip $(PLUGINNAME)/apidoc/_build/html
	zip --delete $(PLUGINNAME).zip $(PLUGINNAME)/test/\* $(PLUGINNAME)/help/source/\*
	rm -r $(PLUGINNAME)/
	echo "Created package: $(PLUGINNAME).zip"

package_no_compile:
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip HEAD

upload_doc: doc
	@echo
	@echo "--------------------------------------"
	@echo "Uploading documentation to GEM server."
	@echo "--------------------------------------"
	VERSION=$(VERSION) ../scripts/doc_upload.sh

upload_plugin: package tag
	@echo
	@echo "-------------------------------------"
	@echo "Uploading plugin to QGIS Plugin repo."
	@echo "-------------------------------------"
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

tag:
	@echo
	@echo "------------------------------------------------"
	@echo "Tagging version $(VERSION).                   "
	@echo "------------------------------------------------"
	@git tag -a $(VERSION) -m"Tagging $(VERSION)"

tag_push:
	@git push origin --tags

# FIXME: the automatic upload to the QGIS repo does not work
# release: upload_plugin upload_doc tag_push
release: package tag tag_push upload_doc
	@echo
	@echo "-----------------------------------------------------------"
	@echo "Released version $(VERSION).                               "
	@echo "FIXME: svir.zip must be uploaded to the QGIS repo manually "
	@echo "-----------------------------------------------------------"

transup:
	@echo
	@echo "------------------------------------------------"
	@echo "Updating translation files with any new strings."
	@echo "------------------------------------------------"
	@chmod +x ../scripts/update-strings.sh
	@../scripts/update-strings.sh $(LOCALES)

transcompile:
	@echo
	@echo "----------------------------------------"
	@echo "Compiled translation files to .qm files."
	@echo "----------------------------------------"
	@chmod +x ../scripts/compile-strings.sh
	@../scripts/compile-strings.sh $(LOCALES)

transclean:
	@echo
	@echo "------------------------------------"
	@echo "Removing compiled translation files."
	@echo "------------------------------------"
	rm -f i18n/*.qm

clean:
	@echo
	@echo "------------------------------------"
	@echo "Removing uic and rcc generated files"
	@echo "------------------------------------"
	rm $(COMPILED_UI_FILES) $(COMPILED_RESOURCE_FILES)

# build documentation with sphinx
doc: build_manual  # build_apidoc

build_manual:
	@echo
	@echo "---------------------------------------"
	@echo "Building the manual inside QGIS docker."
	@echo "---------------------------------------"
	cd ../scripts; ./make_doc.sh
	# NOTE: it would be better if we could let the docker create files owned by
	#       the user launching the script instead of making them owned by root
	sudo chown -R $(USER) help/build/

build_apidoc:
	@echo
	@echo "-----------------------------------------"
	@echo "Building code documentation using sphinx."
	@echo "-----------------------------------------"
	cd apidoc; make html

pylint:
	@echo
	@echo "-----------------"
	@echo "Pylint violations"
	@echo "-----------------"
	@pylint --reports=n --rcfile=pylintrc . || true
	@echo
	@echo "----------------------"
	@echo "If you get a 'no module...' errors, try sourcing"
	@echo "the helper script we have provided first then run make pylint."
	@echo "e.g. source scripts/run-env-linux.sh <path to qgis install>; make pylint"
	@echo "----------------------"


# Run pep8 style checking
#http://pypi.python.org/pypi/pep8
pep8:
	@echo
	@echo "-----------"
	@echo "PEP8 issues"
	@echo "-----------"
	@pep8 --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128 --exclude $(PEP8EXCLUDE) . || true
	@echo "-----------"
	@echo "Ignored in PEP8 check:"
	@echo $(PEP8EXCLUDE)
