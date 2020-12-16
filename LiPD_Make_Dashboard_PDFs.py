#!/usr/bin/env python
# -*- coding: utf-8 -*-
#==============================================================================
# Routines for creating pdf/LiDP dashboard files:
#
#------------------------------------------------------------------------------
# Notes:
#
#------------------------------------------------------------------------------
# By John Vitkovsky
# Modified 02-11-2020
# Queensland Hydrology, Queensland Government
#
#==============================================================================


# Modules: 
import sys, os
import numpy as np
import pandas as pd
import datetime as dt

# Graphics modules:
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import shapely

# LiPD module:
#import lipd
import LiPD_Extra_Routines as xlipd

# ReportLab module:
import io
from reportlab.pdfgen import canvas
#from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import cm

from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

from reportlab.pdfbase.pdfmetrics import stringWidth

from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

import textwrap


# Variables:
DEBUG = 0  # 0=None, 1=Some, 2=More


#==============================================================================
# MAIN
#==============================================================================
def main(argv):

    # Set variables:
    # proxy_path = '.\\proxies\\LiPDs_20201130'
    # proxy_list = '_LiPD_List_Proxies.txt'
    # pdf_file = '.\\output\\dashboard_pdfs\\LiPD_Dashboards_20201130_Proxies.pdf'
    # ----------
    proxy_path = '.\\proxies\\LiPDs_20201214'
    proxy_list = '_LiPD_List.txt'
    pdf_file = '.\\output\\dashboard_pdfs\\LiPD_Dashboards_20201214.pdf'
    # ----------
    map_legend_flag = False
    #bbox_dx = 20.0  # Bounding box side in degrees
    #fig_dpi = 300  # Figure DPI setting for PNG

    # Define colours:
    source_ec = (0.00, 0.00, 1.00)  # Marker/polygon edge colour
    source_pc = (0.00, 0.00, 1.00, 0.15)  # Polygon face colour (transparant)
    source_fc = (0.85, 0.85, 1.00)  # Marker face colour (a=0.15)
    source_lc = (0.65, 0.65, 1.00)  # Line colour (a=0.35)
    # ----------
    target_ec = (1.00, 0.45, 0.00)  # Marker/polygon edge colour
    target_pc = (1.00, 0.45, 0.00, 0.15)  # Polygon face colour (transparant)
    target_fc = (1.00, 0.92, 0.85)  # Marker face colour (a=0.15)
    target_lc = (1.00, 0.75, 0.55)  # Line colour (a=0.45)
    
    # Get list of files from proxy_list:
    proxy_files = []
    f = open(proxy_path + '\\' + proxy_list, 'r')
    for i in f:
        if i.strip()[0] != '#':
            proxy_files.append(i.strip())
        # end if
    # end for
    f.close()

    # Print program details
    print ('\nCreate dashboard PDF from LiPD files:')
    print ('  proxy_path =', proxy_path)
    print ('  proxy_list =', proxy_list)
    print ('  pdf_file =', pdf_file)
    if DEBUG > 0:
        print ('  proxy_files:')
        for i in proxy_files:
            print('    "' + i + '"')
        # end for
    # end if

    # Open up a new PDF canvas:
    print('\nCreating pdf file')
    c = canvas.Canvas(pdf_file, pagesize=portrait(A4))
    c_width, c_height = portrait(A4)

    # Loop through LiPD files:
    num_pages = (len(proxy_files) - 1)// 2 + 1
    page = 0  # Page counter
    item_top = True  # True if is item top of page (two items per page)
    i_xloc = 1*cm
    i_width = c_width - 2*cm
    i_height = c_height/2 - 1.5*cm
    print('\nLooping through LiPD files:')
    for PF in proxy_files:
        print('  "' + PF + '"')

        # Deal with top or bottom page items:
        if item_top:
            page += 1
            if page > 1: c.showPage()
            i_yloc = c_height/2 + 0.5*cm
            # Write date:
            c.setFont('Helvetica-Oblique', 9)
            c.drawRightString(c_width - 1.0*cm, c_height - 0.6*cm,
                              'Created: ' + dt.datetime.now().strftime('%d-%b-%G')) 
            # Write page number:
            c.setFont('Helvetica', 9)
            c.drawCentredString(c_width / 2.0,  0.4*cm,
                                'Page ' + str(page) + ' of ' + str(num_pages))
        else:
            i_yloc = 1*cm
        # end if
        item_top = not item_top
        
        # Draw bounding rectangle:
        c.rect(i_xloc, i_yloc, i_width, i_height, stroke=1, fill=0)

        # Open LiPD metadata:
        LMeta = xlipd.Read_JSON(proxy_path + '\\' + PF)
        #print(LMeta.keys())

        # Get subsets:
        LPub = LMeta['pub']
        #print(LPub.keys())

        # Get measurment table #1:
        LTab = LMeta['paleoData'][0]['measurementTable'][0]
        LTab_columns = len(LTab['columns'])
        if DEBUG > 0:
            print('LTab_columns =', LTab_columns)

        # Find first "year" or "age" column:
        x_col_1 = None
        # ---Try to find "YEAR CE/BCE"---
        for i in range(LTab_columns):
            stmp = xlipd.extract_string1(LTab['columns'][i], 'variableName', False, 'NA')
            if stmp.split(' ')[0].upper() == 'YEAR':
                x_col_1 = i
                break
            # end if
        # end for
        # ---Else try to find "AGE"---
        if x_col_1 == None:
            for i in range(LTab_columns):
                stmp = xlipd.extract_string1(LTab['columns'][i], 'variableName', False, 'NA')
                if stmp.split(' ')[0].upper() == 'AGE':
                    x_col_1 = i
                    break
                # end if
            # end for
        # end if
        # ---Otherwise report error---
        if x_col_1 == None:
            print('Can\'t find year or age column')
            sys.exit()
        # end if

        # Find dataset column (first with "variableType" = PROXY or RECONSTRUCTION):
        x_col_2 = None
        # ---First "variableType" with PROXY or RECONSTRUCTION---
        # for i in range(LTab_columns):
        #     stmp = xlipd.extract_string1(LTab['columns'][i], 'variableType', False, 'NA')
        #     if stmp.upper() in ['PROXY', 'RECONSTRUCTION']: 
        #         x_col_2 = i
        #         break
        #     # end if
        # # end for
        # ---Use specific column---
        # x_col_2 = LTab_columns - 1  # Use last column
        x_col_2 = LTab_columns - 2  # Use 2nd last column (last is QC)
        # ---Otherwise report error---
        if x_col_2 == None:
            print('Can\'t find dataset column')
            sys.exit()
        # end if

        # Get table dataframe:
        x_file = LTab['filename']
        x_df = xlipd.Read_CSV2DF(proxy_path + '\\' + PF, x_file)
        x_df = x_df.sort_values(by=x_df.columns[x_col_1], ascending=True)
        if DEBUG > 0:
            print('x_file =', x_file)
            print('x_col_1 =', x_col_1)
            print('x_col_2 =', x_col_2)
            print('x_df:')
            print(x_df)
        # end if
        
        # Check if proxy or reconstruction:
        # x_type = xlipd.extract_string1(LTab['columns'][x_col_2], 'variableType', 'NA')  # OLD
        x_type = xlipd.extract_string1(LTab['columns'][x_col_2]['datasetType'], 'type', 'NA')
        x_type = x_type.strip().upper()
        # print('x_type = ', x_type)
 
        # If reconstruction check for "interpretation":
        stmp = xlipd.extract_string1(LTab['columns'][x_col_2]['interpretationFormat'], 
                                     'format', False, 'NA')
        x_interp = not (stmp.strip().upper() in ['NONE', 'NULL', 'NA'])
        #print('x_interp = ', x_interp)
 
    
        # ---Data Information--------------------------------------------------

        # Write dataset_name:
        stmp = 'Dataset Name: ' + LMeta['dataSetName']
        stmp = trim_string(stmp, 'Helvetica-Bold', 12, c_width - 3.0*cm)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(i_xloc + 0.5*cm, i_yloc + i_height - 0.7*cm, stmp)

        # Write dataset_id and reference_id:
        c.setFont('Helvetica', 10)
        stmp1 = xlipd.extract_string1(LMeta, 'dataSetID', False, 'NA')
        stmp2 = xlipd.extract_string1(LMeta, 'referenceID', False, 'NA')
        c.drawString(i_xloc + 0.5*cm, i_yloc + i_height - 1.2*cm,
                     'Dataset ID: ' + stmp1 + '; Reference ID: ' + stmp2 )

        # Set up paragraph and table styles:
        pstyle = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=8,
                                leftIndent=20, firstLineIndent=-20, leading=12)
        twidth = (c_width - 3.5*cm) / 2.0
        theight = 5.0*cm
        tstyle = TableStyle([('VALIGN', (0,0), (0,0), 'TOP'),
                             #('BOX', (0,0), (0,0), 0.5, colors.red),
                             ('LEFTPADDING', (0,0), (0,0), 0),
                             ('RIGHTPADDING', (0,0), (0,0), 0),
                             ('TOPPADDING', (0,0), (0,0), 0),
                             ('BOTTOMPADDING', (0,0), (0,0), 0)])

        # Write metadata in column 1:
        tpara = []
        # ---LPub----------------------
        # ---Author--------------------
        # stmp = xlipd.extract_string1(LPub, 'author', False, 'NA')
        # stmp1 = xlipd.extract_string1(LPub, 'year', False, 'NA')
        # if is_number(stmp1): stmp1 = str(int(float(stmp1)))
        # tpara.append(Paragraph('Author: ' + stmp + ' <i>et al</i>. (' + stmp1 +')', pstyle))
        # ---Citation------------------
        stmp = xlipd.extract_string1(LPub, 'citation', False, 'NA')
        i = stmp.find('http')
        if i > 0: stmp = stmp[:i-1]
        if stmp[-1] == ',': stmp = stmp[:-1] + '.'
        tpara.append(Paragraph('Citation: ' + stmp, pstyle))
        # ---Citation DOI--------------
        # Also try to remove dataURL from citation if it exists.
        stmp = xlipd.extract_string1(LPub, 'doi', False, 'NA')
        stmp1 = None
        i = stmp.upper().find('DOI.ORG')
        if i >= 0:
            stmp = stmp[i+8:]
            stmp1 = 'https://doi.org/' + stmp
        # end if
        i = stmp.upper().find('DOI:')
        if i >= 0:
            stmp = stmp[i+4:].strip()
            stmp1 = 'https://doi.org/' + stmp
        # end if
        i = stmp.upper().find('HTTP')
        if i >= 0:
            stmp1 = stmp
        # end if
        stmp = trim_string('Citation DOI: ' + stmp, 'Helvetica', 8, twidth)
        stmp = stmp[14:]
        if not stmp1 is None:
            stmp = '<link href="' + stmp1 + '" color="blue"><u>' + stmp + '</u></link>'
        # end if
        tpara.append(Paragraph('Citation DOI: ' + stmp, pstyle))
        # ---Data Citation-------------
        # Also try to remove dataURL from citation if it exists.
        stmp = xlipd.extract_string1(LPub, 'dataCitation', False, 'NA')
        i = stmp.find('http')
        if i > 0:
            j = stmp[i:].find(' ')
            if j > 0:
                stmp = stmp[:i-1] + stmp[i+j:]
            else:
                stmp = stmp[:i-1]
            # end if
        # end if
        stmp = stmp.strip()
        if stmp[-1] == ',': stmp = stmp[:-1] + '.'
        if stmp[-1] != '.': stmp = stmp + '.'
        tpara.append(Paragraph('Data Citation: ' + stmp, pstyle))
        # ---Data URL------------------
        stmp = xlipd.extract_string1(LPub, 'dataUrl', False, 'NA')
        stmp1 = None
        i = stmp.upper().find('DOI:')
        if i >= 0:
            stmp = 'https://doi.org/' + stmp[i+4:].strip()
        # end if
        i = stmp.upper().find('HTTP')
        if i >= 0:
            stmp1 = stmp
        # end if
        stmp = trim_string('Data URL: ' + stmp, 'Helvetica', 8, twidth)
        stmp = stmp[10:]
        if not stmp1 is None:
            stmp = '<link href="' + stmp1 + '" color="blue"><u>' + stmp + '</u></link>'
        # end if
        tpara.append(Paragraph('Data URL: ' + stmp, pstyle))
        # ---Table---------------------
        tdata = [[tpara]]
        t = Table(tdata, colWidths=twidth, rowHeights=theight, style=tstyle)
        t.wrapOn(c, twidth, theight)
        t.drawOn(c, i_xloc + 0.5*cm, i_yloc + i_height - 1.7*cm - theight)

        # Write metadata in column 2:
        tpara = []
        # ---Data-------
        stmp = xlipd.extract_string1(LMeta['geo'], 'siteName', False, 'NA')
        tpara.append(Paragraph('Site Name: ' + stmp, pstyle))
        # ----------
        stmp = xlipd.extract_string1(LMeta, 'archiveType', False, 'NA')
        tpara.append(Paragraph('Archive Type: ' + stmp, pstyle))
        # ----------
        stmp = xlipd.extract_string1(LTab['columns'][x_col_2], 'variableType', False, 'NA')
        #stmp = 'Proxy'
        tpara.append(Paragraph('Variable Type: ' + stmp, pstyle))
        # ----------
        stmp = xlipd.extract_string1(LTab['columns'][x_col_2], 'variableName', False, 'NA')
        tpara.append(Paragraph('Variable Name: ' + stmp, pstyle))
        # ----------
        stmp = xlipd.extract_string1(LTab['columns'][x_col_2], 'units', False, 'NA')
        tpara.append(Paragraph('Variable Units: ' + stmp, pstyle))
        # ----------
        if x_type == 'PROXY':
            stmp = xlipd.extract_string1(LTab['columns'][x_col_2], 'climateParameter', False, 'NA')
            tpara.append(Paragraph('Climate Parameter: ' + stmp, pstyle))
        # end if
        # ----------
        stmp = xlipd.extract_string1(LTab['columns'][x_col_1], 'startYear', False, 'NA')
        if is_number(stmp): stmp = str(int(float(stmp)))
        tpara.append(Paragraph('Start Year: ' + stmp + ' CE', pstyle))
        # ----------
        stmp = xlipd.extract_string1(LTab['columns'][x_col_1], 'endYear', False, 'NA')
        if is_number(stmp): stmp = str(int(float(stmp)))
        tpara.append(Paragraph('End Year: ' + stmp + ' CE', pstyle))
        # ---Table-------
        tdata = [[tpara]]
        t = Table(tdata, colWidths=twidth, rowHeights=theight, style=tstyle)
        t.wrapOn(c, twidth, theight)
        t.drawOn(c, i_xloc + 1.0*cm + twidth, i_yloc + i_height - 1.7*cm - theight)


        # ---Time Series Graph-------------------------------------------------

        # Replace data values of "-999" within tolerance with NaN:
        x_df.loc[abs(x_df[x_col_2] + 999.0) < 0.001, x_col_2] = np.nan

        # Get axis labels:
        stmp = xlipd.extract_string1(LTab['columns'][x_col_1], 'variableName', False, 'NA')
        stmp1 = xlipd.extract_string1(LTab['columns'][x_col_1], 'units', False, 'NA')
        if stmp1.strip().upper() in ['UNITLESS', 'NA']: stmp1 = '-'
        x_label = stmp + ' (' + stmp1 + ')'
        # ----------
        stmp = xlipd.extract_string1(LTab['columns'][x_col_2], 'variableName', False, 'NA')
        if x_interp:
            stmp1 = xlipd.extract_string1(LTab['columns'][x_col_2]['interpretationFormat'], 'format', False, 'NA')
        else:
            stmp1 = xlipd.extract_string1(LTab['columns'][x_col_2], 'units', False, 'NA')
        # end if
        if stmp1.strip().upper() in ['UNITLESS', 'NA']: stmp1 = '-'
        y_label = stmp + ' (' + stmp1 + ')'
        y_label = textwrap.fill(y_label, 40)

        # Make graph:
        fig = plt.figure(figsize=(12, 6))
        plt.xlabel(x_label, fontsize=14, fontweight='bold', wrap=True)
        plt.ylabel(y_label, fontsize=14, fontweight='bold', wrap=True)
        if x_type == 'PROXY':
            if x_interp:
                ymin = min(-3.0, min(x_df.iloc[:,x_col_2])) * 1.05
                ymax = max( 3.0, max(x_df.iloc[:,x_col_2])) * 1.05
                plt.ylim([ymin, ymax])
                plt.axhline(0.0, color='grey', linewidth=0.5, zorder=1)
                plt.bar(x_df.iloc[:,x_col_1], x_df.iloc[:,x_col_2], 
                        width=1.0, color=source_fc, linewidth=0.5,
                        edgecolor=source_ec, zorder=2)
            else:
                plt.plot(x_df.iloc[:,x_col_1], x_df.iloc[:,x_col_2], 
                         color=source_lc, linewidth=0.5,
                         marker='o', markersize=5.0, markerfacecolor=source_fc,
                         markeredgecolor=source_ec, markeredgewidth=1.0)
            # end if
        else:
            if x_interp:
                ymin = min(-3.0, min(x_df.iloc[:,x_col_2])) * 1.05
                ymax = max( 3.0, max(x_df.iloc[:,x_col_2])) * 1.05
                plt.ylim([ymin, ymax])
                plt.axhline(0.0, color='grey', linewidth=0.5, zorder=1)
                plt.bar(x_df.iloc[:,x_col_1], x_df.iloc[:,x_col_2], 
                        width=1.0, color=target_fc, linewidth=0.5,
                        edgecolor=target_ec, zorder=2)
            else:
                plt.plot(x_df.iloc[:,x_col_1], x_df.iloc[:,x_col_2], 
                         color=target_lc, linewidth=0.5,
                         marker='o', markersize=5.0, markerfacecolor=target_fc,
                         markeredgecolor=target_ec, markeredgewidth=1.0)
            # end if
        # end if

        # Show graph:
        #plt.show()
     
        # Put graph on PDF as PNG:
        # imgdata = io.BytesIO()
        # fig.savefig(imgdata, dpi=fig_dpi, format='png', bbox_inches='tight')
        # imgdata.seek(0)  # rewind the data
        # imgreader = ImageReader(imgdata)
        # c.drawImage(imgreader, i_xloc+0.5*cm, i_yloc+0.5*cm, 12*cm, 6*cm)

        # Put graph on PDF as SVG:
        svg_file = io.BytesIO()
        fig.savefig(svg_file, format='svg', bbox_inches='tight')
        svg_file.seek(0)  # rewind the data
        drawing = svg2rlg(svg_file)
        scaled_drawing = resize_drawing(drawing, 'height', 6*cm)    
        renderPDF.draw(scaled_drawing, c, i_xloc+0.5*cm, i_yloc+0.5*cm)

        # Close graph:
        plt.close()

    
        # ---Locality Map------------------------------------------------------

        # Get coordinates:
        plon = LMeta['geo']['geometry']['coordinates'][0]
        plat = LMeta['geo']['geometry']['coordinates'][1]
        proj = ccrs.Orthographic(central_longitude=plon, central_latitude=plat)
        proj._threshold /= 100.0  # To make geodesic lines smoother

        # Create map:
        fig = plt.figure(figsize=(5, 5))
        ax = plt.axes(projection=proj)
    
        # Add coastlines and grid:
        ax.coastlines(resolution='110m', zorder=1)
        ax.gridlines(zorder=1)
        ax.set_global()
    
        # Add location point:
        # plt.scatter(plon, plat, s=50, c=(0.0,0.0,1.0,0.35), marker='o',
        #             edgecolors='blue', linewidths=1,
        #             transform=proj)
        #             #transform=ccrs.PlateCarree())
    
        # Add bounding box or circle with user-defined radius:
        # proj = ccrs.Orthographic(central_longitude=plon, central_latitude=plat)
        # r_ortho = compute_radius(plon, plat, proj, bbox_dx/2)
        # ax.add_patch(mpatches.Circle(xy=[plon, plat],
        #                                 radius=r_ortho,
        #                                 facecolor=(0.0,0.0,1.0,0.15),
        #                                 edgecolor='blue', linewidth=1,
        #                                 transform=proj))
        # ax.add_patch(mpatches.Rectangle(xy=[plon-r_ortho, plat-r_ortho],
        #                                 width=2*r_ortho, height=2*r_ortho,
        #                                 facecolor=(0.0,0.0,1.0,0.15), 
        #                                 edgecolor='blue', linewidth=1,
        #                                 transform=proj))

        # Add target bounding box or point:
        bbstr = LMeta['geo']['detailedCoordinates']['target']['values']
        if bbstr is None: bbstr = 'NA,NA,NA,NA,NA'
        bbstrs = [x for x in bbstr.split(',')]
        if is_number(bbstrs[0]):
            bblon1 = float(bbstrs[0])
            if is_number(bbstrs[1]):
                bblon2 = float(bbstrs[1])
            else:
                bblon2 = bblon1
            # end if
            bblat1 = float(bbstrs[2])
            if is_number(bbstrs[3]):
                bblat2 = float(bbstrs[3])
            else:
                bblat2 = bblat1
            # end if
            if (bblon1 < 0.0): bblon1 += 360.0  # Deal with +/-180 degrees
            if (bblon2 < 0.0): bblon2 += 360.0  # Deal with +/-180 degrees
            if abs(bblon2-bblon1) > 1.0 and abs(bblat2-bblat1) > 1.0:
                poly_corners = np.zeros((4, 2), np.float64)
                poly_corners[:,0] = [bblon1, bblon2, bblon2, bblon1]  # Anticlockwise from bottom left
                poly_corners[:,1] = [bblat1, bblat1, bblat2, bblat2]
                p = shapely.geometry.Polygon(poly_corners)
                if p.exterior.is_ccw == False:
                    poly_corners = np.flip(poly_corners, axis=0)  # Fix polygon orientation 
                ax.add_patch(mpatches.Polygon(poly_corners, closed=True, fill=True,
                                              fc=target_pc, ec=target_ec, lw=1.0,
                                              transform=ccrs.Geodetic()))
            else:
                plt.scatter(bblon1, bblat1, marker='D', s=50,
                            c=np.atleast_2d(target_pc), ec=target_ec, lw=1.0,
                            transform=ccrs.PlateCarree())
            # end if
        # end if

        # Add source bounding box or point:
        bbstr = LMeta['geo']['detailedCoordinates']['source']['values']
        if bbstr is None: bbstr = 'NA,NA,NA,NA,NA'
        bbstrs = [x for x in bbstr.split(',')]
        if is_number(bbstrs[0]):
            bblon1 = float(bbstrs[0])
            if is_number(bbstrs[1]):
                bblon2 = float(bbstrs[1])
            else:
                bblon2 = bblon1
            # end if
            bblat1 = float(bbstrs[2])
            if is_number(bbstrs[3]):
                bblat2 = float(bbstrs[3])
            else:
                bblat2 = bblat1
            # end if
            if (bblon1 < 0.0): bblon1 += 360.0  # Deal with +/-180 degrees
            if (bblon2 < 0.0): bblon2 += 360.0  # Deal with +/-180 degrees
            if abs(bblon2-bblon1) > 1.0 and abs(bblat2-bblat1) > 1.0:
                poly_corners = np.zeros((4, 2), np.float64)
                poly_corners[:,0] = [bblon1, bblon2, bblon2, bblon1]  # Anticlockwise from bottom left
                poly_corners[:,1] = [bblat1, bblat1, bblat2, bblat2]
                p = shapely.geometry.Polygon(poly_corners)
                if p.exterior.is_ccw == False:
                    poly_corners = np.flip(poly_corners, axis=0)  # Fix polygon orientation 
                ax.add_patch(mpatches.Polygon(poly_corners, closed=True, fill=True,
                                              fc=source_pc, ec=source_ec, lw=1.0, 
                                              transform=ccrs.Geodetic()))
            else:
                plt.scatter(bblon1, bblat1, marker='s', s=50, 
                            c=np.atleast_2d(source_pc), ec=source_ec, lw=1.0,
                            transform=ccrs.PlateCarree())
            # end if
        # end if

        # plt.scatter(plon, plat, marker='s', s=50, 
        #             c=np.atleast_2d(source_pc), ec=source_ec, lw=1.0,
        #             transform=ccrs.PlateCarree())


        # Add custom legend:
        if map_legend_flag:
            legend_elements = [Line2D([0], [0], marker='s', label='Source',
                                      c=source_ec, lw=1.0,
                                      mfc=source_fc, mec=source_ec, mew=1.0),
                               Line2D([0], [0], marker='D', label='Target',
                                      c=target_ec, lw=1.0,
                                      mfc=target_fc, mec=target_ec, mew=1.0)]
            ax.legend(handles=legend_elements, loc='upper right')
        # end if

        # Show graph:
        # plt.show()
    
        # Put map on PDF as PNG:
        # imgdata = io.BytesIO()
        # fig.savefig(imgdata, dpi=fig_dpi, format='png', bbox_inches='tight')
        # imgdata.seek(0)  # rewind the data
        # imgreader = ImageReader(imgdata)
        # c.drawImage(imgreader, i_xloc + 13.25*cm, i_yloc + 1.25*cm, 5*cm, 5*cm)

        # Put graph on PDF as SVG:
        svg_file = io.BytesIO()
        fig.savefig(svg_file, format='svg', bbox_inches='tight')
        svg_file.seek(0)  # rewind the data
        drawing = svg2rlg(svg_file)
        scaled_drawing = resize_drawing(drawing, 'height', 5*cm)    
        renderPDF.draw(scaled_drawing, c, i_xloc + 13.25*cm, i_yloc + 1.25*cm)

        # Close graph:
        plt.close()

        #----------------------------------------------------------------------
        
    # end for

    # Save pdf:
    c.save()
    
    # Clean up:
    del x_df

# end def




#------------------------------------------------------------------------------
# Computes the radius in orthographic coordinates
#   https://stackoverflow.com/questions/52105543/drawing-circles-with-cartopy-in-orthographic-projection/52117339
#------------------------------------------------------------------------------
def compute_radius(lon, lat, ortho, radius_degrees):
    if lat <= 0:
        phi1 = lat + radius_degrees
    else:
        phi1 = lat - radius_degrees
    _, y1 = ortho.transform_point(lon, phi1, ccrs.PlateCarree())
    return abs(y1)
# end def




#------------------------------------------------------------------------------
# Resize ReportLab drawing
#   - Maintain aspect ratio.
#------------------------------------------------------------------------------
def resize_drawing(drawing, resize_type='scale', resize_value=1.0):
    
    # Resize based on scaling factor:
    if resize_type.upper() == 'SCALE':
        scaling = resize_value
        
    # Resize to target width:
    elif resize_type.upper() == 'WIDTH':
        scaling = resize_value / drawing.minWidth()
        
    # Resize to target height:
    elif resize_type.upper() == 'HEIGHT':
        scaling = resize_value / drawing.height
       
    # Unknown resizing type:
    else:
        print('\nUnknown resize type:', resize_type)
        sys.exit()

    # end if

    # Rescale drawing:
    drawing.width = drawing.minWidth() * scaling
    drawing.height = drawing.height * scaling
    drawing.scale(scaling, scaling)
    return drawing

# end def




#------------------------------------------------------------------------------
# Trim string to fit within width (ReportLab drawString)
#------------------------------------------------------------------------------
def trim_string(string, fontName, fontSize, maxWidth):
    
    if stringWidth(string, fontName, fontSize) > maxWidth:
        string = string + '...'
        while stringWidth(string, fontName, fontSize) > maxWidth:
            string = string[:-4] + '...'
        # end while
    # end if
    return string

# end def




#------------------------------------------------------------------------------
# Check if "is number?"
#------------------------------------------------------------------------------
def is_number(n):

    is_number = True
    try:
        num = float(n)
        is_number = num == num   # check for "nan" floats
    except ValueError:
        is_number = False
    return is_number

# end def




# In case running from command-line:
if __name__ == "__main__":
    main(sys.argv)

