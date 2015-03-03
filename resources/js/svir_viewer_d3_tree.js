/*
   Copyright (c) 2014-2015, GEM Foundation.

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

    // For checking if a string is blank or contains only white-space
    String.prototype.isEmpty = function() {
        return (this.length === 0 || !this.trim());
    };

    $(document).ready(function() {
        var longpress = false;
        //  Project definition weight dialog
        $("#projectDefWeightDialog").dialog({
            title: "Set weights and operator",
            position: {my: "left top", at: "left top", of: "#projectDefDialog"},
            autoOpen: false,
            modal: true,
            minWidth: 600
        });
        //  Dialog to set up a new node to insert into the project definition
        $("#projectDefNewNodeDialog").dialog({
            title: "Add new indicator",
            position: {my: "left top", at: "left top", of: "#projectDefDialog"},
            autoOpen: false,
            modal: true,
            minWidth: 500,
            dialogClass: "no-close",
            closeOnEscape: false
        });
    });

    ////////////////////////////////////////////
    //// Project Definition Collapsible Tree ///
    ////////////////////////////////////////////

    function loadPD(project_definition, qt_page) {
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

        var margin = {top: 20, right: 120, bottom: 20, left: 60};
        var width = 960 - margin.right - margin.left;
        var height = 800 - margin.top - margin.bottom;

        var i = 0;
        var duration = 750;
        var root;

        var tooltipdiv = d3.select("#projectDefDialog").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        var tree = d3.layout.tree().size([height, width]);

        var nodeEnter;

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
                    min: -100,
                    max: 100,
                    step: 0.000001,
                    numberFormat: "n"
                });
            });
        }

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

        function fieldSelect(node, node_type){
            // TODO: Add more stuff to the node
            dialog = $('#projectDefNewNodeDialog');
            //TODO use selectmenu when the bug there is fixed9?
            //$(selector).selectmenu()
            //$(selector).prop('selectedIndex', 4)
            // $('#field').val(node.field);
            dialog.empty();

            dialog
                .append('<label for="name">Description: </label>')
                .append('<input id="newNodeName" type="text" name="newNodeName" value="">');

            newNodeName = $('#newNodeName');
            newNodeName.blur(function(){
                if (newNodeName.val().isEmpty()){
                    newNodeName.addClass("ui-state-error");
                }
                else{
                    newNodeName.removeClass("ui-state-error");
                }
            });

            if (node_type != node_types_dict.SV_THEME) {
                dialog
                    .append('<br/><label for="field">Field name: </label>')
                    .append('<select id="field">' + fieldOptions(node) + '</select><br/>');

                // By default, set the name to be equal to the fieldname selected
                var defaultName = $('#field').val();
                newNodeName.val(defaultName);

                $('#field').on('change', function() {
                    newNodeName.val(this.value);
                });
            }
        }

        function node_type_to_class(node_type){
            return node_type.toLowerCase().replace(/ /g, '_');
        }

        function find_next_decimal_level(nesting_level){
            var max_dec_level = 0;

            var nodes_str = JSON.stringify(root, function(key, value) {
                //avoid circularity in JSON by removing the parent key
                if (key == "parent") {
                    return undefined;
                  }
                  return value;
                });

            //match level":3.2 with a submatch containing 2 in the whole json
            var re = new RegExp('level":"'+nesting_level+'\\.(\\d)', 'gi');
            var match;
            while ((match = re.exec(nodes_str)) !== null) {
                if (match.index === re.lastIndex) {
                    re.lastIndex++;
                }
                // get 2 out of level":3.2
                var decimal_level = match[1];
                if (decimal_level >= max_dec_level){
                    max_dec_level = parseInt(decimal_level) + 1;
                }
            }
            return max_dec_level;
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
                    totalWeights += Math.abs(this);
                });

                for (var i = 0; i < pdTempWeights.length; i++) {
                    var tempMath = (pdTempWeights[i] * 100) / totalWeights;
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

        function findTreeBranchInfo(pdData, pdName, pdLevel, pdField, node) {
            // Find out how many elements are in tree branch
            if (pdLevel.some(
                function(currentValue) {
                    return (pdData.level == currentValue);
                }
            ))
            {
                pdTempIds.push(pdData.id);
                createSpinner(pdData.id, pdData.weight, pdData.name, pdData.field);
            }

            (pdData.children || []).forEach(function(child) {
                findTreeBranchInfo(child, [pdName], [pdLevel], pdField, node);
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

        function updateNode(node, field, name) {
            node.field = field;
            node.name = name;
            updateD3Tree(node);
        }

        var svg = d3.select("#projectDefDialog").append("svg")
            .attr("width", width + margin.right + margin.left)
            .attr("height", height + margin.top + margin.bottom)
            .attr("id", "project-definition-svg")
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        d3.json('', function() {
            data = JSON.parse(project_definition);
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

            // remove all the old nodes will redraw the full graph
            svg.selectAll("*").remove();
            //https://github.com/mbostock/d3/wiki/Selections#data
            var updated_nodes = svg.selectAll("g.node").data(nodes, function(d) { return d.id || (d.id = ++i); });
            // Enter any new nodes at the parent's previous position.
            nodeEnter = updated_nodes.enter().append("g")
                .attr("class", "node")
                .attr("transform", function(d) { return "translate(" + root.y0 + "," + root.x0 + ")"; });

            nodeEnter.append("circle")
                .attr("r", 1e-6)
                .attr("class", function(d){return node_type_to_class(d.type);})
                .on("mouseover", function(d) {
                    var info;
                    if (d.field !== undefined) {
                        info = d.field;
                        tooltipdiv .transition()
                            .duration(500)
                            .style("opacity", 0.7);
                        tooltipdiv .html(info)
                            .style("left", (d3.event.pageX) + "px")
                            .style("top", (d3.event.pageY - 20) + "px");
                    }
                })
                .on("mouseout", function(d) {
                    tooltipdiv .transition()
                        .duration(500)
                        .style("opacity", 0);
                    })
                .on("mousedown", function(){
                    startTime = new Date().getTime();
                    })
                .on("mouseup", function(){
                    endTime = new Date().getTime();
                    longpress = (endTime - startTime < 500) ? false : true;
                    })
                .on("click", function(clicked_node) {
                    if (longpress) {
                        // If the clicked node is the IRI, clean the whole tree
                        if (clicked_node.type === node_types_dict.IRI) {
                            pdData = data;
                            // Before cleaning the tree, ask for the user's confirmation
                            var resp = confirm("If you proceed, the whole tree will be reset. Are you sure?");
                            if (resp === false) {
                                return false;
                            }
                            // its children are RI and SVI, and we want to delete their children (grandchildren)
                            for (var i = 0; i < clicked_node.children.length; i++) {
                                var child = clicked_node.children[i];
                                var grandchildren = child.children;
                                if (typeof(grandchildren) !== 'undefined') {
                                    while(grandchildren.length > 0) {
                                        grandchildren.pop();
                                    }
                                }
                            }
                            updateD3Tree(pdData);
                            return true;
                        }
                        // If the clicked node is the RI or SVI, clean its own branch
                        if (clicked_node.type === node_types_dict.RI || clicked_node.type === node_types_dict.SVI) {
                            pdData = data;
                            // Before cleaning the branch, ask for the user's confirmation
                            var resp = confirm("If you proceed, the whole branch be reset. Are you sure?");
                            if (resp === false) {
                                return false;
                            }
                            children = clicked_node.children;
                            if (typeof(children) !== 'undefined') {
                                while (children.length > 0) {
                                    children.pop();
                                }
                            }
                            updateD3Tree(pdData);
                            return true;
                        }

                        // Delete the clicked node, if it's an indicator or a theme
                        // If it's a theme, delete also its children
                        var node_to_del = clicked_node;
                        pdData = data;
                        var deletable_types = [node_types_dict.RISK_INDICATOR,
                                               node_types_dict.SV_INDICATOR,
                                               node_types_dict.SV_THEME];
                        if ( ($.inArray(node_to_del.type, deletable_types)) === -1 ) {
                            // Do not delete the node
                            return false;
                        }
                        var resp = confirm("The node named '" + node_to_del.name + "' will be removed and the weights of its siblings will be reset. Are you sure?");
                        if (resp === false) {
                            return false;
                        }
                        // Delete the node (find it between it's parent's children and delete it)
                        var siblings = node_to_del.parent.children;  // siblings include the clicked node itself
                        var idx_to_remove;
                        for (var i = 0; i < siblings.length; i++) {
                            if (siblings[i].id === node_to_del.id) {
                                // save the index of the item, but don't remove it before updating weights
                                idx_to_remove = i;
                            } else {
                                // reset the weights of the other nodes
                                // (-1 is because we are removing the clicked node)
                                siblings[i].weight = 1.0 / (siblings.length - 1);
                            }
                        }
                        // now it's safe to remove the clicked node
                        siblings.splice(idx_to_remove, 1);
                        updateD3Tree(pdData);
                    } else {
                        // Add a child to the clicked node, if possible
                        // NOTE: Only fields that are not already in the tree should be selectable
                        // By default, assign equal weights to the new node and to its siblings
                        pdData = data; // PAOLO: What's data?
                        var node_type;
                        switch (clicked_node.type) {
                            // clicked on IR, we allow generating a node
                            case node_types_dict.RI:
                                node_type = node_types_dict.RISK_INDICATOR;
                                //alert("You clicked a node with type " + clicked_node.type);
                                break;
                            case node_types_dict.SVI:
                                //alert("You clicked a node with type " + clicked_node.type);
                                node_type = node_types_dict.SV_THEME;
                                break;
                            // clicked on an SVI theme, we allow generating a node
                            case node_types_dict.SV_THEME:
                                //alert("You clicked a node with type " + clicked_node.type);
                                node_type = node_types_dict.SV_INDICATOR;
                                break;
                            // cases where we don't allow generating a node
                            case node_types_dict.SV_INDICATOR:
                                //alert("You clicked a node with type " + clicked_node.type + ". You can't add new nodes there");
                                return false;
                            case undefined:
                                //alert("You clicked a node with type " + clicked_node.type + ". You can't add new nodes there");
                                return false;
                            default:
                                //alert("You clicked a node with type " + clicked_node.type + ". You can't add new nodes there");
                                return false;
                        }

                        if (undefined === clicked_node.children) {
                            clicked_node.children = [];
                            clicked_node.operator = DEFAULT_OPERATOR;
                        }
                        var siblings = clicked_node.children;
                        var avg_weight = 1.0 / (siblings.length + 1);

                        var old_weights = [];
                        for (var i = 0; i < siblings.length; i++) {
                            old_weights[i] = siblings[i].weight;
                            siblings[i].weight = avg_weight;
                        }

                        //Prepare for the new node
                        var siblings_level = 0;
                        var new_node_level = 0;

                        if (siblings.length > 0) {
                            // the clicked_node already has a child
                            new_node_level = siblings[0].level;
                        }
                        else {
                            var parent_level = (clicked_node.level).split('.')[0];
                            siblings_level = parseInt(parent_level) + 1; //ex: 4
                            var next_decimal_level = find_next_decimal_level(siblings_level); //ex: 1
                            new_node_level = siblings_level + '.' + next_decimal_level; //ex: 4.1
                        }

                        var new_node = {
                            // field and name are assigned through a dialog,
                            // after the node is created
                            'parent': clicked_node,
                            'children':[],
                            'weight': avg_weight,
                            'type': node_type,
                            'x0': clicked_node.x,
                            'y0': clicked_node.y,
                            'level': new_node_level,
                            'depth': clicked_node.depth + 1,
                            'field': "",
                            'name': ""
                        };
                        // console.log("newnode:")
                        // console.log(new_node)

                        // Add node, appending it to the node that has been clicked
                        siblings.push(new_node);
                        // alert(JSON.stringify(source));
                        // Let the user choose one of the available fields and set the name
                        $('#projectDefNewNodeDialog').dialog({
                        title: "Add New " + node_type,
                        buttons: [
                            {
                            text: "Cancel",
                            click: function() {
                                clicked_node.children.splice(clicked_node.children.length - 1, 1);
                                for (var i = 0; i < siblings.length; i++) {
                                    siblings[i].weight = old_weights[i];
                                }
                                updateD3Tree(pdData);
                                $( this ).dialog( "close" );
                            }
                            },
                            {
                            text: "Add",
                            click: function(){
                                var newNodeName = $('#newNodeName');

                                if (newNodeName.val().isEmpty()){
                                    newNodeName.addClass("ui-state-error");
                                    return false;
                                }
                                if (node_type == node_types_dict.SV_INDICATOR || node_type == node_types_dict.RISK_INDICATOR) {
                                    var newNodeField = $('#field');
                                    if (newNodeField.val().isEmpty()) {
                                        return false;
                                    }
                                }
                                var field = $('#field').val();
                                    updateNode(new_node, field, newNodeName.val());
                                $( this ).dialog( "close" );
                                }
                            }
                        ]
                        });

                        fieldSelect(clicked_node, node_type);
                        $('#projectDefNewNodeDialog').dialog("open");
                    }
                });

            nodeEnter.append("text")
                .attr("class", (function(d) { return "level-" + d.level; }))
                .attr("id", (function(d) { return 'indicator-label-' + d.name.replace(' ', '-'); }))
                .attr("value", (function(d) { return d.weight; }))
                .attr("x", function(d) { return -(Math.abs(d.weight) * CIRCLE_SCALE + 5); })
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
                    pdLevel = d.level;
                    pdTempSpinnerIds = [];
                    pdTempIds = [];
                    $('#projectDefWeightDialog').empty();
                    if (d.parent){
                        findTreeBranchInfo(pdData, [pdName], [pdLevel], pdField, d);
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
                .attr("id", function(d) {return "operator-label-" + d.level;})
                .attr("x", function(d) { return Math.abs(d.weight) * CIRCLE_SCALE + 15; })
                .on("click", function(d) {
                    pdName = d.children[0].name;
                    pdData = data;
                    pdLevel = d.children[0].level;
                    pdParent = d.name;
                    pdParentField = d.field;
                    pdTempSpinnerIds = [];
                    pdTempIds = [];
                    pdOperator = d.operator;
                    pdId = d.id;
                    $('#projectDefWeightDialog').empty();
                    updated_nodes = d.children[0];
                    findTreeBranchInfo(pdData, [pdName], [pdLevel], pdParentField, updated_nodes);
                    operatorSelect(pdOperator);
                    updateButton(pdId);
                });

            // Transition nodes to their new position.
            var nodeUpdate = updated_nodes.transition()
                .duration(duration)
                .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

            nodeUpdate.select("circle")
                .attr("r", function (d) {
                    // d.weight is expected to be between 0 and 1
                    // Nodes are displayed as circles of size between 1 and CIRCLE_SCALE
                    return d.weight ? Math.max(Math.abs(d.weight) * CIRCLE_SCALE, MIN_CIRCLE_SIZE): MIN_CIRCLE_SIZE;
                })
                .style("stroke", function(d) {
                    if (d.weight < 0) {
                        return "PowderBlue";
                    } else {
                        return "RoyalBlue";
                    }
                })
                .style("stroke-width", 4)
                .style("fill", function(d) {
                    // return d.source ? d.source.linkColor: d.linkColor;
                    if (d.weight < 0) {
                        return "RoyalBlue";
                    } else {
                        return "PowderBlue";
                    }
                });

            nodeUpdate.select("text")
                .style("fill-opacity", 1);

            // Transition exiting nodes to the parent's new position.
            var nodeExit = updated_nodes.exit().transition()
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

