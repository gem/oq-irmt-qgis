.. _chap-aggregating-loss-by-zone:

************************
Aggregating loss by zone
************************

The development of an integrated risk model (IRI) arises from the convolution
of two main components: 1) estimations of physical risk (RI), and 2) a social
vulnerability index (SVI). The convolution of earthquake physical risk and
social vulnerability parameters can be accomplished by selecting layers that
contain estimations of physical risk, (*Loss layer*) or some other type of risk
model, and a layer containing zonal geometries of the study area (e.g., country
borders, district borders) and socioeconomic indicators.

As a subsequent step, earthquake risk data imported into the tool should be
standardized to render the data commensurate to the socioeconomic indicators
created within the tool.

In previous versions of this plugin, there was a specific tool to perform the
geospatial aggregation. Recently, it was dismissed because its functionalities
overlap with those of a powerful tool that is available in the Processing
Toolbox.  Therefore, the button that pointed to our customized implementation
now points to the corresponding Processing algorithm, called "Join attributes
by location (summary)".

In order to obtain a similar workflow with respect to what was done previously
with our tool, we suggest to select the *zonal layer* as "Input layer" and the
*loss layer* as "Join layer", then keep checked "intersects" as "Geometric predicate",
and choose the fields to summarize and the summaries to calculate (that in our case were
"sum" and "mean".
Afterwards, it is possible to style the layer using the standard QGIS layer symbology menu,
for instance setting a "Graduated" renderer by a chosen column and applying the
classification by a chosen number of classes.

.. |icon-aggregate-loss-by-zone| image:: images/iconAggregateLossByZone.png
