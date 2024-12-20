.. _chap-aggregating-points-by-zone:

**************************
Aggregating points by zone
**************************

In previous versions of this plugin, there was a specific tool to perform the
geospatial aggregation. Recently, it was dismissed because its functionalities
overlap with those of a powerful algorithm available in the QGIS Processing
Toolbox. Therefore, the button that pointed to our customized implementation
now points to the corresponding Processing tool, called "Join attributes
by location (summary)". Such button, :guilabel:`Aggregate points by zone`, is
under the :guilabel:`Utilities` submenu of the :guilabel:`OpenQuake IRMT` menu.

In order to obtain a similar workflow with respect to what was done previously
with our tool, we suggest to select the *zonal layer* as "Input layer" and the
*points layer* as "Join layer", then keep checked "intersects" as "Geometric
predicate", and choose the fields to summarize and the summaries to calculate
(that in our case were "sum" and "mean"). When the plugin opens the user
interface of the algorithm, it presets the above configuration by default.

Afterwards, it is possible to style the layer using the standard QGIS layer
symbology menu, for instance setting a "Graduated" renderer by a chosen column
and applying the classification by a chosen number of classes. In our standard
workflow, the column to be chosen is the "_sum" field that was created by the
aggregation tool.

.. |icon-aggregate-points-by-zone| image:: images/iconAggregateLossByZone.png
