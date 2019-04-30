***************
The plugin menu
***************

When the OpenQuake IRMT plugin is installed, it adds its own menu to those available
on the QGIS graphical user interface. The plugin menu contains the
options listed below. For each option, this manual provides a separate chapter
with the description of its functionality and of the typical workflows in which
it is used. Please follow the links next to the option icons, to reach the
corresponding documentation.

.. note::

    The menu options are disabled when the corresponding
    functionalities can not be performed. For instance, the
    *Transform attributes* option will be available only as long as
    one of the loaded layers is activated.

* OpenQuake Platform

  * |icon-load-indicators| :ref:`chap-load-indicators`
  * |icon-import-project| :ref:`chap-download-project`
  * |icon-upload| :ref:`chap-uploading-project-to-platform`

* OpenQuake Engine

  * |icon-ipt| `OpenQuake Risk Input Preparation Toolkit <https://github.com/gem/oq-platform-ipt>`_:
    Online tools used to create exposure, fragility and vulnerability risk input models.
  * |icon-taxtweb| `OpenQuake TaxtWEB <https://github.com/gem/oq-platform-taxtweb>`_:
    Online graphical tool for editing GEM Taxonomy strings.
  * |icon-drive-oq-engine| :ref:`chap-drive-oq-engine`

* Integrated risk

  * |icon-project-definitions-manager| :ref:`chap-project-definitions-manager`
  * |icon-weight-and-calculate| :ref:`chap-weighting-and-calculating`

* Recovery modeling

  * |icon-recovery| :ref:`chap-recovery-modeling`
  * |icon-recovery-settings| :ref:`sec-recovery-modeling-settings`

* Utilities

  * |icon-aggregate-points-by-zone| :ref:`chap-aggregating-points-by-zone`
  * |icon-transform-attributes| :ref:`chap-transform-attribute`

* |icon-plugin-settings| :ref:`chap-irmt-settings`

* |icon-plot| :ref:`chap-viewer-dock`

* |icon-manual| OpenQuake IRMT manual: a web browser will be opened, showing the html
  version of this manual


.. |icon-plugin-settings| image:: images/iconPluginSettings.png
.. |icon-load-indicators| image:: images/iconLoadIndicators.png
.. |icon-import-project| image:: images/iconImportProject.png
.. |icon-transform-attributes| image:: images/iconTransformAttribute.png
.. |icon-project-definitions-manager| image:: images/iconProjectDefinitionManager.png
.. |icon-weight-and-calculate| image:: images/iconWeightAndCalculate.png
.. |icon-aggregate-points-by-zone| image:: images/iconAggregateLossByZone.png
.. |icon-upload| image:: images/iconUpload.png
.. |icon-manual| image:: images/iconManual.png
.. |icon-plot| image:: images/iconPlot.png
.. |icon-recovery| image:: images/iconRecovery.png
.. |icon-recovery-settings| image:: images/iconRecoverySettings.png
.. |icon-drive-oq-engine| image:: images/iconDriveOqEngine.png
.. |icon-ipt| image:: images/iconIpt.png
.. |icon-taxtweb| image:: images/iconTaxtweb.png
