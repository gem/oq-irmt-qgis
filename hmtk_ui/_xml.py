from xml.etree import ElementTree


def registry_to_xml(registry, name):
    def add_property(el, property_name, subel, text):
        prop = ElementTree.Element(el, "property")
        prop.set("name", property_name)
        sub = ElementTree.SubElement(prop, subel)
        sub.text = text
    root = ElementTree.Element("widget")
    root.set("class", "QWidget")
    root.set("name", "stacked_widget_%s" % name)
    layout = ElementTree.SubElement(root, "layout")
    layout.set("class", "QGridLayout")
    layout.set("name", "gridLayout_%s" % name)
    item = ElementTree.SubElement(layout, "item")
    layout = ElementTree.SubElement(item, "layout")
    layout.set("class", "QFormLayout")
    layout.set("name", "%s_form" % name)
    add_property(
        layout, "fieldGrowthPolicy",
        "enum", "QFormLayout::FieldsStayAtSizeHint")
    for i, (field_name, method) in enumerate(registry.items(), 1):
        # the label
        item = ElementTree.SubElement(layout, "item")
        item.set("row", str(i))
        item.set("column", "0")
        widget = ElementTree.SubElement(item, "widget")
        widget.set("class", "QLabel")
        widget.set("name", "%s_%s_label" % (name, field_name))
        add_property(widget, "text", "string", name)

        # the input
        item = ElementTree.SubElement(layout, "item")
        item.set("row", str(i))
        item.set("column", "1")
        widget = ElementTree.SubElement(item, "widget")
        widget.set("class", input_class_for(method))
        widget.set("name", "%s_%s_input" % (name, field_name))
        add_property(widget, "text", "string", name)
