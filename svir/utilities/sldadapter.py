# -*- coding: utf-8 -*-
#/***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2015-03-27
#        copyright            : (C) 2015 by GEM Foundation
#        email                : devops@openquake.org
# ***************************************************************************/
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

# Part of this code was taken and re-adapted from
# https://github.com/boundlessgeo/suite-qgis-plugin/blob/master/src/opengeo/qgis/sldadapter.py
# methods to convert the SLD produced by GeoServer (1.0) to the SLD produced
# by QGIS (1.1), and also the other way round. This is a quick and dirty
# solution until both programs support the same specification

import re
import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import (
    QgsSingleBandGrayRenderer, QgsExpression, QgsOgcUtils,
    QgsSingleBandPseudoColorRenderer, QgsSymbolLayerUtils, QgsSymbol,
    QgsUnitTypes)

SIZE_FACTOR = 4
RASTER_SLD_TEMPLATE = (
    '<?xml version="1.0"?>'
    '<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld"'
    ' xmlns:sld="http://www.opengis.net/sld"'
    ' xmlns:ogc="http://www.opengis.net/ogc"'
    ' xmlns:gml="http://www.opengis.''net/gml" version="1.0.0">'
    '<sld:NamedLayer>'
    '<sld:Name>STYLE_NAME</sld:Name>'
    '<sld:UserStyle>'
    '<sld:Name>STYLE_NAME</sld:Name>'
    '<sld:Title/>'
    '<sld:FeatureTypeStyle>'
    # '<sld:Name>name</sld:Name>'
    '<sld:Rule>'
    # '<sld:Name>Single symbol</sld:Name>'
    '<RasterSymbolizer>'
    'SYMBOLIZER_CODE'
    '</RasterSymbolizer>'
    '</sld:Rule>'
    '</sld:FeatureTypeStyle>'
    '</sld:UserStyle>'
    '</sld:NamedLayer>'
    '</sld:StyledLayerDescriptor>')


def adaptQgsToGs(sld, layer):
    sld = sld.replace("se:SvgParameter", "CssParameter")
    sld = sld.replace("1.1.", "1.0.")
    sld = sld.replace("\t", "")
    sld = sld.replace("\n", "")
    sld = re.sub("\s\s+", " ", sld)
    sld = re.sub("<ogc:Filter>[ ]*?<ogc:Filter>", "<ogc:Filter>", sld)
    sld = re.sub("</ogc:Filter>[ ]*?</ogc:Filter>", "</ogc:Filter>", sld)
    if layer.hasScaleBasedVisibility():
        s = ("<MinScaleDenominator>" + str(layer.minimumScale()) +
             "</MinScaleDenominator><MaxScaleDenominator>" +
             str(layer.maximumScale()) + "</MaxScaleDenominator>")
        sld = sld.replace("<se:Rule>", "<se:Rule>" + s)
    labeling = layer.customProperty("labeling/enabled")
    labeling = str(labeling).lower() == str(True).lower()
    if labeling:
        s = getLabelingAsSld(layer)
        sld = sld.replace("<se:Rule>", "<se:Rule>" + s)
    sld = sld.replace("se:", "sld:")
    sizes = re.findall("<sld:Size>.*?</sld:Size>", sld)
    for size in sizes:
        newsize = "<sld:Size>%f</sld:Size>" % (
            float(size[10:-11]) * SIZE_FACTOR)
        sld = sld.replace(size, newsize)
    return sld


def getLabelingAsSld(layer):
    try:
        s = "<TextSymbolizer><Label>"
        s += ("<ogc:PropertyName>" + layer.customProperty("labeling/fieldName")
              + "</ogc:PropertyName>")
        s += "</Label>"
        r = int(layer.customProperty("labeling/textColorR"))
        g = int(layer.customProperty("labeling/textColorG"))
        b = int(layer.customProperty("labeling/textColorB"))
        rgb = '#%02x%02x%02x' % (r, g, b)
        s += ('<Fill><CssParameter name="fill">' + rgb
              + "</CssParameter></Fill>")
        s += "<Font>"
        s += ('<CssParameter name="font-family">'
              + layer.customProperty("labeling/fontFamily")
              + '</CssParameter>')
        s += ('<CssParameter name="font-size">'
              + str(layer.customProperty("labeling/fontSize"))
              + '</CssParameter>')
        if bool(layer.customProperty("labeling/fontItalic")):
            s += '<CssParameter name="font-style">italic</CssParameter>'
        if bool(layer.customProperty("labeling/fontBold")):
            s += '<CssParameter name="font-weight">bold</CssParameter>'
        s += "</Font>"
        s += "<LabelPlacement>"
        s += ("<PointPlacement>"
              "<AnchorPoint>"
              "<AnchorPointX>0.5</AnchorPointX>"
              "<AnchorPointY>0.5</AnchorPointY>"
              "</AnchorPoint>")
        s += "<Displacement>"
        s += ("<DisplacementX>"
              + str(layer.customProperty("labeling/xOffset"))
              + "0</DisplacementX>")
        s += ("<DisplacementY>"
              + str(layer.customProperty("labeling/yOffset"))
              + "0</DisplacementY>")
        s += "</Displacement>"
        s += ("<Rotation>"
              + str(layer.customProperty("labeling/angleOffset"))
              + "</Rotation>")
        s += "</PointPlacement></LabelPlacement>"
        s += "</TextSymbolizer>"
        return s
    except Exception:
        return ""


def adaptGsToQgs(sld):
    # TODO
    return sld


def getGsCompatibleSld(layer, style_name):
    sld = getStyleAsSld(layer, style_name)
    if sld is not None:
        return adaptQgsToGs(sld, layer)
    else:
        return None
# QDomElement QgsFeatureRenderer::writeSld( QDomDocument& doc, const QString& styleName ) const
#   492 {
#   493   QDomElement userStyleElem = doc.createElement( "UserStyle" );
#   494
#   495   QDomElement nameElem = doc.createElement( "se:Name" );
#   496   nameElem.appendChild( doc.createTextNode( styleName ) );
#   497   userStyleElem.appendChild( nameElem );
#   498
#   499   QDomElement featureTypeStyleElem = doc.createElement( "se:FeatureTypeStyle" );
#   500   toSld( doc, featureTypeStyleElem );
#   501   userStyleElem.appendChild( featureTypeStyleElem );
#   502
#   503   return userStyleElem;
#   504 }

 # void QgsRuleBasedRenderer::Rule::toSld( QDomDocument& doc, QDomElement &element, QgsStringMap props )
 #  300 {
 #  301   // do not convert this rule if there are no symbols
 #  302   if ( symbols().isEmpty() )
 #  303     return;
 #  304
 #  305   if ( !mFilterExp.isEmpty() )
 #  306   {
 #  307     if ( !props.value( "filter", "" ).isEmpty() )
 #  308       props[ "filter" ] += " AND ";
 #  309     props[ "filter" ] += mFilterExp;
 #  310   }
 #  311
 #  312   if ( mScaleMinDenom != 0 )
 #  313   {
 #  314     bool ok;
 #  315     int parentScaleMinDenom = props.value( "minimumScale", "0" ).toInt( &ok );
 #  316     if ( !ok || parentScaleMinDenom <= 0 )
 #  317       props[ "minimumScale" ] = QString::number( mScaleMinDenom );
 #  318     else
 #  319       props[ "minimumScale" ] = QString::number( qMax( parentScaleMinDenom, mScaleMinDenom ) );
 #  320   }
 #  321
 #  322   if ( mScaleMaxDenom != 0 )
 #  323   {
 #  324     bool ok;
 #  325     int parentScaleMaxDenom = props.value( "maximumScale", "0" ).toInt( &ok );
 #  326     if ( !ok || parentScaleMaxDenom <= 0 )
 #  327       props[ "maximumScale" ] = QString::number( mScaleMaxDenom );
 #  328     else
 #  329       props[ "maximumScale" ] = QString::number( qMin( parentScaleMaxDenom, mScaleMaxDenom ) );
 #  330   }
 #  331
 #  332   if ( mSymbol )
 #  333   {
 #  334     QDomElement ruleElem = doc.createElement( "se:Rule" );
 #  335     element.appendChild( ruleElem );
 #  336
 #  337     //XXX: <se:Name> is the rule identifier, but our the Rule objects
 #  338     // have no properties could be used as identifier. Use the label.
 #  339     QDomElement nameElem = doc.createElement( "se:Name" );
 #  340     nameElem.appendChild( doc.createTextNode( mLabel ) );
 #  341     ruleElem.appendChild( nameElem );
 #  342
 #  343     if ( !mLabel.isEmpty() || !mDescription.isEmpty() )
 #  344     {
 #  345       QDomElement descrElem = doc.createElement( "se:Description" );
 #  346       if ( !mLabel.isEmpty() )
 #  347       {
 #  348         QDomElement titleElem = doc.createElement( "se:Title" );
 #  349         titleElem.appendChild( doc.createTextNode( mLabel ) );
 #  350         descrElem.appendChild( titleElem );
 #  351       }
 #  352       if ( !mDescription.isEmpty() )
 #  353       {
 #  354         QDomElement abstractElem = doc.createElement( "se:Abstract" );
 #  355         abstractElem.appendChild( doc.createTextNode( mDescription ) );
 #  356         descrElem.appendChild( abstractElem );
 #  357       }
 #  358       ruleElem.appendChild( descrElem );
 #  359     }
 #  360
 #  361     if ( !props.value( "filter", "" ).isEmpty() )
 #  362     {
 #  363       QgsSymbolLayerUtils::createFunctionElement( doc, ruleElem, props.value( "filter", "" ) );
 #  364     }
 #  365
 #  366     if ( !props.value( "minimumScale", "" ).isEmpty() )
 #  367     {
 #  368       QDomElement minimumScaleElem = doc.createElement( "se:MinScaleDenominator" );
 #  369       minimumScaleElem.appendChild( doc.createTextNode( props.value( "minimumScale", "" ) ) );
 #  370       ruleElem.appendChild( minimumScaleElem );
 #  371     }
 #  372
 #  373     if ( !props.value( "maximumScale", "" ).isEmpty() )
 #  374     {
 #  375       QDomElement maximumScaleElem = doc.createElement( "se:MaxScaleDenominator" );
 #  376       maximumScaleElem.appendChild( doc.createTextNode( props.value( "maximumScale", "" ) ) );
 #  377       ruleElem.appendChild( maximumScaleElem );
 #  378     }
 #  379
 #  380     mSymbol->toSld( doc, ruleElem, props );
 #  381   }
 #  382
 #  383   // loop into childern rule list
 #  384   for ( RuleList::iterator it = mChildren.begin(); it != mChildren.end(); ++it )
 #  385   {
 #  386     ( *it )->toSld( doc, element, props );
 #  387   }
 #  388 }


def getStyleAsSld(layer, styleName):
    if layer.type() == layer.VectorLayer:
        document = QDomDocument()
        header = document.createProcessingInstruction("xml", "version=\"1.0\"")
        document.appendChild(header)

        root = document.createElementNS(
            "http://www.opengis.net/sld", "StyledLayerDescriptor")
        root.setAttribute("version", "1.0.0")
        root.setAttribute("xmlns:ogc", "http://www.opengis.net/ogc")
        root.setAttribute("xmlns:sld", "http://www.opengis.net/sld")
        # root.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink" )
        # root.setAttribute(
        #     "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance" )
        document.appendChild(root)

        namedLayerNode = document.createElement("sld:NamedLayer")
        root.appendChild(namedLayerNode)

        nameNode = document.createElement("sld:Name")
        featureTypeStyleElem = document.createElement("sld:FeatureTypeStyle")
        namedLayerNode.appendChild(nameNode)
        nameNode.appendChild(document.createTextNode(styleName))
        userNode = document.createElement("sld:UserStyle")
        namedLayerNode.appendChild(userNode)

        nameElem = document.createElement("sld:Name")
        nameElem.appendChild(document.createTextNode(styleName))
        userNode.appendChild(nameElem)
        titleElem = document.createElement("sld:Title")
        titleElem.appendChild(document.createTextNode(styleName))
        userNode.appendChild(titleElem)

        rule = layer.renderer().rootRule()
        props = {}  # QgsStringMap() can be see as a python dictionary
        rule_to_sld(rule, document, featureTypeStyleElem, props)
        userNode.appendChild(featureTypeStyleElem)

        return str(document.toString(4))
    elif layer.type() == layer.RasterLayer:
        renderer = layer.renderer()
        if isinstance(renderer, QgsSingleBandGrayRenderer):
            symbolizerCode = "<Opacity>%d</Opacity>" % renderer.opacity()
            symbolizerCode += (
                "<ChannelSelection><GrayChannel><SourceChannelName>"
                + str(renderer.grayBand())
                + "</SourceChannelName></GrayChannel></ChannelSelection>")
            sld = RASTER_SLD_TEMPLATE.replace(
                "SYMBOLIZER_CODE", symbolizerCode).replace("STYLE_NAME",
                                                           layer.name())
            return sld
        elif isinstance(renderer, QgsSingleBandPseudoColorRenderer):
            symbolizerCode = "<ColorMap>"
            # band = renderer.usesBands()[0]
            items = \
                renderer.shader().rasterShaderFunction().colorRampItemList()
            for item in items:
                color = item.color
                rgb = '#%02x%02x%02x' % (
                    color.red(), color.green(), color.blue())
                symbolizerCode += ('<ColorMapEntry color="' + rgb
                                   + '" quantity="'
                                   + str(item.value) + '" />')
            symbolizerCode += "</ColorMap>"
            sld = RASTER_SLD_TEMPLATE.replace(
                "SYMBOLIZER_CODE", symbolizerCode).replace("STYLE_NAME",
                                                           layer.name())
            return sld
        else:
            # we use some default styles in case we have an
            # unsupported renderer
            sldpath = os.path.join(
                os.path.dirname(__file__), "..", "resources")
            if layer.bandCount() == 1:
                sldfile = os.path.join(sldpath, "grayscale.sld")
            else:
                sldfile = os.path.join(sldpath, "rgb.sld")
            with open(sldfile, 'r', newline='') as f:
                sld = f.read()
            return sld
    else:
        return None


def rule_to_sld(rule, document, element, props):
    if (hasattr(rule, 'symbols') and rule.symbols()  # working before QGIS 2.12
            or hasattr(rule, 'symbols2') and rule.symbols2()):  # working after
                                                                # QGIS 2.12
        if rule.filterExpression():
            if filter in props:
                props['filter'] += " AND "
            else:
                props['filter'] = ""
            props['filter'] += rule.filterExpression()
        minimumScale = rule.minimumScale()
        if minimumScale != 0:
            ok = True
            try:
                parentScaleMinDenom = int(props.get('minimumScale', '0'))
            except ValueError:
                ok = False
            if not ok or parentScaleMinDenom <= 0:
                props['minimumScale'] = str(minimumScale)
            else:
                props['minimumScale'] = str(
                    max(parentScaleMinDenom, minimumScale))
        maximumScale = rule.maximumScale()
        if maximumScale != 0:
            ok = True
            try:
                parentScaleMaxDenom = int(props.get('maximumScale', '0'))
            except ValueError:
                ok = False
            if not ok or parentScaleMaxDenom <= 0:
                props['maximumScale'] = str(maximumScale)
            else:
                props['maximumScale'] = str(
                    min(parentScaleMaxDenom, maximumScale))

        if rule.symbol():
            ruleNode = document.createElement("sld:Rule")
            element.appendChild(ruleNode)
#  337     //XXX: <se:Name> is the rule identifier, but our the Rule objects
#  338     // have no properties could be used as identifier. Use the label.
            nameNode = document.createElement("sld:Name")
            nameNode.appendChild(document.createTextNode(rule.label()))
            ruleNode.appendChild(nameNode)
            if rule.label() or rule.description():
                descrNode = document.createElement("sld:Description")
                if rule.label():
                    titleNode = document.createElement("sld:Title")
                    titleNode.appendChild(
                        document.createTextNode(rule.label()))
                    # descrNode.appendChild(titleNode)
                    ruleNode.appendChild(titleNode)
                if rule.description():
                    abstractNode = document.createElement("sld:Abstract")
                    abstractNode.appendChild(
                        document.createTextNode(rule.description()))
                    # descrNode.appendChild(abstractNode)
                    ruleNode.appendChild(abstractNode)
                # ruleNode.appendChild(descrNode)
            if 'filter' in props:
                createFunctionElement(
                    document, ruleNode, props.get('filter', ''))
            if props.get('minimumScale', ''):
                sminNode = document.createElement("sld:MinScaleDenominator")
                sminNode.appendChild(
                    document.createTextNode(props['minimumScale']))
                descrNode.appendChild(sminNode)
            if props.get('maximumScale', ''):
                smaxNode = document.createElement("sld:MaxScaleDenominator")
                smaxNode.appendChild(
                    document.createTextNode(props['maximumScale']))
                descrNode.appendChild(smaxNode)
            symbolv2_to_sld(rule.symbol(), document, ruleNode, props)
#  379
#  380     mSymbol->toSld( doc, ruleElem, props );
#  381   }
#  382
        # loop into childern rule list
        for child in rule.children():
            rule_to_sld(child, document, element, props)
#  383   // loop into childern rule list
#  384   for ( RuleList::iterator it = mChildren.begin(); it != mChildren.end(); ++it )
#  385   {
#  386     ( *it )->toSld( doc, element, props );
#  387   }
#  388 }


def symbolv2_to_sld(symbol, document, element, props):
    props['alpha'] = str(symbol.opacity())
    scaleFactor = 1.0
    (scaleFactor, props['uom']) = encodeSldUom(symbol.outputUnit(),
                                               scaleFactor)
    props['uomScale'] = str(scaleFactor) if scaleFactor != 1 else ''
    for symbolLayer in symbol.symbolLayers():
        symbolLayer_to_sld(symbolLayer, document, element, props)


def encodeSldUom(outputUnit, scaleFactor):
    if outputUnit == QgsUnitTypes.RenderMapUnits:
        if scaleFactor:
            scaleFactor = 0.001  # from millimeters to meters
        return (scaleFactor, "http://www.opengeospatial.org/se/units/metre")
    else:
        # pixel is the SLD default uom. The "standardized rendering pixel
        # size" is defined to be 0.28mm x -1.28mm (millimeters).
        if scaleFactor:
            scaleFactor = 0.28  # from millimeters to pixels
        # http://www.opengeospatial.org/sld/units/pixel
        return (scaleFactor, 'http://www.opengeospatial.org/se/units/pixel')


def symbolLayer_to_sld(symbolLayer, document, element, props):
    if (not hasattr(symbolLayer, 'brushStyle')
            or symbolLayer.brushStyle() == Qt.NoBrush
            and symbolLayer.strokeStyle() == Qt.NoPen):
        return
    symbolizerElem = document.createElement('sld:PolygonSymbolizer')
    if 'uom' in props:
        symbolizerElem.setAttribute('uom', props['uom'])
    element.appendChild(symbolizerElem)
    # geometry
    createGeometryElement(document, symbolizerElem, props.get('geom', ''))
    if symbolLayer.brushStyle() != Qt.NoBrush:
        # fill
        fillElem = document.createElement('sld:Fill')
        symbolizerElem.appendChild(fillElem)
        fill_to_sld(symbolLayer, document, fillElem,
                    symbolLayer.brushStyle(), symbolLayer.color())
    if symbolLayer.strokeStyle() != Qt.NoPen:
        # stroke
        strokeElem = document.createElement('sld:Stroke')
        symbolizerElem.appendChild(strokeElem)
        # TODO: Add dash style and other parameters
        line_to_sld(document, strokeElem, symbolLayer.dxfPenStyle(),
                    symbolLayer.strokeColor(), symbolLayer.strokeWidth(),
                    symbolLayer.penJoinStyle(),  # penCapStyle,
                    symbolLayer.dxfCustomDashPattern()[0],
                    symbolLayer.offset())
    # Displacement
    create_displacement_element(document, element, symbolLayer.offset())


def create_displacement_element(document, element, offset):
    if not offset:
        return
    displacementElem = document.createElement('sld:Displacement')
    element.appendChild(displacementElem)
    dispXElem = document.createElement('sld:DisplacementX')
    dispXElem.appendChild(document.createTextNode(str(offset.x())))
    dispYElem = document.createElement('sld:DisplacementY')
    dispYElem.appendChild(document.createTextNode(str(offset.y())))
    displacementElem.appendChild(dispXElem)
    displacementElem.appendChild(dispYElem)


def line_to_sld(document, element, penStyle, color, width,
                penJoinStyle, customDashPattern, dashOffset):
    dashPattern = []
    if penStyle == Qt.CustomDashLine and not customDashPattern:
        element.appendChild(document.createComment(
            "WARNING: Custom dash pattern required but not provided."
            " Using default dash pattern."))
        penStyle = Qt.DashLine
    if penStyle == Qt.NoPen:
        return
    if penStyle != Qt.SolidLine:
        if penStyle == Qt.DashLine:
            dashPattern.append(4.0)
            dashPattern.append(2.0)
        elif penStyle == Qt.DotLine:
            dashPattern.append(1.0)
            dashPattern.append(2.0)
        elif penStyle == Qt.DashDotLine:
            dashPattern.append(4.0)
            dashPattern.append(2.0)
            dashPattern.append(1.0)
            dashPattern.append(2.0)
        elif penStyle == Qt.DashDotDotLine:
            dashPattern.append(4.0)
            dashPattern.append(2.0)
            dashPattern.append(1.0)
            dashPattern.append(2.0)
            dashPattern.append(1.0)
            dashPattern.append(2.0)
        else:
            element.appendChild(document.createComment(
                'BrushStyle %s not supported yet' % penStyle))
    if color.isValid():
        element.appendChild(createCssParameterElement(
            document, "stroke", color.name()))
        if color.alpha() < 255:
            element.appendChild(createCssParameterElement(
                document, "stroke-opacity",
                QgsSymbolLayerUtils.encodeSldAlpha(color.alpha())))
    if width > 0:
        element.appendChild(createCssParameterElement(
            document, "stroke-width", str(width)))
    if penJoinStyle:
        element.appendChild(createCssParameterElement(
            document, "stroke-linejoin",
            QgsSymbolLayerUtils.encodeSldLineJoinStyle(penJoinStyle)))
    # TODO: manage penCapStyle
    if len(dashPattern) > 0:
        element.appendChild(createCssParameterElement(
            document, "stroke-dasharray",
            QgsSymbolLayerUtils.encodeSldRealVector(dashPattern)))  # " ".join(dashPattern)))
        # FIXME: what's dashOffset? qgsDoubleNear expects a singular number,
        # not a tuple
        # if qgsDoubleNear(dashOffset, 0.0):
        # if abs(dashOffset - 0.0) > 1e-8:
        #     element.appendChild(createCssParameterElement(
        #         document, "stroke-dashoffset", str(dashOffset)))

 # 1763 void QgsSymbolLayerUtils::lineToSld( QDomDocument &doc, QDomElement &element,
 # 1764                                        Qt::PenStyle penStyle, QColor color, double width,
 # 1765                                        const Qt::PenJoinStyle *penJoinStyle, const Qt::PenCapStyle *penCapStyle,
 # 1766                                        const QVector<qreal> *customDashPattern, double dashOffset )
 # 1767 {
 # 1768   QVector<qreal> dashPattern;
 # 1769   const QVector<qreal> *pattern = &dashPattern;
 # 1770
 # 1771   if ( penStyle == Qt::CustomDashLine && !customDashPattern )
 # 1772   {
 # 1773     element.appendChild( doc.createComment( "WARNING: Custom dash pattern required but not provided. Using default dash pattern." ) );
 # 1774     penStyle = Qt::DashLine;
 # 1775   }
 # 1776
 # 1777   switch ( penStyle )
 # 1778   {
 # 1779     case Qt::NoPen:
 # 1780       return;
 # 1781
 # 1782     case Qt::SolidLine:
 # 1783       break;
 # 1784
 # 1785     case Qt::DashLine:
 # 1786       dashPattern.push_back( 4.0 );
 # 1787       dashPattern.push_back( 2.0 );
 # 1788       break;
 # 1789     case Qt::DotLine:
 # 1790       dashPattern.push_back( 1.0 );
 # 1791       dashPattern.push_back( 2.0 );
 # 1792       break;
 # 1793     case Qt::DashDotLine:
 # 1794       dashPattern.push_back( 4.0 );
 # 1795       dashPattern.push_back( 2.0 );
 # 1796       dashPattern.push_back( 1.0 );
 # 1797       dashPattern.push_back( 2.0 );
 # 1798       break;
 # 1799     case Qt::DashDotDotLine:
 # 1800       dashPattern.push_back( 4.0 );
 # 1801       dashPattern.push_back( 2.0 );
 # 1802       dashPattern.push_back( 1.0 );
 # 1803       dashPattern.push_back( 2.0 );
 # 1804       dashPattern.push_back( 1.0 );
 # 1805       dashPattern.push_back( 2.0 );
 # 1806       break;
 # 1807
 # 1808     case Qt::CustomDashLine:
 # 1809       Q_ASSERT( customDashPattern );
 # 1810       pattern = customDashPattern;
 # 1811       break;
 # 1812
 # 1813     default:
 # 1814       element.appendChild( doc.createComment( QString( "Qt::BrushStyle '%1'' not supported yet" ).arg( penStyle ) ) );
 # 1815       return;
 # 1816   }
 # 1817
 # 1818   if ( color.isValid() )
 # 1819   {
 # 1820     element.appendChild( createSvgParameterElement( doc, "stroke", color.name() ) );
 # 1821     if ( color.alpha() < 255 )
 # 1822       element.appendChild( createSvgParameterElement( doc, "stroke-opacity", encodeSldAlpha( color.alpha() ) ) );
 # 1823   }
 # 1824   if ( width > 0 )
 # 1825     element.appendChild( createSvgParameterElement( doc, "stroke-width", QString::number( width ) ) );
 # 1826   if ( penJoinStyle )
 # 1827     element.appendChild( createSvgParameterElement( doc, "stroke-linejoin", encodeSldLineJoinStyle( *penJoinStyle ) ) );
 # 1828   if ( penCapStyle )
 # 1829     element.appendChild( createSvgParameterElement( doc, "stroke-linecap", encodeSldLineCapStyle( *penCapStyle ) ) );
 # 1830
 # 1831   if ( pattern->size() > 0 )
 # 1832   {
 # 1833     element.appendChild( createSvgParameterElement( doc, "stroke-dasharray", encodeSldRealVector( *pattern ) ) );
 # 1834     if ( !qgsDoubleNear( dashOffset, 0.0 ) )
 # 1835       element.appendChild( createSvgParameterElement( doc, "stroke-dashoffset", QString::number( dashOffset ) ) );
 # 1836   }
 # 1837 }

  # 448 QString QgsSymbolLayerUtils::encodeSldRealVector( const QVector<qreal>& v )
  # 449 {
  # 450   QString vectorString;
  # 451   QVector<qreal>::const_iterator it = v.constBegin();
  # 452   for ( ; it != v.constEnd(); ++it )
  # 453   {
  # 454     if ( it != v.constBegin() )
  # 455     {
  # 456       vectorString.append( " " );
  # 457     }
  # 458     vectorString.append( QString::number( *it ) );
  # 459   }
  # 460   return vectorString;
  # 461 }


def createCssParameterElement(document, name, value):
    nodeElem = document.createElement('sld:CssParameter')
    nodeElem.setAttribute('name', name)
    nodeElem.appendChild(document.createTextNode(value))
    return nodeElem
 # 2515 QDomElement QgsSymbolLayerUtils::createSvgParameterElement( QDomDocument &doc, QString name, QString value )
 # 2516 {
 # 2517   QDomElement nodeElem = doc.createElement( "se:SvgParameter" );
 # 2518   nodeElem.setAttribute( "name", name );
 # 2519   nodeElem.appendChild( doc.createTextNode( value ) );
 # 2520   return nodeElem;
 # 2521 }


def fill_to_sld(symbolLayer, document, element, brushStyle, color):
    patternName = ''
    if brushStyle == Qt.NoBrush:
        return
    elif brushStyle == Qt.SolidPattern:
        if color.isValid():
            cssElement = createCssParameterElement(document,
                                                   'fill',
                                                   color.name())
            element.appendChild(cssElement)
            if color.alpha() < 255:
                cssElement = createCssParameterElement(
                    document, 'fill-opacity',
                    QgsSymbolLayerUtils.encodeSldAlpha(color.alpha()))
                element.appendChild()
        return
    elif brushStyle in (Qt.CrossPattern,
                        Qt.CrossPattern,
                        Qt.DiagCrossPattern,
                        Qt.HorPattern,
                        Qt.VerPattern,
                        Qt.BDiagPattern,
                        Qt.FDiagPattern,
                        Qt.Dense1Pattern,
                        Qt.Dense2Pattern,
                        Qt.Dense3Pattern,
                        Qt.Dense4Pattern,
                        Qt.Dense5Pattern,
                        Qt.Dense6Pattern,
                        Qt.Dense7Pattern,
                        ):
        patternName = QgsSymbolLayerUtils.encodeSldBrushStyle(brushStyle)
        return
    else:
        element.appendChild(document.createComment('Brush not supported'))
    graphicFillElem = document.createElement('sld:GraphicFill')
    element.appendChild(graphicFillElem)
    graphicElem = document.createElement('sld:Graphic')
    element.appendChild(graphicElem)
    fillColor = color if patternName.startswith('brush://') else Qt.QColor()
    strokeColor = \
        color if not patternName.startswith('brush://') else Qt.QColor()
    # Use WellKnownName tag to handle QT brush styles.
    QgsSymbolLayerUtils.wellKnownMarkerToSld(
        document, graphicElem, patternName, fillColor,
        strokeColor, Qt.SolidLine, -1, -1)


def createGeometryElement(document, element, geomFunc):
    if not geomFunc:
        return
    geometryElem = document.createElement('Geometry')
    element.appendChild(geometryElem)
    createFunctionElement(document, geometryElem, geomFunc)
# void QgsSymbolLayerUtils::createGeometryElement( QDomDocument &doc, QDomElement &element, QString geomFunc )
#  2388 {
#  2389   if ( geomFunc.isEmpty() )
#  2390     return;
#  2391
#  2392   QDomElement geometryElem = doc.createElement( "Geometry" );
#  2393   element.appendChild( geometryElem );
#  2394
#  2395   /* About using a function withing the Geometry tag.
#  2396    *
#  2397    * The SLD specification <= 1.1 is vague:
#  2398    * "In principle, a fixed geometry could be defined using GML or
#  2399    * operators could be defined for computing the geometry from
#  2400    * references or literals. However, using a feature property directly
#  2401    * is by far the most commonly useful method."
#  2402    *
#  2403    * Even if it seems that specs should take care all the possible cases,
#  2404    * looking at the XML schema fragment that encodes the Geometry element,
#  2405    * it has to be a PropertyName element:
#  2406    *   <xsd:element name="Geometry">
#  2407    *       <xsd:complexType>
#  2408    *           <xsd:sequence>
#  2409    *               <xsd:element ref="ogc:PropertyName"/>
#  2410    *           </xsd:sequence>
#  2411    *       </xsd:complexType>
#  2412    *   </xsd:element>
#  2413    *
#  2414    * Anyway we will use a ogc:Function to handle geometry transformations
#  2415    * like offset, centroid, ...
#  2416    */
#  2417
#  2418   createFunctionElement( doc, geometryElem, geomFunc );
#  2419 }


def createFunctionElement(document, element, function):
    expr = QgsExpression(function)
    if expr.hasParserError():
        element.appendChild(document.createComment("Parser Error"))
        return False
    filterElem = QgsOgcUtils.expressionToOgcFilter(expr, document)
    if filterElem:
        element.appendChild(filterElem)  # NOTE: in qgis2 filterElem was tuple
    return True

# bool QgsSymbolLayerUtils::createFunctionElement( QDomDocument &doc, QDomElement &element, QString function )
#  2431 {
#  2432   // let's use QgsExpression to generate the SLD for the function
#  2433   QgsExpression expr( function );
#  2434   if ( expr.hasParserError() )
#  2435   {
#  2436     element.appendChild( doc.createComment( "Parser Error: " + expr.parserErrorString() + " - Expression was: " + function ) );
#  2437     return false;
#  2438   }
#  2439   QDomElement filterElem = QgsOgcUtils::expressionToOgcFilter( expr, doc );
#  2440   if ( !filterElem.isNull() )
#  2441     element.appendChild( filterElem );
#  2442   return true;
#  2443 }


def getGeomTypeFromSld(sld):
    if "PointSymbolizer" in sld:
        return "Point"
    elif "LineSymbolizer" in sld:
        return "LineString"
    else:
        return "Polygon"
