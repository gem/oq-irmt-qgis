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

const circle_scale = 20;

    $(document).ready(function() {
        //  Project definition weight dialog
        $("#projectDefWeightDialog").dialog({
            autoOpen: false,
            height: 500,
            width: 500,
            modal: true
        });
    });


    ////////////////////////////////////////////
    //// Project Definition Collapsible Tree ///
    ////////////////////////////////////////////

    function loadPD(selectedPDef, qt_page) {
        var qt_page = typeof qt_page !== 'undefined' ? qt_page : false;
        const DEFAULT_OPERATOR = qt_page.DEFAULT_OPERATOR
        const OPERATORS = qt_page.OPERATORS.split(';')
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

        function createSpinner(id, weight, name) {
            pdTempSpinnerIds.push("spinner-"+id);
            $('#projectDefWeightDialog').dialog("open");
            $('#projectDefWeightDialog').append('<p><label for="spinner'+id+'">'+name+': </label><input id="spinner-'+id+'" name="spinner" value="'+weight+'"></p>');
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
            var options = ''
            for (i = 0; i < OPERATORS.length; i++) {
                var c = OPERATORS[i];
                if (c == DEFAULT_OPERATOR){
                    options += '<option value="' + c + '" selected="selected">' + c + '</option>'
                }
                else{
                    options += '<option value="' + c + '">' + c + '</option>'
                }
            }

            return options
        }

        function updateButton(pdId){
            pdId = typeof pdId !== 'undefined' ? pdId : false;
            $('#projectDefWeightDialog').append('<br/><br/><button type="button" id="update-button">Update</button>');
            $('#update-button').click(function(){updateButtonClicked()});
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
                };

                // Adjust the values into percentages
                pdTempWeights = pdTempWeights.map(Number);
                var totalWeights = 0;
                $.each(pdTempWeights,function() {
                    totalWeights += this;
                });

                for (var i = 0; i < pdTempWeights.length; i++) {
                    var tempMath = Math.floor((pdTempWeights[i] * 100) / totalWeights);
                    pdTempWeightsComputed.push(tempMath / 100);
                };

                // Update the results back into the spinners and to the d3.js chart
                for (var i = 0; i < pdTempSpinnerIds.length; i++) {
                    $('#'+pdTempSpinnerIds[i]).spinner("value", pdTempWeightsComputed[i]);
                };

                // Update the json with new values
                for (var i = 0; i < pdTempWeightsComputed.length; i++) {
                    updateTreeBranch(pdData, [pdTempIds[i]], pdTempWeightsComputed[i]);
                };

                if ($('#operator').length != 0) {
                    var operator = $('#operator').val()
                    updateOperator(pdData, pdId, operator);
                }

                nodeEnter.remove("text");
                updateD3Tree(pdData);
            }
        };

        function findTreeBranchInfo(pdData, pdName, pdLevel) {
            // Find out how many elements are in tree branch
            if (pdLevel.some(
                function(currentValue) {
                    return (pdData.level == currentValue);
                }
            ))
            {
                pdTempIds.push(pdData.id);
                createSpinner(pdData.id, pdData.weight, pdData.name);
            }

            (pdData.children || []).forEach(function(currentItem) {
                findTreeBranchInfo(currentItem, [pdName], [pdLevel]);
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
                .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })

            nodeEnter.append("circle")
                .attr("r", 1e-6);
            
            nodeEnter.append("text")
                .attr("class", (function(d) { return "level-" + d.level; }))
                //.attr("id", (function(d) { return d.name; }))
                .attr("id", "svg-text")
                .attr("value", (function(d) { return d.weight; }))
                .attr("x", function(d) { return -(d.weight * circle_scale + 5); })
                .attr("dy", function(d) {
                    // NOTE are x and y swapped?
                    // set te text above or below the node depending on the
                    // parent position
                    if (typeof d.parent != "undefined" && d.x > d.parent.x){
                        return "2em";
                    }
                    return "-1em" })
                .attr("text-anchor", function(d) { return "end"; })
                .text(function(d) {
                    return d.name + " " + d.weight ;
                })
                .style("fill-opacity", 1e-6)
                .on("click", function(d) {
                    pdName = d.name;
                    pdData = data;
                    pdWeight = d.weight;
                    pdLevel = d.level;
                    pdTempSpinnerIds = [];
                    pdTempIds = [];
                    $('#projectDefWeightDialog').empty();
                    if (d.parent){
                        findTreeBranchInfo(pdData, [pdName], [pdLevel]);
                        var pdParentOperator = d.parent.operator? d.parent.operator : DEFAULT_OPERATOR;
                        d.parent.operator = pdParentOperator
                        operatorSelect(pdParentOperator);
                        pdId = d.parent.id
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
                        d.operator = operator
                        return operator
                    }
                })
                .attr("x", function(d) { return d.weight * circle_scale + 15; })
                .on("click", function(d) {
                    pdName = d.children[0].name;
                    pdData = data;
                    pdLevel = d.children[0].level;
                    pdParent = d.name;
                    pdTempSpinnerIds = [];
                    pdTempIds = [];
                    pdOperator = d.operator
                    pdId = d.id
                    $('#projectDefWeightDialog').empty();
                    findTreeBranchInfo(pdData, [pdName], [pdLevel]);
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
                    // Nodes are displayed as circles of size between 2 and 20
                    return d.weight ? Math.max(d.weight * circle_scale, 2): 2;
                })
                .style("fill", function(d) {
                    return d.source ? d.source.linkColor: d.linkColor
                })


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
            if (qt_page){
                if (typeof pdData !== 'undefined'){
                    qt_page.json_updated(pdData)
                }
            }
        }
    } //end d3 tree

