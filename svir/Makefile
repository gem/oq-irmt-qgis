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

# PY_FILES = irmt.py select_input_layers_dialog.py __init__.py attribute_selection_dialog.py transformation_dialog.py select_sv_variables_dialog.py settings_dialog.py projects_manager_dialog.py visualize_oq_output.py

UI_FILES = ui/ui_select_input_layers.py ui/ui_attribute_selection.py ui/ui_transformation.py ui/ui_select_sv_variables.py ui/ui_settings.py ui/ui_weight_data.py ui/ui_calculate_iri.py ui/ui_upload_metadata.py ui/ui_upload_settings.py ui/ui_download_layer.py ui/ui_projects_manager_dialog.py ui/ui_visualize_oq_output.py

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
	VERSION=HEAD
endif

default: compile

compile: $(UI_FILES) $(COMPILED_RESOURCE_FILES)

%_rc.py : %.qrc $(RESOURCE_SRC)
	pyrcc4 -o $*_rc.py  $<

%.py : %.ui
	pyuic4 -o $@ $<

%.qm : %.ts
	lrelease $<

test: compile transcompile
	@echo
	@echo "----------------------"
	@echo "Regression Test Suite"
	@echo "----------------------"

	@# Preceding dash means that make will continue in case of errors
	@-export PYTHONPATH=`pwd`:$(PYTHONPATH); \
		export QGIS_DEBUG=0; \
		export QGIS_LOG_FILE=/dev/null; \
		nosetests -s -v --with-id --with-coverage --cover-package=. test\
		3>&1 1>&2 2>&3 3>&- || true
	@echo "----------------------"
	@echo "If you get 'no module...' errors, try sourcing"
	@echo "the helper script we have provided first then run make test."
	@echo "e.g. source ../scripts/run-env-linux.sh <path to qgis install>; make test"
	@echo "----------------------"

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
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
	mkdir -p $(PLUGINNAME)/help/build; rm -r $(PLUGINNAME)/help/build/html; cp -r help/build/html $(PLUGINNAME)/help/build/html
	mkdir -p $(PLUGINNAME)/apidoc/build; rm -r $(PLUGINNAME)/apidoc/build/html; cp -r apidoc/build/html $(PLUGINNAME)/apidoc/build/html
	zip -r $(PLUGINNAME).zip $(PLUGINNAME)/help/build/html
	zip -r $(PLUGINNAME).zip $(PLUGINNAME)/apidoc/build/html
	zip --delete $(PLUGINNAME).zip $(PLUGINNAME)/test/\* $(PLUGINNAME)/help/source/\* $(PLUGINNAME)/apidoc/source/\*
	rm -r $(PLUGINNAME)/
	echo "Created package: $(PLUGINNAME).zip"

package_no_compile:
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)

upload_doc: doc
	@echo
	@echo "--------------------------------------"
	@echo "Uploading documentation to GEM server."
	@echo "--------------------------------------"
	VERSION=$(VERSION) ../scripts/doc_upload.sh

upload: package upload_doc
	@echo
	@echo "-------------------------------------"
	@echo "Uploading plugin to QGIS Plugin repo."
	@echo "-------------------------------------"
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

tag:
ifndef NEW_VERSION
	$(error NEW_VERSION is not defined)
endif
	$(eval VERSION := $(NEW_VERSION))
	@echo
	@echo "------------------------------------------------"
	@echo "Tagging version $(VERSION).                   "
	@echo "------------------------------------------------"
	@git tag -a $(VERSION) -m"Tagging $(VERSION)"

release: tag upload
	@git push origin --tags
	@echo
	@echo "------------------------------------------------"
	@echo "Released version $(VERSION).                   "
	@echo "------------------------------------------------"


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
doc: build_manual build_apidoc

build_manual:
	@echo
	@echo "-----------------------------"
	@echo "Building manual using sphinx."
	@echo "-----------------------------"
	cd help; make latexpdf html

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
