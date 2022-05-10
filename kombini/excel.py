#==============================================================================
"""
    name:           
    description:    
    started:        
    (c) Alfred LEUNG
"""
#==============================================================================

#==============================================================================
# Imports
#==============================================================================
#-System-----------------------------------------------------------------------
import datetime
#-Third party------------------------------------------------------------------
import xlrd
import xlsxwriter
import numpy as np
#-Own modules (different packages)---------------------------------------------
#-Own modules (same package)---------------------------------------------------
from outils.logger      import default_logger
#==============================================================================
# Constants
#==============================================================================

#==============================================================================
#
#==============================================================================
def read_table_from_xls(file_name,sheet_name,header_marker='HEADER_MARKER',
                        logger=None):
    """
    Read a table from a xls spreadsheet

    Open a spreadsheet called =filename=

    Look for a worksheet named =sheet_name= and then on this sheet
    look for a cell with =header_marker= in it.
    The table starts on the row just below it (with the headers row)
    """


    def conv_cell(cell):
        t=cell.ctype
        if t==xlrd.XL_CELL_EMPTY:
            return None
        elif t==xlrd.XL_CELL_TEXT:
            return str(cell.value)
        elif t==xlrd.XL_CELL_NUMBER:
            return float(cell.value)
        elif t==xlrd.XL_CELL_DATE:
            tu=xlrd.xldate_as_tuple(cell.value,workbook.datemode)
            if 0<=cell.value<1:
                return datetime.time(*tu[3:])
            else:
                return datetime.datetime(*tu)
        elif t==xlrd.XL_CELL_BOOLEAN:
            return cell.value==1
        elif t==xlrd.XL_CELL_ERROR:
            return None
        elif t==xlrd.XL_CELL_BLANK:
            return None
        else:
            raise

    def det_data_loc():
        for row in range(sheet.nrows):
            cv=conv_cell(sheet.cell(row,0))
            if cv==header_marker:
                return row+1
        return None

    def det_last_col(row):
        for col in range(sheet.ncols):
            if sheet.cell(row,col).ctype in (xlrd.XL_CELL_EMPTY,
                                             xlrd.XL_CELL_BLANK):
                return col
        return sheet.ncols

    logger=default_logger(logger)
    try:
        workbook=xlrd.open_workbook(file_name)
    except FileNotFoundError:
        logger.error('File not found %s' % file_name)
        return None

    sheet=workbook.sheet_by_name(sheet_name)
    row0=det_data_loc()
    if row0 is None: return None
    col0=det_last_col(row0)
    headers=sheet.row_values(row0,end_colx=col0)
    return [dict(zip(headers,
                     map(conv_cell,
                         sheet.row_slice(r,end_colx=col0)))) \
            for r in range(row0+1,sheet.nrows)]


#==============================================================================
# 
#==============================================================================
def write_table_to_workbook(workbook,data,sheet_name,headers,headers_row,
                            row_func=None,global_func=None,freeze_column=0):

    def write_sheet(r,c,v,numfmt=None):
        if v is None:
            sheet.write_blank(r,c,None)
        elif type(v) in (int,float,np.float64):
            if np.isnan(v):
                sheet.write_blank(r,c,None)
            elif numfmt:
                sheet.write_number(r,c,v,cell_format=numfmts[numfmt])
            elif (v==int(v)) or (np.abs(v)>100000):
                sheet.write_number(r,c,v,cell_format=st_int)
            else:
                sheet.write_number(r,c,v,cell_format=st_float)
        elif type(v) in (datetime.datetime,datetime.date):
            #remove timezone info (not supported in xls)
            if type(v) is datetime.datetime: v=v.replace(tzinfo=None)
            fmt=numfmts[numfmt] if numfmt in numfmts else None
            sheet.write_datetime(r,c,v,fmt)
        else:
            sheet.write_string(r,c,str(v))

    sheet=workbook.add_worksheet(sheet_name)

    st_float=workbook.add_format({'num_format':'#,##0.00;[RED]-#,##0.00'})
    st_float1=workbook.add_format({'num_format':'#,##0.0;[RED]-#,##0.0'})
    st_int=workbook.add_format({'num_format':'#,##0;[RED]-#,##0'})
    st_perc0=workbook.add_format({'num_format':'0%;[RED]-0%'})
    st_perc1=workbook.add_format({'num_format':'0.0%;[RED]-0.0%'})
    st_usd0=workbook.add_format({'num_format':
                                     '[$$-409]#,##0;[RED]-[$$-409]#,##0'})
    st_usd1=workbook.add_format({'num_format':
                                     '[$$-409]#,##0.0;[RED]-[$$-409]#,##0.0'})
    st_date=workbook.add_format({'num_format':'yyyy-mm-dd'})
    numfmts={
        'float' :st_float,
        'float1':st_float1,
        'int'   :st_int,
        'perc0' :st_perc0,
        'perc1' :st_perc1,
        'usd0'  :st_usd0,
        'usd1'  :st_usd1,
        'date'  :st_date,
    }

    st_header=workbook.add_format({
        'bold'          :1,
        #'font_size'     :8,
        #'font_color'    :'#F5F5F5',
        #'bg_color'      :'#000000',
        # 'text_wrap'     :True,
    })

    sheet.freeze_panes(headers_row+1,freeze_column)
    for j,h in enumerate(headers):
        if type(h) in (tuple,list):
            v=h[0]
            try:
                w=h[2]
            except IndexError:
                pass
            else:
                sheet.set_column(j,j,w)
        else:
            v=h
        sheet.write_string(headers_row,j,v.capitalize(),cell_format=st_header)

    for row,rec in enumerate(data):
        for col,h in enumerate(headers):
            if type(h) in (tuple,list):
                k=h[0]; numfmt=h[1]
            else:
                k=h; numfmt=None
            if k in rec:
                v=rec[k]
            else:
                v=None
            if v: write_sheet(row+headers_row+1,col,v,numfmt=numfmt)
            if row_func:
                row_func(sheet=sheet,row=row+headers_row+1,col=col,
                         key=k,rec=rec,wrfunc=write_sheet)

    if global_func:
        global_func(sheet,write_sheet)

    return workbook


def write_table_to_xls(file_name,data,sheet_name,headers,headers_row,
                            row_func=None,global_func=None,freeze_column=0):

    try:
        workbook=xlsxwriter.Workbook(file_name)
    except:
        return None

    workbook=write_table_to_workbook(workbook,data,sheet_name,headers,
                                     headers_row,row_func,global_func,
                                     freeze_column)
    if workbook:
        workbook.close()
        return file_name
    else:
        return None
