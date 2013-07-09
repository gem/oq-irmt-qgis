UI_FILES = ui_process_manager.py

RESOURCE_FILES = # resources_rc.py

default: compile

compile: $(UI_FILES) $(RESOURCE_FILES)

%_rc.py : %.qrc
	pyrcc4 -o $*_rc.py  $<

%.py : %.ui
	pyuic4 -o $@ $<

%.qm : %.ts
	lrelease $<
