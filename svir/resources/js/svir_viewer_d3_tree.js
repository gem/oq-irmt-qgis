/*
   Copyright (c) 2013, GEM Foundation.

      This program is free software: you can redistribute it and/or modify
      it under the terms of the GNU Affero General Public License as
      published by the Free Software Foundation, either version 3 of the
      License, or (at your option) any later version.

      This program is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU Affero General Public License for more details.

      You should have received a copy of the GNU Affero General Public License
      along with this program.  If not, see <https://www.gnu.org/licenses/agpl.html>.
*/

    // const is not supported by all the browsers, so we are using var instead
    var CIRCLE_SCALE = 30;
    var MIN_CIRCLE_SIZE = 0.001;

    $(document).ready(function() {
        //  Project definition weight dialog
        $("#projectDefWeightDialog").dialog({
            autoOpen: false,
            height: 500,
            width: 500,
            modal: true
        });
        //  Dialog to set up a new node to insert into the project definition
        $("#projectDefNewNodeDialog").dialog({
            autoOpen: false,
            height: 200,
            width: 500,
            modal: true
        });
    });

    ////////////////////////////////////////////
    //// Project Definition Collapsible Tree ///
    ////////////////////////////////////////////

    function loadPD(selectedPDef, qt_page) {
        var tooltipdiv = d3.select("#projectDefDialog").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        var DEFAULT_OPERATOR = qt_page.DEFAULT_OPERATOR;
        var OPERATORS = qt_page.OPERATORS.split(';');
        var ACTIVE_LAYER_NUMERIC_FIELDS = qt_page.ACTIVE_LAYER_NUMERIC_FIELDS.split(';');
        var NODE_TYPES = qt_page.NODE_TYPES.split(';');
        var node_types_dict = {};
        for (var i = 0; i < NODE_TYPES.length; i++) {
            var keyval = NODE_TYPES[i];
            var keyvalsplit = keyval.split(':');
            var type_key = keyvalsplit[0];
            var type_name = keyvalsplit[1];
            node_types_dict[type_key] = type_name;
        }

        var margin = {top: 20, right: 120, bottom: 20, left: 60},
            width = 960 - margin.right - margin.left,
            height = 800 - margin.top - margin.bottom;

        var i = 0,
            duration = 750,
            root;

        var tree = d3.layout.tree()
            .size([height, width]);

        var diagonal = d3.svg.diagonal()
            .projection(function(d) { return [d.y, d.x]; });


        function createSpinner(id, weight, name, field) {
            pdTempSpinnerIds.push("spinner-"+id);
            $('#projectDefWeightDialog').dialog("open");
            if (field === undefined) {
                $('#projectDefWeightDialog').append(
                    '<p><label for="spinner'+id+'">'+name+': </label><input id="spinner-'+id+'" name="spinner" value="'+weight+'"></p>');
            } else {
                $('#projectDefWeightDialog').append(
                    '<p><label for="spinner'+id+'">'+name+'('+field+'): </label><input id="spinner-'+id+'" name="spinner" value="'+weight+'"></p>');
            }
            $(function() {
                $("#spinner-"+id).width(100).spinner({
                    min: 0,
                    max: 100,
                    step: 0.01,
                    numberFormat: "n"
                });
            });
        }

        var nodeEnter;

        function operatorSelect(pdOperator){
            $('#projectDefWeightDialog')
                .append('<br/><label for="operator">Operator: </label>')
                .append('<select id="operator">'+ operatorOptions() + '</select>');
            //TODO use selectmenu when the bug there is fixed9?
            //$(selector).selectmenu()
            //$(selector).prop('selectedIndex', 4)
            $('#operator').val(pdOperator);
        }

        function operatorOptions(){
            var options = '';
            for (var i = 0; i < OPERATORS.length; i++) {
                var c = OPERATORS[i];
                if (c == DEFAULT_OPERATOR){
                    options += '<option value="' + c + '" selected="selected">' + c + '</option>';
                }
                else{
                    options += '<option value="' + c + '">' + c + '</option>';
                }
            }
            return options;
        }


        function fieldSelect(node){
            // TODO: Add more stuff to the node
            $('#projectDefNewNodeDialog').empty();
            $('#projectDefNewNodeDialog').dialog("open");
            $('#projectDefNewNodeDialog')
                .append('<br/><label for="field">Field: </label>')
                .append('<select id="field">'+ fieldOptions(node) + '</select>')
                .append('<br/><label for="name">Name: </label>')
                .append('<input id="newNodeName" type="text" name="newNodeName">');

            //TODO use selectmenu when the bug there is fixed9?
            //$(selector).selectmenu()
            //$(selector).prop('selectedIndex', 4)
            // $('#field').val(node.field);
            
            // By default, set the name to be equal to the fieldname selected
            var defaultName = $('#field').val();
            $('#newNodeName').val(defaultName);

            $('#field').on('change', function() {
                $('#newNodeName').val(this.value);
            });
        }

        function getRootNode(node){
            if (node.parent === undefined) {
                return node;
            } else {
                return getRootNode(node.parent);
            }
        }

        function listTakenFields(node) {
            var takenFields = [];
            if (typeof node.field !== "undefined") {
                takenFields.push(node.field);
            }
            // Recursive search inside the children of the node
            if (typeof node.children !== "undefined"){
                for (var i = 0; i < node.children.length; i++){
                    var takenInChild = listTakenFields(node.children[i]);
                    takenFields.push.apply(takenFields, takenInChild);
                }
            }
            return takenFields;
        }

        function fieldOptions(pdData) {
            var options = '';
            // Retrieve the root (TODO: we should keep the root node visible and use that here)
            var rootNode = getRootNode(pdData);
            // Get a list of fields that are already in the Project Definition
            var takenFields = listTakenFields(rootNode);
            for (var i = 0; i < ACTIVE_LAYER_NUMERIC_FIELDS.length; i++) {
                var field_name = ACTIVE_LAYER_NUMERIC_FIELDS[i];
                // Add only numeric fields in the active layer that are not already in the PD
                if (takenFields.indexOf(field_name) === -1){
                    options += '<option value="' + field_name + '">' + field_name + '</option>';
                }
            }
            return options;
        }

        function cancelAddNodeButton(pdData) {
            // $('#projectDefNewNodeDialog').dialog("open");
            $('#projectDefNewNodeDialog').append(
                '<br/><br/><button type="button" id="cancel-add-node-button">Cancel</button>'
            );
            $('#cancel-add-node-button').click(
                function(){
                    // $('.ui-icon-closethick').click();
                    // Remove the new node (the last child, just created) from the children
                    // FIXME: Currently, if you press cancel twice or more, it keeps removing children
                    pdData.children.splice(pdData.children.length - 1, 1);
                    updateD3Tree(pdData);
                    $('#projectDefNewNodeDialog').dialog("close");
                }
            );

        }

        function addNodeButton(pdData) {
            // pdId = typeof pdId !== 'undefined' ? pdId : false;
            // $('#projectDefNewNodeDialog').dialog("open");
            $('#projectDefNewNodeDialog').append(
                '<button type="button" id="add-node-button">Add node</button>'
            );
            // alert('Created the "add node" button');
            $('#add-node-button').click(
                function(){
                    // $('.ui-icon-closethick').click();
                    if ($('#field').length !== 0) {
                        var field = $('#field').val();
                        var newNodeName = $('#newNodeName').val();
                        updateNode(pdData, field, newNodeName);
                        // updateNode(pdData, pdData.id, field);
                    }
                    $('#projectDefNewNodeDialog').dialog("close");
                }
            );
        }

        function updateButton(pdId){
            // FIXME: Are we using pdId?
            pdId = typeof pdId !== 'undefined' ? pdId : false;
            $('#projectDefWeightDialog').append('<br/><br/><button type="button" id="update-button">Update</button>');
            $('#update-button').click(
                function(){
                    updateButtonClicked();
                }
            );
            $('#projectDefWeightDialog').append('<button type="button" id="updateandclose-button">Update and close</button>');
            $('#updateandclose-button').click(function(){
                updateButtonClicked();
                $('#projectDefWeightDialog').dialog("close");
            });

            function updateButtonClicked() {
                pdTempWeights = [];
                pdTempWeightsComputed = [];

                // Get the values of the spinners
                for (var i = 0; i < pdTempSpinnerIds.length; i++) {
                    pdTempWeights.push($('#'+pdTempSpinnerIds[i]).val());
                }

                // Adjust the values into percentages
                pdTempWeights = pdTempWeights.map(Number);
                var totalWeights = 0;
                $.each(pdTempWeights,function() {
                    totalWeights += this;
                });

                for (var i = 0; i < pdTempWeights.length; i++) {
                    var tempMath = Math.floor((pdTempWeights[i] * 100) / totalWeights);
                    pdTempWeightsComputed.push(tempMath / 100);
                }

                // Update the results back into the spinners and to the d3.js chart
                for (var i = 0; i < pdTempSpinnerIds.length; i++) {
                    $('#'+pdTempSpinnerIds[i]).spinner("value", pdTempWeightsComputed[i]);
                }

                // Update the json with new values
                for (var i = 0; i < pdTempWeightsComputed.length; i++) {
                    updateTreeBranch(pdData, [pdTempIds[i]], pdTempWeightsComputed[i]);
                }

                if ($('#operator').length !== 0) {
                    var operator = $('#operator').val();
                    updateOperator(pdData, pdId, operator);
                }

                nodeEnter.remove("text");
                updateD3Tree(pdData);
            }
        }

        function findTreeBranchInfo(pdData, pdName, pdField, node) {
            // Find out how many elements are in tree branch

            // PAOLO: Create spinners for nodes sharing the same parent
            if (node.parent === pdData) {
                pdTempIds.push(pdData.id);
                createSpinner(pdData.id, pdData.weight, pdData.name, pdData.field);
            }

            (pdData.children || []).forEach(function(child) {
                findTreeBranchInfo(child, [pdName], pdField, node);
            });


        }

        function updateTreeBranch(pdData, id, pdWeight) {
            if (id.some(function(currentValue) {
                return (pdData.id == currentValue);
            })) {
                pdData.weight = pdWeight;
            }

            (pdData.children || []).forEach(function(currentItem) {
                updateTreeBranch(currentItem, id, pdWeight);
            });
        }

        function updateOperator(pdData, id, pdOperator) {
            if (pdData.id == id){
                pdData.operator = pdOperator;
            }

            (pdData.children || []).forEach(function(currentItem) {
                updateOperator(currentItem, id, pdOperator);
            });
        }

        function updateNode(pdData, field, name) {
            // alert('Inside updateNode');
            pdData.field = field;
            pdData.name = name;
            updateD3Tree(pdData);
            // alert(pdData.name);
        }

        function updateNodeOLD(pdData, id, pdField) {
            if (pdData.id == id){
                pdData.field = pdField;
                // FIXME Let the user type a name for the field
                pdData.name = pdField;
            }

            (pdData.children || []).forEach(function(currentItem) {
                updateNode(currentItem, id, pdField);
            });
        }

        var svg = d3.select("#projectDefDialog").append("svg")
            .attr("width", width + margin.right + margin.left)
            .attr("height", height + margin.top + margin.bottom)
            .attr("id", "project-definition-svg")
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        d3.json(selectedPDef, function() {
            data = JSON.parse(selectedPDef);
            root = data;
            root.x0 = height / 2;
            root.y0 = 0;

            //root.children.forEach(collapse);
            updateD3Tree(root);
        });

        d3.select(self.frameElement).style("height", "800px");


        function updateD3Tree(source) {
            // Compute the new tree layout.
            var nodes = tree.nodes(root).reverse(),
                links = tree.links(nodes);

            // Normalize for fixed-depth.
            nodes.forEach(function(d) { d.y = d.depth * 180; });

            // Update the nodes…
            var node = svg.selectAll("g.node")
                .data(nodes, function(d) { return d.id || (d.id = ++i); });

            // Enter any new nodes at the parent's previous position.
            nodeEnter = node.enter().append("g")
                .attr("class", "node")
                .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; });

            nodeEnter.append("circle")
                .attr("r", 1e-6)
                .on("mouseover", function(d) {
                    var info = d.name;
                    tooltipdiv .transition()
                        .duration(500)
                        .style("opacity", 0.9);
                    tooltipdiv .html(info)
                        .style("left", (d3.event.pageX) + "px")
                        .style("top", (d3.event.pageY - 28) + "px");
                    })
                .on("mouseout", function(d) {
                    tooltipdiv .transition()
                        .duration(500)
                        .style("opacity", 0);
                })
                .on("click", function(d) {
                    // TODO: Open dialog to select one of the fields of the current layer
                    // and build the newNode depending on it and on the siblings
                    // NOTE: Only fields that are not already in the tree should be selectable
                    // By default, assign equal weights to the new node and to its siblings
                    pdData = data; // PAOLO: What's data?
                    var nodeType;
                    switch (d.type) {
                        case undefined:
                            // alert("You clicked a node with undefined type");
                            return false;
                        case node_types_dict.RI:
                            nodeType = node_types_dict.RISK_INDICATOR;
                            break;
                        case node_types_dict.SV_INDICATOR:
                            // alert("You clicked a node with type " + d.type);
                            // alert("You can't add new nodes to primary indicator nodes");
                            return false;
                        case node_types_dict.SV_THEME:
                            // alert("You clicked a node with type " + d.type);
                            nodeType = node_types_dict.SV_INDICATOR;
                            break;
                        default:
                            // alert("You clicked a node with type " + d.type);
                            return false;
                    }
                    if (d.children === undefined) {
                        d.children = [];
                    }
                    var avgWeight = 1.0 / (d.children.length + 1);
                    for (var i = 0; i < d.children.length; i++) {
                        d.children[i].weight = avgWeight;
                    }
                    var newNode = {
                        // field and name are assigned through a dialog,
                        // after the node is created
                        'parent': d.name,
                        'weight': avgWeight,
                        'type': nodeType,
                        'x0': d.x,
                        'y0': d.y
                    };
                    // Add node, appending it to the node that has been clicked
                    (d.children || (d.children = [])).push(newNode);
                    // alert(JSON.stringify(source));
                    var builtNode = d.children[d.children.length - 1];
                    updateD3Tree(builtNode);
                    // updateD3Tree(pdData);
                    // Let the user choose one of the available fields and set the name
                    $('#projectDefNewNodeDialog').dialog("open");
                    fieldSelect(d);
                    // pdData = d.children[d.children.length - 1];
                    // alert(pdData.id);
                    // alert(builtNode.id);
                    // pdData.transition();
                    // addNodeButton(pdData);
                    cancelAddNodeButton(d);
                    addNodeButton(builtNode);
                });

            nodeEnter.append("text")
                // .attr("class", (function(d) { return "level-" + d.level; }))
                //.attr("id", (function(d) { return d.name; }))
                .attr("id", "svg-text")
                .attr("value", (function(d) { return d.weight; }))
                .attr("x", function(d) { return -(d.weight * CIRCLE_SCALE + 5); })
                .attr("dy", function(d) {
                    // NOTE are x and y swapped?
                    // set te text above or below the node depending on the
                    // parent position
                    if (typeof d.parent != "undefined" && d.x > d.parent.x){
                        return "2em";
                    }
                    return "-1em";
                })
                .attr("text-anchor", function(d) { return "end"; })
                .text(function(d) {
                    return d.name;
                })
                .style("fill-opacity", 1e-6)
                .on("click", function(d) {
                    pdField = d.field;
                    pdName = d.name;
                    pdData = data;
                    pdWeight = d.weight;
                    pdTempSpinnerIds = [];
                    pdTempIds = [];
                    $('#projectDefWeightDialog').empty();
                    if (d.parent){
                        findTreeBranchInfo(pdData, [pdName], pdField, d);
                        var pdParentOperator = d.parent.operator? d.parent.operator : DEFAULT_OPERATOR;
                        d.parent.operator = pdParentOperator;
                        operatorSelect(pdParentOperator);
                        pdId = d.parent.id;
                        updateButton(pdId);
                    }
                    else{
                        //we clicked the root element
                    }
                });

            nodeEnter.append("text")
                .text(function(d) {
                    if (d.children){
                        var operator = d.operator? d.operator : DEFAULT_OPERATOR;
                        d.operator = operator;
                        return operator;
                    }
                })
                .attr("x", function(d) { return d.weight * CIRCLE_SCALE + 15; })
                .on("click", function(d) {
                    pdName = d.children[0].name;
                    pdData = data;
                    pdParent = d.name;
                    pdParentField = d.field;
                    pdTempSpinnerIds = [];
                    pdTempIds = [];
                    pdOperator = d.operator;
                    pdId = d.id;
                    $('#projectDefWeightDialog').empty();
                    node = d.children[0];
                    findTreeBranchInfo(pdData, [pdName], pdParentField, node);
                    operatorSelect(pdOperator);
                    updateButton(pdId);
                });

            // Transition nodes to their new position.
            var nodeUpdate = node.transition()
                .duration(duration)
                .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

            nodeUpdate.select("circle")
                .attr("r", function (d) {
                    // d.weight is expected to be between 0 and 1
                    // Nodes are displayed as circles of size between 1 and CIRCLE_SCALE
                    return d.weight ? Math.max(d.weight * CIRCLE_SCALE, MIN_CIRCLE_SIZE): MIN_CIRCLE_SIZE;
                })
                .style("fill", function(d) {
                    return d.source ? d.source.linkColor: d.linkColor;
                });

            nodeUpdate.select("text")
                .style("fill-opacity", 1);

            // Transition exiting nodes to the parent's new position.
            var nodeExit = node.exit().transition()
                .duration(duration)
                .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
                .remove();

            nodeExit.select("circle")
                .attr("r", 1e-6);

            nodeExit.select("text")
                .style("fill-opacity", 1e-6);

            // Update the links…
            var link = svg.selectAll("path.link")
                .data(links, function(d) { return d.target.id; });

            // Enter any new links at the parent's previous position.
            link.enter().insert("path", "g")
                .attr("class", "link")
                .attr("d", function(d) {
                  var o = {x: source.x0, y: source.y0};
                  return diagonal({source: o, target: o});
                });

            // Transition links to their new position.
            link.transition()
                .duration(duration)
                .attr("d", diagonal);

            // Transition exiting nodes to the parent's new position.
            link.exit().transition()
                .duration(duration)
                .attr("d", function(d) {
                  var o = {x: source.x, y: source.y};
                  return diagonal({source: o, target: o});
                })
                .remove();

            // Stash the old positions for transition.
            nodes.forEach(function(d) {
                d.x0 = d.x;
                d.y0 = d.y;
            });
            if (typeof pdData !== 'undefined'){
                qt_page.json_updated(pdData);
            }
        }
    } //end d3 tree

