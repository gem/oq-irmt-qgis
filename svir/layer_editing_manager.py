class LayerEditingManager(object):
    def __init__(self, layer, message, debug=False):
        self.layer = layer
        self.message = message
        self.debug = debug

    def __enter__(self):
        self.layer.startEditing()
        self.layer.beginEditCommand(self.message)
        if self.debug:
            print "BEGIN", self.message

    def __exit__(self, type, value, traceback):
        self.layer.endEditCommand()
        self.layer.commitChanges()
        self.layer.updateExtents()
        if self.debug:
            print "END", self.message
