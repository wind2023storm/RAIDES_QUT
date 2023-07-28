import os

from fpdf import FPDF
from datetime import date
import itertools
from pathlib import Path
from django.http import HttpResponse, FileResponse
from . import plotter
from django.urls import reverse
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(BASE_DIR)


class PDF(FPDF):
    """
    Subclass of FPDF to define some of the standard sections of the reports.
    """

    def __init__(self, title: str='', title_font: str='Times',
            left_margin: float=10, right_margin: float=10,
            top_margin: float=10):
        """Sets some important metavariables.
        
        Args:
            title: The title to set for the report in the header.
            title_font: The font family for the title.
            left_margin: The margin from the left in mm.
            right_margin: The margin from the top in mm.
            top_margin: The margin from the top in mm.
        """

        super().__init__()

        # Set args as class attributes for the other functions of this class
        self.title = title
        self.title_font = title_font

        # Set margins for this pdf
        self.set_margins(left=left_margin, top=top_margin, 
                right=right_margin)

    def header(self, ln_break: int=20):
        """Defines the header for the pdf."""

        # dont add header on title page
        if self.page_no() == 1:
            return

        # Logo in top left corner
        self.image(str(BASE_DIR) + '/geochem/resources/images/orefoxlogo.png', y=15, w=45)

        # Display title
        self.set_font(self.title_font, 'B', size=20)
        self.cell(0, 10, self.title, align='R')

        # Set a line break after the header
        self.ln(ln_break)

    def footer(self):
        """Defines the footer for the pdf."""

        # dont add footer on title page
        if self.page_no() == 1:
            return

        # 15mm from bottom
        self.set_y(-15)

        self.set_font(self.title_font, 'I')

        # Display a page count
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')


class ReportMaker:
    """Handles process of generating reports."""

    def __init__(self, temp_filepath: str='test/reports/temporary/',
            image_width: float=160, make_temp_dir: bool=True):

        if make_temp_dir:
            try:
                os.makedirs(temp_filepath)
            except FileExistsError:
                # If directory already exists, don't do anything
                pass

        self.temp_filepath = temp_filepath
        self.image_width = image_width

    def make_title(self, pdf, title: str, fontsize=14):
        """Function to make a title for a page."""
        pdf.set_font(pdf.title_font, 'B', size=fontsize)
        pdf.cell(0, 10, title, align='L')
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)

    def get_x_value_image_centre(self, image_width: float):
        """Finds centre for an image. Useful for centering images.
        
        Takes an image's width and finds the horizontal coordinate for the
        top left by taking the middle of the document and taking half of the
        width from that number.
        Args:
            image_width: The width of the image in inches (matplotlib default).
        """

        # A4 pages are 210mm wide, with 10mm margins on either side
        midpoint = 95 # 190/2

        # Convert image width to mm and divide by two
        distance_from_midpoint = image_width/2

        return 10 + midpoint - distance_from_midpoint

    def make_table(self, pdf, data):
        """makes a table containing all the data selected for a cleaning option
        Parameters:
        --------------
                pdf: FPDF
                        pdf being built
                data: List[str]
                        contains data that will populate the table being built
        """
        all = []
        for column in data:
                all.append(column)

        args = [iter(all)] * 6
        grouped = itertools.zip_longest(*args, fillvalue='')

        for index, column in enumerate(grouped):
                # Save top coordinate
                top = pdf.y
                pdf.x = pdf.x + 7

                fill = True if index%2 == 0 else False

                for element in column:
                        if element == '':
                                continue
                        # Calculate x position of next cell
                        offset = pdf.x + 29

                        pdf.cell(30, 10, element, fill=fill)

                        # Reset y coordinate
                        pdf.y = top

                        # Move to computed offset
                        pdf.x = offset
                pdf.ln(12)

    def title_page(self, pdf, title: str, project: str):
        """Displays a title page for the given report.
        Args:
            pdf: The pdf to display in.
            title: The title of the report.
        """
        pdf.add_page()
        
        pdf.image(str(BASE_DIR) + '/geochem/resources/images/defaultimage.jpg', x=0 , y=0, w=210, h=297)

        # add white triangle to block out half of image
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(1)
        y1 = 265
        x2 = 210
        while y1 > 0 and x2 > 0:
                # Make the first few lines black
                if y1 == 264:
                        pdf.set_draw_color(255, 255, 255)

                pdf.line(x1=0, y1=y1, x2=x2, y2=0)
                y1 -= 1
                x2 -= 1

        # Logo in top left corner
        pdf.image(str(BASE_DIR) + '/geochem/resources/images/orefoxlogo.png', y=12, w=45)

        # adding orange card - MUST DEAL WITH TRANSPARENCY
        # with pdf.local_context(fill_opacity=0.15, stroke_opacity=0.15):
        pdf.set_draw_color(238, 154, 73)
        pdf.set_fill_color(238, 154, 73)
        pdf.rect(x=0, y=60, w=190, h=90, style="F")

        pdf.set_line_width(0.5)

        x1 = 190
        y1 = 60.5
        x2 = 190
        y2 = 105
        x3 = x1
        y3 = 149.5
        pdf.line(x1=x1, y1=y1, x2=x3, y2=y3)
        while y1 <= y3 and x2 > x1:
                pdf.line(x1=x1, y1=y1, x2=x2, y2=y2)
                pdf.line(x1=x3, y1=y3, x2=x2, y2=y2)
                y1 += 0.5
                x2 -= 0.5
                y3 -= 0.5

        pdf.ln(59)

        # adding title

        pdf.set_font(pdf.title_font, style='', size=45)  # style = 'B' originally
        pdf.set_x(25)
        pdf.multi_cell(120, h=10, txt=title, align='C')
        pdf.ln(11)

        # text underneath title
        pdf.set_font('Merriweather', '', 18)

        # date preparation text
        pdf.set_x(20)
        pdf.cell(30, h=9, txt="Date prepared: ")
        pdf.ln(11)
        pdf.set_x(30)
        pdf.cell(30, h=9, txt=str(date.today()))

        pdf.ln(11)

        # project text
        pdf.set_x(20)
        pdf.cell(30, h=9, txt="Project: ")
        pdf.ln(11)
        pdf.set_x(30)

        pdf.set_draw_color(0, 0, 73)
        #pdf.cell(90, h=9, txt=project, border=1)
        # use multi_cell
        pdf.multi_cell(115, h=9, txt=project, align='L')
    
    def executed_methods_subtitle(self, pdf):
        """adds 'summary of executed methods' subtitle to current place in pdf
        Parameters:
        ----------------
                pdf: FPDF
                        pdf being built
        """
        pdf.add_page()

        pdf.ln(6)

        pdf.set_font(pdf.title_font, 'B', size=20)
        pdf.set_text_color(0, 112, 192)
        pdf.cell(30, txt="Summary of Executed Methods:")

    def cleaning_table_of_contents(self, pdf, options):
        """builds and adds table of contents to cleaning report pdf
        Parameters:
        --------------
                pdf: FPDF
                        pdf being built
                log: List[str]
                        contains information related to cleaning options selected by user
        """
        self.executed_methods_subtitle(pdf)

        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)
        page = 4

        # If columns have been removed
        if 'removeColumns' in options:
                pdf.set_x(15)
                link = pdf.add_link()
                pdf.set_link(link=link, page=page)
                pdf.cell(30, txt="\u2022 Remove Columns..............................................................................................................................." )
                pdf.ln(10)
                page += 1
        
        # If handling the inequality cells
        if 'handleInequalities' in options:
                pdf.set_x(15)
                link_2 = pdf.add_link()
                pdf.set_link(link=link_2, page=page)
                pdf.cell(30, txt="\u2022 Handle inequalities..........................................................................................................................." )
                pdf.ln(10)
                page += 1
       
        # Removal of duplicate units
        if 'removeDuplicates' in options:
                pdf.set_x(15)
                link_4 = pdf.add_link()
                pdf.set_link(link=link_4, page=page)
                pdf.cell(30, txt="\u2022 Remove Duplicates............................................................................................................................")
                pdf.ln(10)
                page += 1

        if 'removeNonNumeric' in options:
                pdf.set_x(15)
                link_6 = pdf.add_link()
                pdf.set_link(link=link_6, page=page)
                pdf.cell(30, txt="\u2022 Removed non-numeric entries......................................................................................................" )
                pdf.ln(10)
                page += 1

        if 'removeComma' in options:
                pdf.set_x(15)
                link_7 = pdf.add_link()
                pdf.set_link(link=link_7, page=page)
                pdf.cell(30, txt="\u2022 Removed comma seperation from numbers..............................................................................." )
                pdf.ln(10)
                page += 1
        # If imputing values was done
        if 'imputeEmpty' in options:
                pdf.set_x(15)
                link_1 = pdf.add_link()
                pdf.set_link(link=link_1, page=page)
                pdf.cell(30, txt="\u2022 Columns imputed.............................................................................................................................." )
                pdf.ln(10)
                page += 1    
         # If converting units
        if 'convertUnits' in options:
                pdf.set_x(15)
                link_3 = pdf.add_link()
                pdf.set_link(link=link_3, page=page)
                pdf.cell(30, txt="\u2022 Convert uniform units......................................................................................................................")
                pdf.ln(10)
                page += 1            

    def cleaning_summary_table_header_row(self, pdf, column_headers):
        """adds header row of table to current place in the pdf
        
        Parameters:
        --------------
                pdf: FPDF
                        pdf being built
                column_headers: List[str]
                        list of possible cleaning operations that can be performed on a dataset
        """
        top = pdf.y
        pdf.x = pdf.x + 7
        curX = pdf.x  
        pdf.set_fill_color(r=255, g=136, b=59)
        for element in column_headers:
                pdf.y = top
                pdf.x = curX
                if element == 'Units':
                        pdf.multi_cell(15, 10, element, fill=True, align='C')
                        curX += 15
                elif element == 'Remove':
                        pdf.multi_cell(22, 10, element, fill=True, align='C')
                        curX += 22
                elif element == 'Inequalities':
                        pdf.multi_cell(20, 10, "Inequal.", fill=True, align='C')
                        curX += 20
                elif element == 'Non-numeric':
                        pdf.multi_cell(32, 10, element, fill=True, align='C')
                        curX += 32
                elif element == 'Comma Sep':
                        pdf.multi_cell(30, 10, element, fill=True, align='C')
                        curX += 30
                else:
                        pdf.multi_cell(25, 10, element, fill=True, align='C')
                        curX += 25

    def cleaning_summary_table_body_row(self, pdf, index, column, column_manipulations, column_manipulation_types):
        """adds a body row of table in pdf
        
        Parameters:
        --------------
                pdf: FPDF
                        pdf being built
                index: int
                        index of the row being added to the table
                column: List[List[str]]
                        observation in dataset that is being created in the table
                column_manipulations: List[List[str]]
                        contains all the observations separated by group based on cleaning operations
                column_manipulation_types: List[str]
                        list of possible cleaning operations to be performed on a column (in the format used in logs)
        """
        top = pdf.y
        pdf.x = pdf.x + 7
        curX = pdf.x

        is_index_even = index % 2 == 0

        pdf.set_font('Merriweather', '', 8)
        pdf.set_fill_color(r=251, g=228, b=213)

        pdf.multi_cell(25, 5, column, fill=is_index_even)
        pdf.y = top
        curX += 25

        pdf.set_font('ZapfDingbats', '', 12)

        # if column should be removed
        pdf.x = curX
        if column in column_manipulations[column_manipulation_types.index('REMOVE_COLUMNS:')]:
                pdf.cell(22, 5, '3', fill=is_index_even, align='C')
                # pdf.multi_cell(22, 5, '3', fill=is_index_even, align='C')
                # if column is removed then no other operations should be performed on it
        else:
                pdf.cell(22, 5, '', fill=is_index_even)
                #pdf.multi_cell(22, 5, '', fill=is_index_even)
        pdf.y = top
        curX += 22

        # imputing columns selected
        pdf.x = curX
        if column in column_manipulations[column_manipulation_types.index('IMPUTE_VALUES:')]:
                pdf.cell(25, 5, '3', fill=is_index_even, align='C')
        else:
                pdf.cell(25, 5, '', fill=is_index_even)
        pdf.y = top
        curX += 25

        # If handling the inequality cells
        pdf.x = curX
        if column in column_manipulations[column_manipulation_types.index('HANDLE_INEQUALITIES:')]:
                pdf.cell(20, 5, '3', fill=is_index_even, align='C')
        else:
                pdf.cell(20, 5, '', fill=is_index_even)
        curX += 20
        pdf.y = top

        # If converting units
        pdf.x = curX
        if column in column_manipulations[column_manipulation_types.index('UNITS:')]:
                pdf.cell(15, 5, '3', fill=is_index_even, align='C')
        else:
                pdf.cell(15, 5, '', fill=is_index_even)
        curX += 15
        pdf.y = top
        
        # if removing non-numeric units
        pdf.x = curX
        if column in column_manipulations[column_manipulation_types.index('REMOVE_NON_NUMERIC:')]:
                pdf.cell(32, 5, '3', fill=is_index_even, align='C')
        else:
                pdf.cell(32, 5, '', fill=is_index_even)
        curX += 32
        pdf.y = top
        
        # removing comma separations - RECONSIDER
        pdf.x = curX
        if column in column_manipulations[column_manipulation_types.index('REMOVED_COMMA_SEP:')]:
                pdf.cell(30, 5, '3', fill=is_index_even, align='C')
        else:
                pdf.cell(30, 5, '', fill=is_index_even)
        curX += 30
        pdf.y = top

        pdf.set_font('Merriweather', '', 12)

        # Reset y coordinate
        pdf.y = top + 5
        pdf.ln(1)
    def add_link(self, pdf, x, y, w, h, link):
        pdf.set_xy(x,y)
        pdf.cell(w, h, '', link=link)    
    def cleaning_summary_table(self, pdf, datacleaner, datacleaning_result,csv_file_url):
        pdf.add_page()

        pdf.set_font(pdf.title_font, 'B', size=15) 
        pdf.set_text_color(0, 112, 192)
        pdf.cell(30, txt="Summary of Executed Methods:") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)
        remove_columns = []
        impute_columns = []
        inequalities_columns = []
        units_columns = []
        non_numeric_columns = []
        comma_sep_columns = []
        column_headers = ['Column', 'Removed', 'Imputed', 'Inequalities', 'Units', 'Non-numeric', 'Comma Sep']

        for result in datacleaning_result:
            result_split = result.split("detail:")
            change_dict = eval(result_split[1])
            line = result_split[0]

           
            # If columns have been removed
            if 'REMOVE_COLUMNS:' in line:
                string = line.split('REMOVE_COLUMNS:')[-1]
                remove_columns = string.split(',')
            # If imputing values was done
            elif 'IMPUTE_VALUES' in line:
                string = line.split('IMPUTE_VALUES:')[-1]
                for columns, (rows,values,percentage) in change_dict.items():
                        impute_columns.append(columns)

           # If handling the inequality cells
            elif 'HANDLE_INEQUALITIES' in line:
                string = line.split('HANDLE_INEQUALITIES:')[-1]
                for columns, (rows,values,percentage) in change_dict.items():
                        inequalities_columns.append(columns)        
                #inequalities_columns = string.split(',')
            # If converting units
            elif 'UNITS' in line:
                string = line.split('UNITS:')[-1]
                for columns, (rows,values,percentage) in change_dict.items():
                        units_columns.append(columns)
            elif 'REMOVE_NON_NUMERIC' in line:
                string = line.split('REMOVE_NON_NUMERIC:')[-1]
                for columns,(rows,values,percentage) in change_dict.items():
                        non_numeric_columns.append(columns)
            elif 'REMOVED_COMMA_SEP' in line:
                string = line.split('REMOVED_COMMA_SEP:')[-1]
                for columns,(rows,values,percentage) in change_dict.items():
                        comma_sep_columns.append(columns)
          
        top = pdf.y
        pdf.x = pdf.x + 7
        curX = pdf.x  
        pdf.set_fill_color(r=255, g=136, b=59)
        for element in column_headers:
                pdf.y = top
                pdf.x = curX
                if element == 'Units':
                        pdf.multi_cell(15, 10, element, fill=True)
                        curX += 15
                elif element == 'Removed':
                        pdf.multi_cell(22, 10, element, fill=True)
                        curX += 22
                elif element == 'Inequalities':
                        pdf.multi_cell(30, 10, element, fill=True)
                        curX += 30
                elif element == 'Non-numeric':
                        pdf.multi_cell(32, 10, element, fill=True)
                        curX += 32
                elif element == 'Comma Sep':
                        pdf.multi_cell(30, 10, element, fill=True)
                        curX += 30
                else:
                        pdf.multi_cell(25, 10, element, fill=True)
                        curX += 25
        pdf.set_fill_color(r=251, g=228, b=213)
        first_loop = True
        for index, column in enumerate(datacleaner.columns):
                if pdf.y >= 270:
                        pdf.add_page()
                        top = pdf.y
                        pdf.x = 17
                        curX = pdf.x 
                        first_loop = True 
                        pdf.set_fill_color(r=255, g=136, b=59)
                        for element in column_headers:
                                pdf.y = top
                                pdf.x = curX
                                if element == 'Units':
                                        pdf.multi_cell(15, 10, element, fill=True)
                                        curX += 15
                                elif element == 'Removed':
                                        pdf.multi_cell(22, 10, element, fill=True)
                                        curX += 22
                                elif element == 'Inequalities':
                                        pdf.multi_cell(30, 10, element, fill=True)
                                        curX += 30
                                elif element == 'Non-numeric':
                                        pdf.multi_cell(32, 10, element, fill=True)
                                        curX += 32
                                elif element == 'Comma Sep':
                                        pdf.multi_cell(30, 10, element, fill=True)
                                        curX += 30
                                else:
                                        pdf.multi_cell(25, 10, element, fill=True)
                                        curX += 25
                        pdf.set_fill_color(r=251, g=228, b=213)
                # Save top coordinate
                top = pdf.y
                if first_loop:
                      pdf.x = 17
                      first_loop=False
                else:      
                      pdf.x = pdf.x + 7
                      
                curX = pdf.x
                #pdf.ln()
                pdf.multi_cell(25, 6, column[:7], fill=True if index%2 == 0 else False)
                pdf.y = top
                curX += 25

                pdf.set_font('ZapfDingbats', '', 12)

                pdf.x = curX
                if column in remove_columns:
                        pdf.multi_cell(22, 6, '3', fill=True if index%2 == 0 else False, align='C')
                else:
                        pdf.multi_cell(22, 6, '', fill=True if index%2 == 0 else False)
                pdf.y = top
                curX += 22

                # If imputing values was done
                pdf.x = curX
                if column in impute_columns:
                        pdf.multi_cell(25, 6, '3', fill=True if index%2 == 0 else False, align='C')
                else:
                        pdf.multi_cell(25, 6, '', fill=True if index%2 == 0 else False)
                pdf.y = top
                curX += 25

                # If handling the inequality cells
                pdf.x = curX
                if column in inequalities_columns:
                        pdf.multi_cell(30, 6, '3', fill=True if index%2 == 0 else False, align='C')
                else:
                        pdf.multi_cell(30, 6, '', fill=True if index%2 == 0 else False)
                curX += 30
                pdf.y = top

                # If converting units
                pdf.x = curX
                if column in units_columns:
                        pdf.multi_cell(15, 6, '3', fill=True if index%2 == 0 else False, align='C')
                else:
                        pdf.multi_cell(15, 6, '', fill=True if index%2 == 0 else False)
                curX += 16
                pdf.y = top
                
                pdf.x = curX
                if column in non_numeric_columns:
                        pdf.multi_cell(32, 6, '3', fill=True if index%2 == 0 else False, align='C')
                else:
                        pdf.multi_cell(32, 6, '', fill=True if index%2 == 0 else False)
                curX += 32
                pdf.y = top
                
                pdf.x = curX
                if column in comma_sep_columns:
                        pdf.multi_cell(30, 6, '3', fill=True if index%2 == 0 else False, align='C')
                else:
                        pdf.multi_cell(30, 6, '', fill=True if index%2 == 0 else False)
                curX += 30
                pdf.y = top

                pdf.set_font('Merriweather', '', 12)

                # Reset y coordinate
                pdf.y = top + 7
                pdf.ln(2)

    def analysis_table_of_contents(self, pdf, analyser):
        """builds and adds table of contents to analyser report pdf
        Parameters:
        --------------
                pdf: FPDF
                        pdf being built
                analyser: Analyser
                        contains information related to analysis functions selected by user
        """
        self.executed_methods_subtitle(pdf)

        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)
        page = 3
            # If columns have been removed
        if analyser.stats is not None:
                pdf.set_x(15)
                link = pdf.add_link()
                pdf.set_link(link=link, page=page)
                pdf.cell(30, txt="\u2022 Analyser Statistics........................................................................................................................." + str(page), link=link)
                pdf.ln(10)
                page += 1
        if analyser.summaries is not None:
                pdf.set_x(15)
                link = pdf.add_link()
                pdf.set_link(link=link, page=page)
                pdf.cell(30, txt="\u2022 Summarize Float Columns........................................................................................................." + str(page), link=link)
                pdf.ln(10)
                page += 5         
            # If imputing values was done
        if analyser.kmeans is not None:
                pdf.set_x(15)
                link_1 = pdf.add_link()
                pdf.set_link(link=link_1, page=page)
                pdf.cell(30, txt="\u2022 K-means Clustering....................................................................................................................." + str(page), link=link_1)
                pdf.ln(10)
                page += 2
            # If handling the inequality cells
        if analyser.rf is not None:
                pdf.set_x(15)
                link_2 = pdf.add_link()
                pdf.set_link(link=link_2, page=page)
                pdf.cell(30, txt="\u2022 Random Forest Regression........................................................................................................." + str(page), link=link_2)
                pdf.ln(10)
                page += 5
            # If converting units
        if analyser.adaboost is not None:
                pdf.set_x(15)
                link_3 = pdf.add_link()
                pdf.set_link(link=link_3, page=page)
                pdf.cell(30, txt="\u2022 AdaBoost........................................................................................................................................." + str(page), link=link_3)
                pdf.ln(10)
                page += 5
            # Removal of duplicate units
        if analyser.xgboost is not None:
                pdf.set_x(15)
                link_4 = pdf.add_link()
                pdf.set_link(link=link_4, page=page)
                pdf.cell(30, txt="\u2022 XGBoost.........................................................................................................................................." +str(page), link=link_4)
                pdf.ln(10)
                page += 5
            # Removing entries

        if analyser.rf is not None and analyser.adaboost is not None and \
                analyser.xgboost is not None:
                pdf.set_x(15)
                link_5 = pdf.add_link()
                pdf.set_link(link=link_5, page=page)
                pdf.cell(30, txt="\u2022 RF ADA XG Comparison..............................................................................................................." + str(page), link=link_5)
                pdf.ln(10)
                page += 1

        if analyser.pca is not None:
                pdf.set_x(15)
                link_6 = pdf.add_link()
                pdf.set_link(link=link_6, page=page)
                pdf.cell(30, txt="\u2022 Principal Component Analysis.................................................................................................." + str(page), link=link_6)
                pdf.ln(10)
                page += 5

        if analyser.hca is not None:
                pdf.set_x(15)
                link_7 = pdf.add_link()
                pdf.set_link(link=link_7, page=page)
                pdf.cell(30, txt="\u2022 Hierarchical Clustering Analysis.............................................................................................." + str(page), link=link_7)
                pdf.ln(10)
                page += 4

        if analyser.nn is not None:
                pdf.set_x(15)
                link_8 = pdf.add_link()
                pdf.set_link(link=link_8, page=page)
                pdf.cell(30, txt="\u2022 Dense Neural Network..............................................................................................................." + str(page), link=link_8)
                pdf.ln(10)
                page += 5
        if analyser.correlations is not None:
                pdf.set_x(15)
                link_9 = pdf.add_link()
                pdf.set_link(link=link_9, page=page)
                pdf.cell(30, txt="\u2022 Correlation Coefficients............................................................................................................." + str(page), link=link_9)
                pdf.ln(10)
                page += 1

    def display_info(self, pdf, info_filepath: str):
        """Displays an info txt in the pdf."""
        with open(info_filepath, 'r') as f:
            log = f.readlines()

        for line in log:
            if line[0] == '*':
                # Set font to bold and display
                pdf.set_font(pdf.title_font, 'B', size=14)
                pdf.cell(0, 10, line[1:], align='L')
                pdf.ln(10)

                # Revert font
                pdf.set_font('Merriweather', '', 12)

            else:
                pdf.multi_cell(190, h=5, txt=line)
                pdf.ln(2)

    def display_analyser_stats(self, pdf, analyser):
        """Helper function to display analyser.stats in report.
        
        Args:
            pdf: The pdf to display the stats in.
            analyser: The analyser to get the stats from.
        """
        pdf.add_page()

        pdf.set_font('Merriweather', '', size=14)
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        pdf.cell(30, txt="Summary of Analyser Stats:") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        # Feature count
        feature_string = 'The number of features: {}'.format(
            analyser.stats['num_features'])
        pdf.cell(0, h=10, txt=feature_string, ln=1)
        pdf.ln(5)

        # Row count
        row_string = 'The number of rows: {}'.format(
            analyser.stats['num_entries']
        )
        pdf.cell(0, h=10, txt=row_string, ln=1)
        pdf.ln(5)

        # Empty cells
        empty_string = 'The number of empty cells: {}'.format(
            analyser.stats['num_empty']
        )
        pdf.cell(0, h=10, txt=empty_string, ln=1)
        pdf.ln(5)

        # Size of data
        size_string = 'The size of the data: {} bytes'.format(
            analyser.stats['data_size']
        )
        pdf.cell(0, h=10, txt=size_string, ln=1)
        pdf.ln(5)

    def display_analyser_summaries(self, pdf, analyser):
        """Helper function to display analyser.summaries in report.
        
        Args:
            pdf: The pdf to display the stats in.
            analyser: The analyser to get the stats from.
        """

        pdf.add_page()
        self.make_title(pdf, 'Statistics of Data- Summarize Float Columns')
        plot = plotter.Plotter(analyser)

        # Make figures
        plot.plot_means(f'{self.temp_filepath}mean.png', figsize=(18,13),
                rotation=90)
        plot.plot_medians(f'{self.temp_filepath}medians.png', figsize=(18,13),
                rotation=90)
        plot.plot_std(f'{self.temp_filepath}std.png', figsize=(18,13),
                rotation=90)
        plot.plot_range(f'{self.temp_filepath}range.png', figsize=(18,13),
                rotation=90)
        plot.plot_violin(f'{self.temp_filepath}violin.png', figsize=(15,21))
        plot.plot_box_whisker(f'{self.temp_filepath}box_whisker.png', figsize=(15,21))
        
        # Display figures now
        pdf.image(f'{self.temp_filepath}mean.png', 
                x=self.get_x_value_image_centre(self.image_width),
                w=self.image_width)

        pdf.image(f'{self.temp_filepath}medians.png', 
                x=self.get_x_value_image_centre(self.image_width),
                w=self.image_width)

        pdf.add_page()

        pdf.image(f'{self.temp_filepath}std.png', 
                x=self.get_x_value_image_centre(self.image_width),
                w=self.image_width)

        pdf.image(f'{self.temp_filepath}range.png', 
                x=self.get_x_value_image_centre(self.image_width),
                w=self.image_width)
        
        pdf.image(f'{self.temp_filepath}box_whisker.png',
                x=self.get_x_value_image_centre(self.image_width) -5,
                w=self.image_width)
        
        pdf.image(f'{self.temp_filepath}violin.png',
                x=self.get_x_value_image_centre(self.image_width) -5,
                w=self.image_width)

    def display_k_means(self, pdf, plotter, 
            display_hyperparams: bool=True, display_text: bool=True):
        """Displays k-means results in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create the figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
            display_hyperparams: Whether or not to display hyper parameters.
            display_text: Whether or not to display text explanations.
        """
        pdf.add_page()

        pdf.set_font(pdf.title_font, 'B', size=15) 
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        pdf.cell(30, txt="K-means Clustering") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        kmeans_filename = self.temp_filepath + 'kmeans.png'

        plotter.plot_silhouette(kmeans_filename)

        pdf.image(kmeans_filename, 
                x=self.get_x_value_image_centre(self.image_width*1.3),
                w=self.image_width*1.3)

        if display_hyperparams:
                pdf.add_page()

                # Make a title for this page
                pdf.set_font('Merriweather', '', size=14)
                pdf.cell(0, 10, 'K-means Hyperparameters', align='L')
                pdf.ln(10)
                pdf.set_font('Merriweather', '', 12)

                # Get the hyperparams
                hp = plotter.analyser.kmeans.get_params()

                # Algorithm                    
                pdf.multi_cell(190, 5, 'Algorithm used: {}'.format(
                        hp['algorithm']))
                pdf.ln(5)

                # Init                 
                pdf.multi_cell(100, 5, 'Initialisation method: {}'.format(
                        hp['init']))
                pdf.ln(5)

                # Max iterations
                pdf.multi_cell(100, 5, 'Maximum iterations used: {}'.format(
                        hp['max_iter']))
                pdf.ln(5)

                # N clusters
                pdf.multi_cell(100, 5, 'Number of clusters: {}'.format(
                        hp['n_clusters']))
                pdf.ln(5)

                # Random Seed
                pdf.multi_cell(100, 5, 'The random generator seed used: {}'.format(
                        hp['random_state']
                ))
                pdf.ln(5)

                # N init
                pdf.multi_cell(100, 5, 'Number of beginning seeds: {}'.format(
                        hp['n_init']))
                pdf.ln(5)

        # TEXT
        if display_text:
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/kmeans.txt')
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/kmeans_hyperparams.txt')

    def display_random_forest(self, pdf, plotter, 
            display_hyperparams: bool=True, display_text: bool=True):
        """Displays random forest results in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create the figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
            display_hyperparams: Whether or not to display hyper parameters.
            display_text: Whether or not to display text explanations.
        """

        # FIGURES
        pdf.add_page()

        pdf.set_font('Merriweather', '', size=14)
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        pdf.cell(30, txt="Random Forest Regression") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)
        
        rf_filename = self.temp_filepath + 'rf.png'

        plotter.plot_rf_importances(rf_filename, big_to_small=False, 
                figsize=(16,18))

        pdf.image(rf_filename, 
                x=8,y=45,
                w=170)
        pdf.add_page()

        # add graph of the biggest 10 data from the RF graph

        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        rf_big_filename = self.temp_filepath + 'rf_big.png'

        if plotter.plot_rf_importances_big_10(rf_big_filename, big_to_small=False,
                                    figsize=(14, 8)):

                pdf.image(rf_big_filename,
                        x=10,
                        w=190)


        # add graph of the smallest 10 data from the RF graph

        pdf.ln(5)

        rf_small_filename = self.temp_filepath + 'rf_small.png'

        if plotter.plot_rf_importances_small_10(rf_small_filename, big_to_small=False,
                                    figsize=(14, 8)):

                pdf.image(rf_small_filename,
                        x=10,
                        w=190)



        plotter.plot_model_predictions(
                plotter.analyser.rf_test_predictions, 
                plotter.analyser.rf_test_y, 
                self.temp_filepath + 'rf_performance.png',
                figsize=(12, 8)
            )

        pdf.image(self.temp_filepath + 'rf_performance.png',
                x=self.get_x_value_image_centre(self.image_width)*0.3,
                w=self.image_width*1.2)
        
        # HYPER PARAMETERS
        if display_hyperparams:
                pdf.add_page()

                # Make a title for this page
                pdf.set_font('Merriweather', '', size=14)
                pdf.cell(0, 10, 'Random Forest Hyperparameters', align='L')
                pdf.ln(10)
                pdf.set_font('Merriweather', '', 12)

                # Get the hyperparams
                hp = plotter.analyser.rf.get_params()

                # The number of estimators                    
                pdf.multi_cell(190, 5, 'Number of estimators: {}'.format(
                        hp['n_estimators']))
                pdf.ln(5)

                # The max number of features
                pdf.multi_cell(190, 5, 
                                'The maximum number of features to ' + \
                                'split a node is: {}'.format(hp['max_features']))
                pdf.ln(5)

                # Criterion
                pdf.multi_cell(190, 5, 'The criterion used to measure the ' + \
                        'quality of a split is: {}'.format(
                                hp['criterion']
                        ))
                pdf.ln(5)

                # Max depth
                pdf.multi_cell(190, 5, 'The maximum depth of each tree: {}'.format(
                        hp['max_depth']
                ))
                pdf.ln(5)

                # Bootstrap
                pdf.multi_cell(190, 5, 'Are bootstrap samples used: {}'.format(
                        hp['bootstrap']
                ))
                pdf.ln(5)

                # Min samples split
                pdf.multi_cell(190, 5, 'The minimum samples before split: {}'.format(
                        hp['min_samples_split']
                ))
                pdf.ln(5)

                # Min samples leaf
                pdf.multi_cell(190, 5, 'The minimum samples allowed in leaf: ' +\
                        '{}'.format(hp['min_samples_leaf']))
                pdf.ln(5)

                # Max num leaf nodes
                pdf.multi_cell(190, 5, 'The maximum leaf nodes: {}'.format(
                        hp['max_leaf_nodes']
                ))
                pdf.ln(5)

                # Max samples
                pdf.multi_cell(190, 5, 'The max number of samples: {}'.format(
                        hp['max_samples']
                ))
                pdf.ln(5)

                # Random Seed
                pdf.multi_cell(190, 5, 'The random generator seed used: {}'.format(
                        hp['random_state']
                ))
                pdf.ln(5)

                # CCP Alpha
                pdf.multi_cell(190, 5, 'CCP alpha: {}'.format(
                        hp['ccp_alpha']
                ))
                pdf.ln(5)

                # Min impurity decrease
                pdf.multi_cell(190, 5, 'The minimum impurity decrease: {}'.format(
                        hp['min_impurity_decrease']
                ))
                pdf.ln(5)

                # Min weight fraction leaf
                pdf.multi_cell(190, 5, 'The minimum weighted fraction of ' + \
                        'leaf nodes: {}'.format(hp['min_weight_fraction_leaf']))
                pdf.ln(5)

                # OOB Score
                pdf.multi_cell(190, 5, 'OOB Score: {}'.format(hp['oob_score']))
                pdf.ln(5)

        # TEXT
        if display_text:
            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/rf.txt')

            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/pca_hyperparams.txt')

    def display_pca(self, pdf, plotter, display_hyperparams: bool=True,
            display_text: bool=True):
        """Display PCA results in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
            display_hyperparams: Whether or not to display hyper parameters.
            display_text: Whether or not to display text explanations.
        """

        # FIGURES
        pdf.add_page()

        pdf.set_font('Merriweather', '', size=14)
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        pdf.cell(30, txt="Principal Component Analysis") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        pca_filenames = [self.temp_filepath + 'pca.png',
                self.temp_filepath + 'pca2.png']

        plotter.plot_pca_feature_bar(pca_filenames[0], figsize=(14,14))
        plotter.plot_pca_cumulative_importance(pca_filenames[1], 
                figsize=(14,11))

        pdf.image(pca_filenames[0],
                x=self.get_x_value_image_centre(self.image_width*1.1),
                w=self.image_width*1.1)
        pdf.add_page()
        pdf.image(pca_filenames[1],
                x=self.get_x_value_image_centre(self.image_width*1.3),
                w=self.image_width*1.3)

        # HYPER PARAMETERS
        if display_hyperparams:
                hp = plotter.analyser.pca.get_params()

                pdf.add_page()

                # Make a title for this page
                pdf.set_font(pdf.title_font, 'B', size=14)
                pdf.cell(0, 10, 'Principal Component Analysis Hyperparameters', 
                        align='L')
                pdf.ln(10)
                pdf.set_font('Merriweather', '', 12)
                
                # Number of features
                pdf.multi_cell(190, 5, 'The number of features: {}'.format(
                        hp['n_components']
                ))
                pdf.ln(5)

                # The random state
                pdf.multi_cell(190, 5, 'The random state: {}'.format(
                        hp['random_state']
                ))
                pdf.ln(5)

                # SVD Solver
                pdf.multi_cell(190, 5, 'The SVD solver: {}'.format(
                        hp['svd_solver']
                ))
                pdf.ln(5)

                # Tolerance
                pdf.multi_cell(190, 5, 'The tolerance for singular values: {}'.format(
                        hp['tol']
                ))
                pdf.ln(5)

                # Iterated power
                pdf.multi_cell(190, 5, 'Number of iterations for solving with ' + \
                        'randomised solver: {}'.format(hp['iterated_power']))
                pdf.ln(5)

                # Whiten
                pdf.multi_cell(190, 5, 'Whiten: {}'.format(hp['whiten']))
                pdf.ln(5)

        # TEXT
        if display_text:
            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/pca.txt')

            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/pca_hyperparams.txt')

    def display_hca(self, pdf, plotter, display_hyperparams: bool=True,
            display_text: bool=True): 
        """Display HCA results in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
            display_hyperparams: Whether or not to display hyper parameters.
            display_text: Whether or not to display text explanations.
        """
        
        # FIGURES

        pdf.add_page()

        pdf.set_font('Merriweather', '', size=14)
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        pdf.cell(30, txt="Hierarchical Clustering Analysis") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        hca_filename = self.temp_filepath + 'hca.png'

        plotter.plot_dendrogram(hca_filename, 
                labels=plotter.analyser.hca_subset_X,                
                figsize=(14,14), label_font_size=8, rotation=90)

        pdf.image(hca_filename, 
                x=self.get_x_value_image_centre(self.image_width*1.3),
                w=self.image_width*1.3)


        # HYPER PARAMETERS
        if display_hyperparams:
                hp = plotter.analyser.hca_hyperparams

                pdf.add_page()

                # Make a title for this page
                pdf.set_font(pdf.title_font, 'B', size=14)
                pdf.cell(0, 10, 'Hierarchical Clustering Analysis Hyperparameters', 
                        align='L')
                pdf.ln(10)
                pdf.set_font('Merriweather', '', 12)

                # Method
                pdf.multi_cell(190, 5, 
                        'Method used to link: {}'.format(hp['method']))
                pdf.ln(5)

                # Metric
                pdf.multi_cell(190, 5, 'Metric used: {}'.format(hp['metric']))

        # TEXT
        if display_text:
            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/hca.txt')

            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/hca_hyperparams.txt')

    def display_cc(self, pdf, plotter, display_text=True):
        """Display correlation coefficient results in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
            display_text: Whether or not to display text explanations.
        """
        # FIGURES
        pdf.add_page()

        pdf.set_font('Merriweather', '', size=14)
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        pdf.cell(30, txt="Correlation Coefficients") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)


        cc_filename = [self.temp_filepath + 'cc1.png',
                self.temp_filepath + 'cc2.png',
                self.temp_filepath + 'cc3.png']

        plotter.plot_correlations_heatmap(filenames=cc_filename,figsize=(14,16))

        cc_image_width = self.image_width - 10

        pdf.image(cc_filename[0], 
                x=10,y=45,
                w=190)
        pdf.add_page()

        pdf.image(cc_filename[1], 
                x=10,
                w=190)

        pdf.add_page()

        pdf.image(cc_filename[2], 
                x=10,
                w=190)

        # TEXT
        if display_text:
            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/cc.txt')

    def display_adaboost(self, pdf, plotter, display_hyperparams: bool=True,
            display_text: bool=True):
        """Display AdaBoost results in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
            display_hyperparams: Whether or not to display hyper parameters.
            display_text: Whether or not to display text explanations.
        """

        # FIGURES
        pdf.add_page()

        pdf.set_font('Merriweather', '', size=14)
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        pdf.cell(30, txt="AdaBoost") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        plotter.plot_adaboost_importances(self.temp_filepath + 'ada.png',
                big_to_small=False, figsize=(16,18))

        pdf.image(self.temp_filepath + 'ada.png', 
                x=10,
                w=190)

        # add graph of the biggest 10 data from the AdaBoost graph

        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        ada_big_filename = self.temp_filepath + 'ada_big.png'

        if plotter.plot_adaboost_importances_big_10(ada_big_filename, big_to_small=False,
                                    figsize=(14, 8)):

                pdf.image(ada_big_filename,
                        x=10,
                        w=190)


        # add graph of the smallest 10 data from the AdaBoost graph


        ada_small_filename = self.temp_filepath + 'ada_small.png'

        if plotter.plot_adaboost_importances_small_10(ada_small_filename, big_to_small=False,
                                    figsize=(14, 8)):

                pdf.image(ada_small_filename,
                        x=10,
                        w=190)


        plotter.plot_model_predictions(
                plotter.analyser.ada_test_predictions, 
                plotter.analyser.ada_test_y, 
                self.temp_filepath + 'ada_performance.png',
                figsize=(14,12)
            )

        pdf.image(self.temp_filepath + 'ada_performance.png',
                x=self.get_x_value_image_centre(self.image_width*1.1),
                w=self.image_width*1.1)

        # HYPER PARAMETERS
        if display_hyperparams:
                hp = plotter.analyser.adaboost.get_params()

                pdf.add_page()

                # Make a title for this page
                pdf.set_font(pdf.title_font, 'B', size=14)
                pdf.cell(0, 10, 'AdaBoost Hyperparameters', 
                        align='L')
                pdf.ln(10)
                pdf.set_font('Merriweather', '', 12)

                # Base estimator
                pdf.multi_cell(190, 5, 'The base estimator used: {}'.format(
                        hp['base_estimator']
                ))

                pdf.ln(5)

                # Learning rate
                pdf.multi_cell(190, 5, 'The learning rate: {}'.format(
                        hp['learning_rate']
                ))
                pdf.ln(5)

                # Loss
                pdf.multi_cell(190, 5, 'The loss function: {}'.format(hp['loss']))
                pdf.ln(5)

                # n estimators
                pdf.multi_cell(190, 5, 'The number of estimators: {}'.format(
                        hp['n_estimators']
                ))
                pdf.ln(5)

                # The random state
                pdf.multi_cell(190, 5, 'The random state: {}'.format(
                        hp['random_state']
                ))
                pdf.ln(5)

        # TEXT
        if display_text:
            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/adaboost.txt')

            pdf.add_page()
            self.display_info(pdf,
                    str(BASE_DIR) + '/geochem/resources/infos/adaboost_hyperparams.txt')

    def display_xgboost(self, pdf, plotter, display_hyperparams: bool=True,
            display_text: bool=True):
        """Display XGBoost results in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
            display_hyperparams: Whether or not to display hyper parameters.
            display_text: Whether or not to display text explanations.
        """

        # FIGURES
        pdf.add_page()

        pdf.set_font('Merriweather', '', size=14)
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        pdf.cell(30, txt="XGBoost") 
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        plotter.plot_xgboost_importances(self.temp_filepath + 'xg.png',
                big_to_small=False, figsize=(16,18))

        pdf.image(self.temp_filepath + 'xg.png', 
                x=8,
                w=170)

        # add graph of the biggest 10 data from the XGBOOST graph


        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        xg_big_filename = self.temp_filepath + 'xg_big.png'

        if plotter.plot_xgboost_importances_big_10(xg_big_filename, big_to_small=False,
                                    figsize=(14, 8)):

                pdf.image(xg_big_filename,
                        x=10,
                        w=190)


        # add graph of the smallest 10 data from the XGBOOST graph

        pdf.ln(5)

        xg_small_filename = self.temp_filepath + 'xg_small.png'

        if plotter.plot_xgboost_importances_small_10(xg_small_filename, big_to_small=False,
                                    figsize=(14, 8)):

                pdf.image(xg_small_filename,
                        x=10,
                        w=190)


        plotter.plot_model_predictions(
                plotter.analyser.xgboost_test_predictions, 
                plotter.analyser.xgboost_test_y, 
                self.temp_filepath + 'xg_performance.png',
                figsize=(14,12)
            )

        pdf.image(self.temp_filepath + 'xg_performance.png',
                x=self.get_x_value_image_centre(self.image_width*1.1),
                w=self.image_width*1.1)

        if display_hyperparams:
            
                pdf.add_page()

                hp = plotter.analyser.xgboost.get_params()

                # Make a title for this page
                pdf.set_font(pdf.title_font, 'B', size=14)
                pdf.cell(0, 10, 'XGBoost Hyperparameters', 
                        align='L')
                pdf.ln(10)
                pdf.set_font('Merriweather', '', 12)

                # Objective
                pdf.multi_cell(190, 5, 'The objective: {}'.format(
                        hp['objective']
                ))
                pdf.ln(5)

                # Learning rate
                pdf.multi_cell(190, 5, 'The learning rate: {}'.format(
                        hp['learning_rate']
                ))
                pdf.ln(5)


                # Gamma
                pdf.multi_cell(190, 5, 'Gamma: {}'.format(hp['gamma']))
                pdf.ln(5)

                # The base score
                pdf.multi_cell(190, 5, 'The base score: {}'.format(
                        hp['base_score']
                ))
                pdf.ln(5)

                # Booster used
                pdf.multi_cell(190, 5, 'The booster used: {}'.format(
                        hp['booster']
                ))
                pdf.ln(5)

                # Tree method
                pdf.multi_cell(190, 5, 'Tree method: {}'.format(
                        hp['tree_method']
                ))
                pdf.ln(5)

                # Number of estimators
                pdf.multi_cell(190, 5, 'The number of estimators: {}'.format(
                        hp['n_estimators']
                ))
                pdf.ln(5)

                # Colsamplelevel
                pdf.multi_cell(190, 5, 'The columns sample by level: {}'.format(
                        hp['colsample_bylevel']
                ))
                pdf.ln(5)

                # Colsamplenode
                pdf.multi_cell(190, 5, 'The columns sample by node: {}'.format(
                        hp['colsample_bynode']
                ))
                pdf.ln(5)

                # Colsampletree
                pdf.multi_cell(190, 5, 'The columns sample by tree: {}'.format(
                        hp['colsample_bytree']
                ))
                pdf.ln(5)

                # Importance type
                pdf.multi_cell(190, 5, 'The importance type: {}'.format(
                        hp['importance_type']
                ))
                pdf.ln(5)

                # Interaction constraints
                pdf.multi_cell(190, 5, 'The interaction constraints: {}'.format(
                        hp['interaction_constraints']
                ))
                pdf.ln(5)

                # Monotone constraints
                pdf.multi_cell(190, 5, 'The monotone constraints: {}'.format(
                        hp['monotone_constraints']
                ))
                pdf.ln(5)


                # Max delta
                pdf.multi_cell(190, 5, 'The maximum delta for step: {}'.format(
                        hp['max_delta_step']
                ))
                pdf.ln(5)

                # Max depth
                pdf.multi_cell(190, 5, 'The maximum depth: {}'.format(
                        hp['max_depth']
                ))
                pdf.ln(5)

                # Min child weight
                pdf.multi_cell(190, 5, 'The minimum weight of child: {}'.format(
                        hp['min_child_weight']
                ))
                pdf.ln(5)

                # Random State
                pdf.multi_cell(190, 5, 'The random state: {}'.format(
                        hp['random_state']
                ))
                pdf.ln(5)

        # TEXT
        if display_text:
            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/xgboost.txt')

            pdf.add_page()
            self.display_info(pdf,
                    str(BASE_DIR) + '/geochem/resources/infos/xgboost_hyperparams.txt')

    def display_rf_ada_xg_compare(self, pdf, plot):
        """Display comparison of RF and AdaBoost in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
        """
        n = 10
        intersect = plot.analyser.compare_ada_rf_xg(top_n=n)

        pdf.add_page()

        if len(intersect) == 0:
            pdf.multi_cell(190, h=5, txt='There are no features in common in' + \
                ' the top {} features'.format(n) + \
                'for the trained random forest, AdaBoost or XGBoost.')

        else:
                pdf.multi_cell(190, h=5, txt='The features that are in ' + \
                'the top {} for the '.format(n) + \
                'random forest, AdaBoost and XGBoost are:')
                pdf.ln(5)


                for feature in intersect:
                        pdf.multi_cell(190, h=5, txt='    ' + feature)
                        pdf.ln(5)

    def display_nn(self, pdf, plotter, display_hyperparams: bool=True,
            display_text: bool=True):
        """Display neural network results in report.
        
        Args:
            pdf: The pdf to display in.
            plotter: The plotter that is used to create figures. This must
              be created with the appropriate analyser, in the space calling
              this helper function.
            display_hyperparams: Whether or not to display hyper parameters.
            display_text: Whether or not to display text explanations.
        """
        # FIGURES
        pdf.add_page()

        # Title
        pdf.set_font('Merriweather', '', size=14)
        pdf.set_text_color(0, 112, 192)
        pdf.ln(5)
        self.make_title(pdf, 'Dense Neural Network')
        pdf.ln(10)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_text_color(0, 0, 0)

        '''

        plotter.plot_tf_model_losses(plotter.analyser.history_filename,
                self.temp_filepath + 'nn_loss.png')

        pdf.image(self.temp_filepath + 'nn_loss.png', 
                x=self.get_x_value_image_centre(self.image_width*1.3),
                w=self.image_width*1.3)

        '''

        plotter.plot_model_predictions(
                plotter.analyser.nn_test_predictions, 
                plotter.analyser.nn_test_y, 
                self.temp_filepath + 'nn_performance.png',
                figsize=(14,12)
            )

        pdf.image(self.temp_filepath + 'nn_performance.png',
                x=self.get_x_value_image_centre(self.image_width*1.1),
                w=self.image_width*1.1)

        # HYPER PARAMETERS
        if display_hyperparams:

                pdf.add_page()

                hp = plotter.analyser.nn_params

                # Make a title for this page
                pdf.set_font('Merriweather', '', size=14)
                pdf.cell(0, 10, 'Dense Neural Network Hyperparameters', 
                        align='L')
                pdf.ln(10)
                pdf.set_font('Merriweather', '', 12)

                # N layers
                pdf.multi_cell(190, 5, 'Number of layers: {}'.format(hp['n_layers']))
                pdf.ln(5)

                # Filters
                pdf.multi_cell(190, 5, 'Number of filters per layer: {}'.format(
                        hp['n_filters']))
                pdf.ln(5)

                # Activation function
                pdf.multi_cell(190, 5, 'Activation function: {}'.format(
                        hp['activation']))
                pdf.ln(5)

                # Loss
                pdf.multi_cell(190, 5, 'Loss function: {}'.format(hp['loss']))
                pdf.ln(5)

                # Epochs
                pdf.multi_cell(190, 5, 'Number of epochs: {}'.format(hp['epochs']))
                pdf.ln(5)

                # Random state
                pdf.multi_cell(190, 5, 'Random state: {}'.format(hp['random_state']))
                pdf.ln(5)

        # TEXT
        if display_text:
            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/nn.txt')

            pdf.add_page()
            self.display_info(pdf, str(BASE_DIR) + '/geochem/resources/infos/nn_hyperparams.txt')

    def make_analysis_report(self, analyser, filepath: str, 
            display_text: bool=True):
        """Makes a report based on analysis done.
        
        Args:
            analyser: The analyser to generate a report on.
            filepath: The output filepath for the pdf report.
        """

        pdf = PDF(title='Analysis Report')
        pdf.alias_nb_pages()
        pdf.add_font('Merriweather', fname=str(BASE_DIR) + '/geochem/resources/fonts/Merriweather-Regular.ttf',
                      uni=True)
        pdf.set_font('Merriweather', '', 12)

        plot = plotter.Plotter(analyser)

        # Title page
        self.title_page(pdf=pdf, title='Analysis Report', project=analyser.project)

        self.analysis_table_of_contents(pdf=pdf, analyser=analyser)

        if analyser.stats is not None:
            self.display_analyser_stats(pdf, analyser)

        if analyser.summaries is not None:
            self.display_analyser_summaries(pdf, analyser)

        if analyser.kmeans is not None:
            self.display_k_means(pdf, plot, display_text=display_text)

        if analyser.rf is not None:
            self.display_random_forest(pdf, plot, display_text=display_text)

        if analyser.adaboost is not None:
            self.display_adaboost(pdf, plot, display_text=display_text)

        if analyser.xgboost is not None:
            self.display_xgboost(pdf, plot, display_text=display_text)

        # if analyser.rf is not None and analyser.adaboost is not None and \
        #         analyser.xgboost is not None:
        #     self.display_rf_ada_xg_compare(pdf, plot)

        if analyser.pca is not None:
            self.display_pca(pdf, plot, display_text=display_text)

        if analyser.hca is not None:
            self.display_hca(pdf, plot, display_text=display_text)

        if analyser.nn is not None:
            self.display_nn(pdf, plot, display_text=display_text)

        if analyser.correlations is not None:
            self.display_cc(pdf, plot, display_text=display_text)

        pdf.output(filepath, 'F')

    def make_cleaner_report(self, datacleaner, filename: str, instance_name: str, csv_file_url :str):
        """Makes a cleaner report based on the cleaning performed on dataset.
        Args:
            datacleaner: The DataCleaner to generate a report on.
            filename: The output filename for the pdf.
        """
        # Initialise pdf
        pdf = PDF(title='Cleaning Report')
        pdf.alias_nb_pages()
        pdf.add_font('Merriweather', fname=str(BASE_DIR) + '/geochem/resources/fonts/Merriweather-Regular.ttf', uni=True)
        pdf.set_font('Merriweather', '', 12)
        pdf.set_fill_color(r=251, g=228, b=213)

        # Title page
        self.title_page(pdf, 'Cleaning Report', instance_name)

        options = datacleaner.options

        self.cleaning_table_of_contents(pdf, options)
        self.cleaning_summary_table(pdf,datacleaner,datacleaner.datacleaning_result,csv_file_url)
       
              
        # If columns have been removed
        for line in datacleaner.datacleaning_result:
            # If columns have been removed
            if 'REMOVE_COLUMNS:' in line:
                #string = line.split('REMOVE_COLUMNS:')[-1]
                result = line.split("detail:")
                change_dict = eval(result[1])
                string = result[0].split('REMOVE_COLUMNS:')[-1]
                pdf.add_page()

                pdf.set_text_color(0, 112, 192)
                pdf.set_font('Merriweather', '', 14)
                pdf.multi_cell(0, h=5, txt='Remove Columns: ')
                pdf.set_text_color(0, 0, 0)
                pdf.ln(4)
                pdf.set_font('Merriweather', '', 12)
                pdf.multi_cell(0, h=5, txt='Description: Columns that have been removed from the dataset.')
                pdf.ln(5)

                columns = string.split(',')
                if len(columns) == 0:
                    pdf.multi_cell(0, h=5, txt='No Columns Removed.')
                else:

                        pdf.set_x(pdf.x + 5)
                        pdf.multi_cell(0, h=5, txt='Columns Removed:')
                        pdf.ln(5)

                        self.make_table(pdf, columns)
            
            # If imputing values was done
            elif 'IMPUTE_VALUES' in line:
                result = line.split("detail:")
                change_dict = eval(result[1])
                string = result[0].split('IMPUTE_VALUES:')[-1]

                pdf.add_page()

                # Start after the MODE word in log
                counter = 4
            
                # Construct mode string
                mode = ''
                while True:
                    if string[counter] == ':':
                        break
                    mode += string[counter]
                    counter += 1

                # Get only columns now
                #string = line.split('IMPUTE_VALUES:MODE' + mode + ':')[-1]
                #columns = string.split(',')
                columns = list(change_dict.keys())
                 # Print columns
                pdf.set_text_color(0, 112, 192)
                pdf.set_font('Merriweather', '', 14)
                pdf.multi_cell(0, h=5, txt='Columns Imputed: ')
                pdf.ln(4)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Merriweather', '', 12)
                pdf.multi_cell(0, h=5, txt='Description: Replaced emplty columns using the method selected.')
                pdf.ln(5)

                if len(columns) == 0:
                    pdf.multi_cell(0, h=5, txt='No columns imputed.')
                else:
                        pdf.set_x(pdf.x + 5)
                        pdf.multi_cell(0, h=5, txt='Columns Imputed ' + \
                                'using {}:'.format(mode))
                         
                        pdf.ln(5)
                        self.cleaning_function_table(pdf,change_dict)
                        #for column, (diff_rows, num_changes) in change_dict.items():
                                #print(f"Column {column} differs in rows {diff_rows}, with {num_changes} values changed.")
                                #pdf.multi_cell(0, h=5, txt=f'Column {column} differs in rows {diff_rows}, with {num_changes} values changed.')
                                
                                #pdf.ln(3)

            # If handling the inequality cells
            elif 'HANDLE_INEQUALITIES' in line:
                result = line.split("detail:")
                change_dict = eval(result[1])
                string = result[0].split('HANDLE_INEQUALITIES:')[-1]

                pdf.add_page()

                columns = list(change_dict.keys())

                pdf.set_text_color(0, 112, 192)
                pdf.set_font('Merriweather', '', 14)
                pdf.multi_cell(0, h=5, txt='Removed inequalities in columns: ')
                pdf.ln(4)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Merriweather', '', 12)
                pdf.multi_cell(0, h=5, txt='Description: Columns that have had their inequalities converted to a numeric value')
                pdf.ln(5)

                if len(columns) == 0:
                    pdf.multi_cell(0, h=5, txt='No columns were searched ' + \
                            'for < or > symbols.')
                else:
                        pdf.set_x(pdf.x + 5)
                        pdf.multi_cell(0, h=5, txt='Columns checked for < or >' + \
                                ' cells')
                        pdf.ln(5)

                        self.cleaning_function_table(pdf,change_dict)
                        #self.make_table(pdf, columns)

            # If converting units
            elif 'UNITS' in line:
                result = line.split("detail:")
                change_dict = eval(result[1])
                string = result[0].split('UNITS:')[-1]

                pdf.add_page()
                pdf.set_text_color(0, 112, 192)
                pdf.set_font('Merriweather', '', 14)
                pdf.multi_cell(0, h=5, txt='Converted units in columns: ')
                pdf.ln(4)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Merriweather', '', 12)
                pdf.multi_cell(0, h=5, txt='Description: Columns that have had their units converted to the given units')
                pdf.ln(5)
                columns = string.split(',')
                pdf.multi_cell(0, h=5, txt='Columns were converted to {}'.format(columns[0]))
                pdf.set_x(pdf.x + 5)
                #pdf.multi_cell(0, h=5, txt='Columns Removed:')
                pdf.ln(5)
                self.make_table(pdf, columns[1:])
                
               

            # Removal of duplicate units
            elif 'DUPLICATES' in line:
                string = line.split('DUPLICATES:')[-1]

                pdf.add_page()


                pdf.set_text_color(0, 112, 192)
                pdf.set_font('Merriweather', '', 14)
                pdf.multi_cell(0, h=5, txt='Removed duplicate entries: ')
                pdf.ln(4)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Merriweather', '', 12)
                pdf.multi_cell(0, h=5, txt='Description: Duplicate entries have been removed from the dataset')
                pdf.ln(5)

                pdf.multi_cell(0, h=5, txt=string)

            # Removing entries
            elif 'REMOVE_ENTRIES' in line:
                string = line.split('REMOVE_ENTRIES:')[-1]

                pdf.add_page()

                pdf.set_text_color(0, 112, 192)
                pdf.set_font('Merriweather', '', 14)
                pdf.multi_cell(0, h=5, txt='Entries removed: ')
                pdf.ln(4)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Merriweather', '', 12)
                pdf.multi_cell(0, h=5, txt='Description: Entries that were removed from the first ten rows')
                pdf.ln(5)

                pdf.multi_cell(0, h=5, txt=string)
        
            elif 'REMOVE_NON_NUMERIC' in line:
                result = line.split("detail:")
                change_dict = eval(result[1])
                string = result[0].split('REMOVE_NON_NUMERIC:')[-1]

                pdf.add_page()

                columns = list(change_dict.keys())

                pdf.set_text_color(0, 112, 192)
                pdf.set_font('Merriweather', '', 14)
                pdf.multi_cell(0, h=5, txt='Removed non-numeric values in columns: ')
                pdf.ln(4)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Merriweather', '', 12)
                pdf.multi_cell(0, h=5, txt='Description: Columns that have had non-numeric values removed')
                pdf.ln(5)


                if len(columns) == 0:
                    pdf.multi_cell(0, h=5, txt='No Non Numeric Columns found to remove ')
                else:
                        pdf.set_x(pdf.x + 5)
                        pdf.multi_cell(0, h=5, txt='Columns that are found with Non Numeric values are:')
                        pdf.ln(5)
                        self.cleaning_function_table(pdf,change_dict)        
                        #self.make_table(pdf, columns)

            # Removal of duplicate units
            elif 'REMOVED_COMMA_SEP' in line:
                result = line.split("detail:")
                change_dict = eval(result[1])
                string = result[0].split('REMOVED_COMMA_SEP:')[-1]

                pdf.add_page()


                pdf.set_text_color(0, 112, 192)
                pdf.set_font('Merriweather', '', 14)
                pdf.multi_cell(0, h=5, txt='Removed comma seperated values: ')
                pdf.ln(4)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Merriweather', '', 12)
                pdf.multi_cell(0, h=5, txt='Description: Removes comma sepeartion from numeric values')
                pdf.ln(5)
                columns = list(change_dict.keys())
                if len(columns) == 0:
                    pdf.multi_cell(0, h=5, txt='No Numeric Columns were found with commas')
                else:
                        pdf.set_x(pdf.x + 5)
                        pdf.multi_cell(0, h=5, txt='Columns that are found with comma are:')
                        pdf.ln(5)
                        self.cleaning_function_table(pdf,change_dict) 
                
            # Writing to file
            elif 'WRITE_CSV' in line:
                pdf.add_page()
                pdf.multi_cell(0, h=5, txt='Wrote to file.')


        # Save pdf
        pdf.output(filename, 'F')

    def cleaning_function_table(self, pdf, change_dict):              
                pdf.set_font('Merriweather', '', 12)
                pdf.set_text_color(0, 0, 0)
                remove_columns = []
                impute_columns = []
                inequalities_columns = []
                units_columns = []
                non_numeric_columns = []
                comma_sep_columns = []
                top= pdf.y
                self.header_cleaning_function_table(pdf,top)    
                pdf.y = top+8  
                count=1
                for column, (diff_rows, num_changed,percentage_changed) in change_dict.items():
                        changed_y = pdf.y
                        if pdf.y >= 270:
                                pdf.add_page()
                                top=pdf.y
                                self.header_cleaning_function_table(pdf,top) 
                                pdf.y = top+8
                                changed_y = top+8  
                        pdf.x = 17              
                        curX = pdf.x  
                        if(count%2 ==0):
                              pdf.set_fill_color(r=255, g=136, b=59)  
                        else:
                              pdf.set_fill_color(r=251, g=228, b=213)      
                        pdf.multi_cell(45, 8, column, fill=True)
                        curX += 45
                        pdf.y = changed_y 
                        pdf.multi_cell(72, 8, str(num_changed), fill=True)
                        curX += 72
                        pdf.y = changed_y 
                        pdf.multi_cell(60, 8, str(percentage_changed), fill=True)
                        curX += 60
                        pdf.y = changed_y +8          
                        #pdf.ln(2)
                        count +=1
    def header_cleaning_function_table(self,pdf,top):
                column_headers = ['Column', 'No of Values Changed', 'Percentage Changed']
                pdf.y = top
                top=pdf.y
                count =1
                pdf.x = 17
                pdf.set_fill_color(r=255, g=136, b=59)         
                pdf.multi_cell(45, 8, column_headers[0], fill=True)
                pdf.y = top 
                pdf.multi_cell(72, 8, column_headers[1], fill=True)
                pdf.y = top 
                pdf.multi_cell(60, 8, column_headers[2], fill=True)     
