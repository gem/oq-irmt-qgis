************
Introduction
************

At the core of the Global Earthquake Model (GEM) is the development of
state-of-the-art modeling capabilities and a suite of software tools that can
be utilized worldwide for the assessment and communication of earthquake risk.
For a more holistic assessment of the scale and consequences of earthquake
impacts, a set of methods, metrics, and tools are incorporated into the GEM
modelling framework to assess earthquake impact potential beyond direct
physical impacts and loss of life. This is because with increased exposure of
people, livelihoods, and property to earthquakes, the potential for social and
economic impacts of earthquakes cannot be ignored. Not only is it vital to
evaluate and benchmark the conditions within social systems that lead to
adverse earthquake impacts and loss, it is equally important to measure the
capacity of populations to respond to damaging events and to provide a set of
metrics for priority setting and decision-making.  

The employment  of a methodology and workflow necessary for the evaluation of
seismic risk that is integrated and holistic begins with the OpenQuake Integrated Risk
Modelling Toolkit (OpenQuake IRMT). The OpenQuake IRMT is QGIS plugin that was developed by the
`Global Earthquake Model (GEM) Foundation <http://www.globalquakemodel.org/>`_
and co-designed by GEM and the `Center for Disaster Management and Risk
Reduction Technology (CEDIM) <https://www.cedim.de/english/index.php>`_. 

The OpenQuake IRMT plugin has evolved significantly with respect to its original
purposes, in order to make it operate seamlessly with the
`OpenQuake Engine <https://github.com/gem/oq-engine>`_ (OQ-engine)
([PMW+14]_ and [SCP+14]_). This enables
a whole end-to-end workflow, where calculations of physical hazard and risk can
be run directly from within the QGIS environment (see
:ref:`chap-drive-oq-engine`) and the outputs of such calculations can be loaded
as QGIS vector layers. Those of them that can be visualized as maps (e.g.
hazard maps) are also automatically styled with respect to fields selected by
the user. Others can be plotted as curves (e.g. hazard curves) inside a
:guilabel:`Data Viewer` window (see :ref:`chap-viewer-dock`) that was conceived
for this purpose.


.. [PMW+14]
    Pagani, M., Monelli, D., Weatherill, G., Danciu, L., Crowley, H., Silva,
    V., Henshaw, P., Butler, L., Nastasi, M., Panzeri, L., Simionato, M. and
    Vigano, V. OpenQuake Engine: An Open Hazard (and Risk) Software for the
    Global Earthquake Model. Seismological Research Letters, vol. 85 no. 3,
    692-702

.. [SCP+14]
    Silva, V., Crowley, H., Pagani, M., Monelli, D., and Pinho, R., 2014.
    Development of the OpenQuake engine, the Global Earthquake Model’s
    open-source software for seismic risk assessment. Natural Hazards 72(3),
    1409-1427.
