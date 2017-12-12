.. _chap-definitions:

************************
Definitions and acronyms
************************

In this manual, the terminology *layer*, *project*, and *project definition*
are used ubiquitously, and it is important to explain what the terminology
means as well as its use. In QGIS, a *project* or *project file* is a kind of
container that acts like a folder storing information on file locations of
layers and how these layers are displayed in a map. It is the main QGIS
datafile. A *layer* is the mechanism used to display geographic datasets in the
QGIS software, and layers provide the data that is manipulated within the IRMT.
Each layer references a specific dataset and specifies how that dataset is
portrayed within the map. The standard layer format for the IRMT is the ESRI
Shapefile [ESRI98]_ that can be imported within the QGIS software using the
default *add data* functionality, or layers may be created on-the-fly within
the IRMT using GEM socio-economic databases.  A QGIS project can include
multiple layers that can be utilized to provide the variables and maps
necessary for an integrated risk assessment. For each layer, multiple *project
definitions* can be saved. A *project definition* is a set of parameters that
are defined within the IRMT to define the integrated risk assessment's
workflow. It allows users to create, edit, and manage the workflow needed to
systematically develop integrated risk models using layers. The project
definition:

* distinguishes which variables within a dataset are to be combined
  together to obtain a composite indicator;
* defines how variables are grouped together by supporting: 1)
  deductive models that typically contain fewer than ten indicators that
  are normalized and aggregated to create the index;  and 2) hierarchical
  models that employ roughly ten to twenty indicators that are separated
  into groups (sub-indices) that share the same underlying dimension
  (such as economy and infrastructure) in a manner in which individual
  indicators are aggregated into sub-indices, and the subindices are
  aggregated to create the index;
* describes  the type of aggregation method including additive
  modelling, weighted aggregation, and geometric aggregation that can be
  utilized by users to combine variables;
* establishes the application of weights (if desired) to individual
  variables or sub-indices; and
* delimits the directionality of variables when the intent is to
  consider that some variables may add to an index outcome; whereas some
  variables may need to detract from it. When considering the social
  vulnerability of populations, a socio-economic status indicator such as
  the percentage of population with a college education provides an
  example of a characteristic that may detract from social vulnerability,
  thereby warranting a negative directionality within an index.

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


.. [ESRI98]
    ESRI Shapefile Technical Description,
    Environmental Systems Research Institute, Redlands, C.A.
