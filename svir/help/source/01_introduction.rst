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
Reduction Technology (CEDIM) <https://www.cedim.de/english/index.php>`_. The
plugin allows users to form an integrated workflow for the construction of
metrics used to assess characteristics within societies that affect earthquake
risk by providing a GIS-based platform for the construction of indicators and
composite indices to foster comparative assessments. Here, an indicator is
defined as a piece of information that summarizes the characteristics of a
system or highlights what is happening in a system. An indicator is a
quantitative or qualitative measure derived from observed facts that simplify
and communicate the reality of a complex situation. Indicators reveal the
relative position of the phenomena being measured and when evaluated over time,
can illustrate the magnitude of change (a little or a lot) as well as direction
of change (up or down; increasing or decreasing). The mathematical combination
(or aggregation as it is termed) of a set of indicators forms a composite
indicator (or composite index or indices).

As part of the workflow, the OpenQuake IRMT facilitates the integration of composite
indicators of socio-economic characteristics with measures of physical risk
(i.e. estimations of human or economic loss) from the OpenQuake Engine
(OQ-engine) ([PMW+14]_ and [SCP+14]_), or other sources, to form what is referred to
as an integrated risk assessment. Although the tool may be utilized for any
type of indicator development, it is encouraged that composite indicators of
social vulnerability are developed within this integrated risk framework.
Social vulnerability is defined here as characteristics or qualities within
social systems that create the potential for harm or loss from damaging hazard
events. Given equal exposure to natural threats, such as an earthquake, two
groups may vary in their social vulnerability due to their pre-existing social
characteristics, where differences according to wealth, gender, race, class,
history, and sociopolitical organization influence the patterns of loss,
mortality, and the ability to reconstruct following damaging events. 

The focus on the development of indicators of social vulnerability, and
ultimately integrated risk, will allow researchers, decision-makers, and other
relevant stakeholders to:
 
* consider loss and damage as part of a dynamic system in which interactions
  between natural systems and societal factors redistribute risk before an event
  and redistribute loss after an event
* mainstream socio-economic vulnerability
  and resilience in earthquake loss and damage policy discussions
* evaluate loss
  and damage taking social factors into account at different time and space
  scales
* use risk assessments in benchmarking exercises to monitor trends in
  earthquake risk over time
* recognize that both causes and solutions for
  earthquake loss are found in human, environmental, and built-environmental
  interactions
* help decision-makers develop a common dialog that pertains to the
  factors that they should concentrate on to reduce risk and strengthen
  resilience.

The development of composite indicators is not new to research fields and
occupations requiring empirical measurement, and a vast literature on composite
indicators exists that outline methodological approaches for index construction
and validation. To accompany this manual we suggest the use of two popular
resources ([NSST05]_ and [NSST08]_) aimed at providing a guide for the
construction and use of composite indicators.

This literature outlines the process of robust composite indicator construction
that contains a number of steps. The OpenQuake IRMT guides
the user through the major steps for index construction. These steps include 1)
the selection of variables; 2) data normalization/standardization; 3) weighting
and aggregation to produce composite indicators; 4) risk integration using
OpenQuake risk estimates; and 5) the presentation of the results.

The OpenQuake IRMT plugin has been extended significantly with respect to its original
purposes, in order to make it operate seamlessly with the
`OpenQuake Engine <https://github.com/gem/oq-engine>`_. This enables
a whole end-to-end workflow, where calculations of physical hazard and risk can
be run directly from within the QGIS environment (see
:ref:`chap-drive-oq-engine`) and the outputs of such calculations can be loaded
as QGIS vector layers. Those of them that can be visualized as maps (e.g.
hazard maps) are also automatically styled with respect to fields selected by
the user. Others can be plotted as curves (e.g. hazard curves) inside a
:guilabel:`Data Viewer` window (see :ref:`chap-viewer-dock`) that was conceived
for this purpose.

Another important addition to the OpenQuake IRMT plugin is a module for post-earthquake
recovery modeling (see :ref:`chap-recovery-modeling`), that was supported by
the State of California, Alfred E. Alquist Seismic Safety Commission, as part
of a collaborative effort between the Global Earthquake Model (GEM) and the
University of California at Los Angeles (UCLA), Department of Civil and
Environmental Engineering. GEM implemented in the QGIS environment the
scientific methodology developed by UCLA [BDL+15]_.

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

.. [NSST05]
    Nardo, M., Saisana, M., Saltelli, A. and Tarantola, S. 2005. Tools for
    composite indicators Building. Ispara, Italy: Joint Research Center of the
    European Commission.

.. [NSST08]
    Nardo, M., Saisana, M., Saltelli, A. and Tarantola, S. 2008. Handbook on
    constructing composite indicators: Methodology and user guide. Paris,
    France: OECD Publishing.

.. [BDL+15]
   Burton, H., Deierlein, G., Lallemant, D., & Lin, T. (2015). Framework for
   Incorporating Probabilistic Building Performance in the Assessment of
   Community Seismic Resilience. J.Struct.Eng.
   doi:10.1061/(ASCE)ST.1943-541X.0001321
