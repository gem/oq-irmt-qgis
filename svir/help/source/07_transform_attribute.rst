.. _chap-transform-attribute:

***********************
Transforming attributes
***********************

.. _fig-transform-attribute:

.. figure:: images/dialogTransformAttribute.png
    :align: center
    :scale: 60%

    |icon-transform-attributes| Variable transformation and batch transformation functionality


When variables are defined in incommensurate ranges or scales, they can be
standardized to avoid problems inherent when mixing measurement units, and
normalization is employed to avoid having extreme values dominate an indicator,
and to partially correct for data
quality problems. The QGIS platform natively provides a :guilabel:`Field calculator` that
can be used to update existing fields, or to create new ones, in order to
perform a wide variety of mathematical operations for the
standardization/transformation of data. In addition, the  OpenQuake IRMT provides a
number of transformation functions found in popular statistical and
mathematical modelling packages (:numref:`tab-transformation-functions`).

.. _tab-transformation-functions:

.. table:: Selection of transformation functions with equations found in the OpenQuake IRMT.

  =============================  =================================================================================================================================
  Standardization (or Z-scores)  :math:`Z(x_i) = \frac{x_i-\mu_x}{\sigma_x} \; (\mu_x = mean \; \sigma_x = stddev)`
  Min-Max                        :math:`M(x_i) = \frac{x_i - \min_{i \in \{1,\dots,n\}}(x_i)}{\max_{i \in \{1,\dots,n\}}(x_i) - \min_{i \in \{1,\dots,n\}}(x_i)}` 
  Logistig Sigmoid               :math:`S(x_i) = \frac{1}{1 + e^{-x_i}}`
  Simple Quadratic               :math:`Q(x_i) = \frac{x^2}{\max_{i \in \{1,\dots,n\}}(x_i)}`
  =============================  =================================================================================================================================

.. warning::

    Not all layer types can be edited. For instance, it is impossible to add or
    modify fields of a csv-based layer. Prior to apply transformations to
    non-editable layers, it is necessary to save them as shapefiles or as
    another editable kind.

These include:

1. **Data Ranking** is the simplest standardization technique.
   Ranking is not affected by outliers and allows the performance of
   enumeration units to be benchmarked over time in terms of their relative
   positions (rankings). The ranking algorithm deals with
   ties using a chosen strategy between those listed below (see
   `<https://en.wikipedia.org/wiki/Ranking#Strategies_for_assigning_rankings>_`):

   * Average - Fractional (1 2.5 2.5 4)
   * Standard competition - Minimum (1 2 2 4)
   * Modified competition - Maximum (1 3 3 4)
   * Dense (1 2 2 3)
   * Ordinal (1 2 3 4)
 
2. **Z-scores (or normalization)** is the most common standardization
   technique. A Z-score converts indicators to a common scale with a mean of
   zero and standard deviation of one. Indicators with outliers that are
   extreme values may have a greater effect on the composite indicator. The
   latter may not be desirable if the intention is to support compensability
   where a deficit in one variable can be offset (or compensated) by a surplus
   in another.
 
3. **Min-Max Transformation** is a type of transformation that
   rescales variables into an identical range between 0 and 1. Extreme
   values/or outliers could distort the transformed risk indicator. However,
   the MIN-MAX transformation can widen a range of indicators lying within a
   small interval, increasing the effect of the variable on the composite
   indicator more than the Z-scores.
 
4. **Log10** is one of a class of logarithmic transformations that
   include natural log, log2, log3, log4, etc. Within the current plugin, we
   offer functionality for log10 only, yet these transformations are possible
   within the advanced :guilabel:`field calculator`. A logarithm of any negative number
   or zero is undefined. It is not possible to log transform values within the
   plugin if the data contains negative values or a zero. For values of zero,
   the tool will warn users and suggest that a :math:`1.0` constant be added to move
   the minimum value of the distribution.
 
5. **Sigmoid function** is a transformation function having an *S*
   shape (sigmoid curve). A Sigmoid function is used to transform values on
   :math:`(-\infty, \infty)` into numbers on :math:`(0, 1)`. The Sigmoid function is often
   utilized because the transformation is relative to a convergence upon an
   upper limit as defined by the S-curve. The OpenQuake IRMT utilizes a *simple sigmoid
   function* as well as its inverse. The Inverse of the Sigmoid function is a
   logit function which transfers variables on :math:`(0, 1)` into a new variable on
   :math:`(-\infty, \infty)`.
 
6. **Quadratic or U-shaped functions** are the product of a
   polynomial equation of degree 2. In a quadratic function, the variable is
   always squared resulting in a parabola or U-shaped curve. The OpenQuake IRMT offers
   an increasing or decreasing variant of the quadratic equation for
   horizontal translations and the respective inverses of the two for vertical
   translations.

.. note::

    It may be desirable to visualize the results of the
    application of transformation functions to data. Although not feasible
    within the plugin at this point, we intend to build data plotting and curve
    manipulating functionalities into future versions of the toolkit.   

The :guilabel:`Transform attribute` dialog (:numref:`fig-transform-attribute`) was
designed to be quite straightforward. The user is required to select one or
more numeric fields (variables) available in the active layer. For the
selection to be completed, the user must move the variables (either one at a
time, or in a batch) to the :guilabel:`Selected variables` window on the right side of
the interface. The user must then select the function necessary to transform
the selected variables. For some functions, more than one variant is available.
For functions that have an implementation of an inverse transformation, the
:guilabel:`Inverse` checkbox will be enabled to allow users to invert the outcome of the
transformation.

The :guilabel:`New field(s)` section contains two checkboxes and a text field. If the
first checkbox :guilabel:`Overwrite the field(s)` is selected, the original values of the
transformed fields will be overwritten by the results of the calculations;
otherwise, a new field for each transformed variable will be created to store
the results. In situations in which a user may desire to transform variables
one at a time rather than using a batch transformation process, it is possible
for the user to name each respective new field (editing the default one
proposed by the tool). Otherwise, the names of the new fields will be
automatically assigned using the following convention: if the original
attribute is named *ORIGINALNA*, the name of the transformed attribute becomes
*\_ORIGINALN* (prepending "*\_*" and truncating to 10 characters which is the
maximum length permitted for field names in shapefiles). If the layer does not
have the limitations of a shapefile, the name of the transformed field will *not*
be truncated to 10 characters.

.. note::

    In the lists of fields, both the field name and the field alias are displayed,
    with the format `name (alias)`. If no alias is specified for the field, the
    parenthesis will be empty. The plugin automatically assigns to the
    transformed field the same alias of the original one (if available).
    Please make sure that the names of the fields to be transformed do not
    contain parentheses, otherwise the plugin would erroneously interpret them
    as containers for the alias; therefore the selected name would be incomplete
    (being taken excluding the parentheses) and it would not be found in the layer.

If the checkbox :guilabel:`Let all project definitions utilize transformed
values` is checked, all the project definitions associated with the active
layer will reference the transformed fields instead of the original ones.
Otherwise, they will keep the links to the original selected attributes. In
most cases it is recommended to keep this checkbox checked. This automatic
update of field references simplifies the workflow because it avoids the need
to manually remove the original nodes from the weighting and aggregation tree
(discussed in detail in :ref:`chap-weighting-and-calculating`) in
order to add the transformed nodes and to set again the nodes' weights. In
other words, if a project was developed by weighting and aggregating
untransformed indicators, this functionality allows for variables used in the
project definition to be replaced on-the-fly (and automatically) by transformed
variables.  This saves the user from having to augment the model manually.  

By clicking the :guilabel:`Advanced Calculator` button, the native QGIS field calculator
is opened. Please refer to the `code documentation
<../../../apidoc/_build/html/svir.calculations.html#module-svir.calculations.transformation_algs>`_
for the detailed description of all the agorithms and variants provided by
the OpenQuake IRMT.

The plugin is also an algorithm provider (the :guilabel:`OpenQuake IRMT` provider)
for the Processing Toolbox. The transformation functions described above
are available under the :guilabel:`Field transformation` group.

.. |icon-transform-attributes| image:: images/iconTransformAttribute.png
