.. _chap-definitions:

************************
Definitions and acronyms
************************

In this manual, the terminology *layer*, and *project*
are used ubiquitously, and it is important to explain what the terminology
means as well as its use. In QGIS, a *project* or *project file* is a kind of
container that acts like a folder storing information on file locations of
layers and how these layers are displayed in a map. It is the main QGIS
datafile. A *layer* is the mechanism used to display geographic datasets in the
QGIS software, and layers provide the data that is manipulated within the OpenQuake IRMT.
Each layer references a specific dataset and specifies how that dataset is
portrayed within the map. The standard layer format for the OpenQuake IRMT is the ESRI
Shapefile [ESRI98]_ that can be imported within the QGIS software using the
default *add data* functionality, or layers may be created on-the-fly within
the OpenQuake IRMT using GEM socio-economic databases.  A QGIS project can include
multiple layers that can be utilized to provide the variables and maps
necessary for an integrated risk assessment.

In seismic hazard and risk analysis, a Ground-Motion Measure Type (GMMT) is a
physical quantity expressing a particular characteristic of the ground shaking
recorded or computed at one site. The most important and frequently used GMMTs
are scalar and they indicate the shaking intensity (i.e. the amplitude of the
ground shaking). These GMMT are also indicated with the acronym IMT. Other
ground-motion measures define, for example, the duration of the shaking. A very
common IMT is the peak ground acceleration, specified with the PGA acronym. The
principal IMT used in the OpenQuake-engine are:

  * Peak Ground Acceleration – indicated as PGA – measured in fractions of g
  * Peak Ground Velocity – indicated as PGV – measured in cm/s
  * Peak Ground Displacement – indicated as PGV – measured in cm
  * Spectral Acceleration for a given period T – indicated as Sa(T) - measured
    in fractions of g

An Intensity Measure Level (IML) is a value of a specific IMT.

.. FIXME add definitions needed while describing risk outputs


.. [ESRI98]
    ESRI Shapefile Technical Description,
    Environmental Systems Research Institute, Redlands, C.A.
