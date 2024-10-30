
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QSpacerItem, QHBoxLayout,
                               QPushButton, QFileDialog, QMessageBox, QTreeView, QHeaderView, QLabel,
                               QFrame, QTableView, QStackedWidget, QComboBox, QInputDialog, QGridLayout, QSizePolicy,
                               QStyledItemDelegate, QMenu, QListWidget, QDialog, QTextBrowser,QScrollArea,QSplashScreen,QTableView, QScrollArea, QTableWidget, QTableWidgetItem) 

from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QAction, QPixmap,QColor, QIcon,QPainter, QColor, QPixmap,QBrush 
from PySide6.QtCore import Qt, QDir, QDateTime, QTimer,  QSize
from PySide6.QtSvg import QSvgRenderer


import sys
import json
from scipy.stats import median_abs_deviation
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from itertools import combinations
import piflib.pif_calculator as pif
import seaborn as sns
import matplotlib.colors as mcolors
import io


from rpy2 import robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri


# Activate pandas <-> R DataFrame conversion
pandas2ri.activate()

# Import the sdcMicro package
sdcMicro = importr('sdcMicro')




class NumericStandardItem(QStandardItem):
    def __init__(self, text):
        super().__init__(text)
        try:
            self.numeric_value = float(text)
        except ValueError:
            self.numeric_value = None

    def __lt__(self, other):
        if self.numeric_value is not None and other.numeric_value is not None:
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        combo_box = QComboBox(parent)
        combo_box.addItems(["Categorical", "Continuous"])
        return combo_box

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class metaprivBIDS(QMainWindow):

    def __init__(self):
        super().__init__()
        self.file_path, self.data, self.column_unique_counts, self.metadata, self.sensitive_attr = None, None, {}, {}, None
        self.original_data = pd.DataFrame()  
        self.original_columns = {}  
        self.combined_values = {} 
        self.combined_values_history = {}  
        
        self.initUI()

          

    def show_splash_screen(self):
        splash_pix = QPixmap("hacker_8334462.png")  # Change to your splash image path
        self.splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        self.splash.setMask(splash_pix.mask())
        self.splash.setAutoFillBackground(True)

        # Center the splash screen relative to the main window
        self.splash.move(self.x() + (self.width() - splash_pix.width()) // 2,
                         self.y() + (self.height() - splash_pix.height()) // 2)

        # Display the splash screen
        self.splash.show()

        # Timer to close the splash screen and show the main window
        QTimer.singleShot(2000, self.close_splash)


    def close_splash(self):
        self.splash.close()
        self.show() 
     
    def initUI(self):

        """
        Initialize the user interface of the File Analyzer application.
        Sets up the main window, styles it, and initializes the pages using dedicated methods.
        """
        self.setWindowTitle('MetaprivBIDS')
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet("background-color: #121212; color: #FFFFFF;")

        self.setupCentralWidget()
        self.initializePages()

        self.show_splash_screen()

    def setupCentralWidget(self):
        """
        Setup the central widget and the main layout.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

    def initializePages(self):
        """
        Initialize all pages and add them to the stacked widget.
        """
        self.setupMainPage()
        self.setupPrivacyInfoPage()
        self.setupPreviewPage()
        self.setupSudaInfoPage()

    def setupMainPage(self):
        """
        Setup the main page with buttons and frames.
        """
        self.main_page = QWidget()
        main_layout = QVBoxLayout(self.main_page)
        self.add_buttons(main_layout)
        self.add_frames(main_layout)

        # Additional buttons or components specific to the main page
        self.setupMainPageSpecificComponents(main_layout)
        
        self.stacked_widget.addWidget(self.main_page)

    def setupMainPageSpecificComponents(self, layout):
        """
        Setup components specific to the main page such as custom buttons.
        """
        combine_button_layout = QHBoxLayout()
        combine_button_layout.addStretch(1)
        combine_button_layout.setContentsMargins(0, -5, 0, 0)  # Adjust -5 to move the button upwards

        combine_column_button = QPushButton('Compute K-Combined')
        combine_column_button.setFixedSize(200, 20)  # Set the button size to 50x20
        combine_column_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #94127e; 
                        color: white; 
                        font-family: 'Roboto'; /* Set font family */
                        font-weight: bold; 
                        font-size: 14px;
                        border-radius: 2px; 
                        padding: 5px;
                        min-height: 20px;

                    }}
                    QPushButton:pressed {{
                        background-color: #808080; /* Change color when pressed */
                        border-radius: 8px; /* Optional: slightly decrease border radius */
                    }}
                    QPushButton:hover {{
                        background-color: #b0529c; /* Change to a matte or darker color on hover */
                        color: white; /* Keep text color white */
                    }}
                """)



        combine_column_button.clicked.connect(self.compute_combined_column_contribution)
        combine_button_layout.addWidget(combine_column_button)
        layout.addLayout(combine_button_layout)









    def handle_descrip_icon(self):
        # Hide the icon when Compute CIG is pressed
        self.icon_label_descrip.hide()  # Assuming self.icon_label is the QLabel for the icon

        # Call the original action (e.g., compute CIG)
        self.describe_cig()

    def addPrivacyButtons(self, layout):
        """
        Add buttons related to privacy calculations on the privacy info page.
        """
        button_layout = QHBoxLayout()
        buttons = [
            ('Compute CIG', self.handle_compute_cig, '#94127e'),
            ('Summary Statistics CIG', self.handle_descrip_icon, '#94127e'),
            ('Generate Heatmap', self.generate_heatmap, '#94127e'),
            ('Save CSV', self.save_cig_to_csv, '#94127e'),
            ('Back to Main', self.show_main_page, '#94127e')  # Including the Describe CIG button here
        ]
        
        # Load the icon for the 'Back to Main Menu' button
        arrow_icon = QIcon("output-onlinepngtools copy 2.png")  # Make sure 'logo.png' exists in the correct path

        for text, action, color in buttons:
            button = QPushButton(text)
            
            # Special style for 'Back to Main Menu' button
            if text == 'Back to Main':
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color}; 
                        color: white;  /* Change text color to red */
                        font-family: 'Roboto'; /* Set font family */
                        font-weight: bold; 
                        font-size: 14px;
                        border-radius: 2px; 
                        padding: 5px;
                        min-height: 20px;
                    }}
                    QPushButton::icon {{
                        margin-right: 20px;  /* Adds space between the text and the icon */
                    }}
                    QPushButton:pressed {{
                        background-color: #808080; /* Change color when pressed */
                        border-radius: 8px; /* Optional: slightly decrease border radius */
                    }}
                    QPushButton:hover {{
                        background-color: #b0529c; /* Change to a matte or darker color on hover */
                        color: white; /* Keep text color white */
                    }}
                """)

                # Set the icon for the button
                button.setIcon(arrow_icon)
                button.setIconSize(QSize(24, 24))  # Adjust icon size if needed
                button.setLayoutDirection(Qt.RightToLeft)

            else:
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color}; 
                        color: white; 
                        font-family: 'Roboto'; /* Set font family */
                        font-weight: bold; 
                        font-size: 14px;
                        border-radius: 2px; 
                        padding: 5px;
                        min-height: 20px;
                    }}
                    QPushButton:pressed {{
                        background-color: #808080; /* Change color when pressed */
                        border-radius: 8px; /* Optional: slightly decrease border radius */
                    }}
                    QPushButton:hover {{
                        background-color: #b0529c; /* Change to a matte or darker color on hover */
                        color: white; /* Keep text color white */
                    }}
                """)
            # Connect button to action
            button.clicked.connect(action)
            button_layout.addWidget(button)

        # Add the final layout
        layout.addLayout(button_layout)

    def handle_compute_cig(self):
        # Hide the icon when Compute CIG is pressed
        self.icon_label.hide()  # Assuming self.icon_label is the QLabel for the icon

        # Call the original action (e.g., compute CIG)
        self.compute_cig()

    def addCigResultDisplay(self, layout):
        """
        Add a QTextBrowser inside the CIG result frame to display CIG results on the privacy info page.
        """
        # Create a QTextBrowser for CIG results
        self.cig_result_browser = QTextBrowser(self.cig_result_frame)  # Place it inside the frame
        self.cig_result_browser.setOpenExternalLinks(True)
        self.cig_result_browser.setStyleSheet("border: none;")  # Remove border to blend into the frame
        layout.addWidget(self.cig_result_browser)

    def setupPrivacyInfoPage(self):
        """
        Setup the privacy information page with buttons and static placeholder frames for CIG results and description.
        """
        self.privacy_info_page = QWidget()
        privacy_layout = QVBoxLayout(self.privacy_info_page)
        privacy_layout.setContentsMargins(10, 10, 10, 10)
        privacy_layout.setSpacing(10)

        # Add the buttons
        self.addPrivacyButtons(privacy_layout)

        # Create a horizontal layout to hold the results and the boxplot
        results_layout = QHBoxLayout()

        # Create a label for the CIG results section
        self.cig_results_label = QLabel("Cell Information Gain")
        self.cig_results_label.setAlignment(Qt.AlignLeft)
        self.cig_results_label.setStyleSheet("""
            color: white; 
            background-color: #121212; 
            padding: 5px; 
            font-size: 16px;  /* Set the font size */
            font-weight: bold; /* Make the font bold */
            """)  # Set text color and background
        privacy_layout.addWidget(self.cig_results_label)  # Add the label to the main layout
        


        temp_icon_path = "colorkit.svg"  # Change to your actual path
        

        # Add a placeholder frame for the CIG results
        self.cig_result_frame = QFrame()
        self.cig_result_frame.setFrameShape(QFrame.StyledPanel)
        self.cig_result_frame.setStyleSheet("background-color: #121212; border: 0.2px solid #FFFFFF;")  
        self.cig_result_frame.setMinimumHeight(400)  # Set a minimum height for the frame
        self.cig_result_frame.setMaximumHeight(400)  # Set a maximum height for the frame

        # Add the CIG result frame to the horizontal layout
        results_layout.addWidget(self.cig_result_frame)



        # Create a placeholder frame for the boxplot
        self.boxplot_frame = QFrame()
        self.boxplot_frame.setFrameShape(QFrame.StyledPanel)
        self.boxplot_frame.setStyleSheet("background-color: #121212; border: 0.5px solid #FFFFFF;")  
        self.boxplot_frame.setMinimumHeight(400)  # Match the height
        self.boxplot_frame.setFixedWidth(400)  # Set a fixed width for the boxplot frame

        # Add the boxplot frame to the horizontal layout
        results_layout.addWidget(self.boxplot_frame)

        # Create a QLabel for displaying the boxplot
        self.boxplot_label = QLabel(self.boxplot_frame)
        self.boxplot_label.setMinimumHeight(400)  # Match the height
        self.boxplot_label.setFixedWidth(400)  # Set a fixed width for the boxplot display
        self.boxplot_label.setScaledContents(True)  # Allow the contents to scale

        # Load the temporary PNG icon and scale it to 32x32 pixels
        
        description_layout = QVBoxLayout(self.boxplot_frame)
        # Create a separate QLabel for the small PNG icon
        self.icon_label = QLabel(self.boxplot_frame)
        self.icon_label.setFixedSize(40, 40)  # Set a fixed size for the icon label
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        icon_pixmap = QPixmap(temp_icon_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(icon_pixmap)  # Set the scaled pixmap into the icon QLabel
        description_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)


        # Add the horizontal layout to the main privacy layout
        privacy_layout.addLayout(results_layout)

        # Create a label for the section between the CIG results and the boxplot
        self.section_label = QLabel("Statistics Summary of Cell Information gain")
        self.section_label.setAlignment(Qt.AlignLeft)
        self.section_label.setStyleSheet("""
            color: white; 
            background-color: #121212; 
            padding: 5px; 
            font-size: 16px;  /* Set the font size */
            font-weight: bold; /* Make the font bold */
            """)
        
        privacy_layout.addWidget(self.section_label)  # Add the section label to the main layout

        # Create a QTableWidget for displaying CIG results
        self.cig_table_widget = QTableWidget(self.cig_result_frame)  # Create the table widget
        self.cig_table_widget.setRowCount(0)  # Initially set row count to 0
        self.cig_table_widget.setColumnCount(0)  # Initially set column count to 0

        # Set the style of the QTableWidget
        self.cig_table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #121212; 
                color: white;
            }
            QHeaderView::section {
                background-color: #121212;  
                color: white;  
                font-weight: bold;  /* Optional: make header text bold */
            }
        """)


        # Create a scroll area for the QTableWidget
        self.cig_result_scroll_area = QScrollArea(self.cig_result_frame)
        self.cig_result_scroll_area.setWidgetResizable(True)
        self.cig_result_scroll_area.setWidget(self.cig_table_widget)  # Set the QTableWidget as the widget of the scroll area

        # Add the scroll area to the results frame
        cig_result_layout = QVBoxLayout(self.cig_result_frame)
        cig_result_layout.addWidget(self.cig_result_scroll_area)





        # Add a placeholder frame for the CIG description
        self.cig_description_frame = QFrame()
        self.cig_description_frame.setFrameShape(QFrame.StyledPanel)
        self.cig_description_frame.setStyleSheet("background-color: #121212; border: 0.5px solid #94127e;")  # Background for description
        self.cig_description_frame.setMinimumHeight(250)  # Increased height for better visibility
        self.cig_description_frame.setMaximumHeight(250)  # Set a maximum height for the frame

        privacy_layout.addWidget(self.cig_description_frame)
        
        description_layout = QVBoxLayout(self.cig_description_frame)
        self.icon_label_descrip = QLabel(self.cig_description_frame)
        self.icon_label_descrip.setFixedSize(40, 40)  # Set a fixed size for the icon label
        self.icon_label_descrip.setStyleSheet("background: transparent; border: none;")
        icon_pixmap = QPixmap(temp_icon_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label_descrip.setPixmap(icon_pixmap)  
        description_layout.addWidget(self.icon_label_descrip, alignment=Qt.AlignCenter)


        # Create a QLabel for displaying CIG description
        self.cig_description_label = QLabel("PIF Percentile: To be computed.")
        self.cig_description_label.setAlignment(Qt.AlignCenter)
        self.cig_description_label.setStyleSheet("color: white;")  # Set text color to white
        privacy_layout.addWidget(self.cig_description_label)



        # Set up the stacked widget
        self.stacked_widget.addWidget(self.privacy_info_page)

    def save_boxplot_rig_values(self):
        # Check if 'RIG' column exists in cigs_df_display
        if 'RIG' in self.cigs_df_display.columns:
            # Extract the RIG data
            rig_data = self.cigs_df_display['RIG'].values
            
            # Check if there's enough data to create a meaningful boxplot
            if len(rig_data) < 5:
                print("Not enough data to generate a boxplot.")
                return None

            # Calculate median and MAD
            median_value = np.median(rig_data)
            mad = median_abs_deviation(rig_data)

            # Set the box bounds: 1.5 MADs above and below the median
            lower_bound = median_value - 1.5 * mad  # 1.5 MAD below the median
            upper_bound = median_value + 1.5 * mad  # 1.5 MAD above the median

            # Set the whiskers: 3 MADs above and below the median
            whisker_low = median_value - 3 * mad  # 3 MAD below the median
            whisker_high = median_value + 3 * mad  # 3 MAD above the median

            # Identify outliers: values outside the whiskers
            outliers = rig_data[(rig_data < whisker_low) | (rig_data > whisker_high)]

            # Create a figure and axis
            fig, ax = plt.subplots(figsize=(6, 4))  # Set the size of the plot

            # Create custom boxplot with the median in the middle and MAD-based whiskers
            ax.bxp([{
                'med': median_value,      # Center on the median
                'q1': lower_bound,        # 1.5 MAD below the median
                'q3': upper_bound,        # 1.5 MAD above the median
                'whislo': whisker_low,    # 3 MAD below the median
                'whishi': whisker_high,   # 3 MAD above the median
                'fliers': outliers        # Outliers
            }], showfliers=True)

            # Set title and labels
            ax.set_title(f'Custom Boxplot of RIG Values (MAD Spread = 3) / MAD = {mad:.2f}')

            # Customize the boxplot style (remove spines)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)

            # Render the figure to a byte array in PNG format
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)  # Close the figure to free memory

            # Load the image data from the buffer and convert it to a QPixmap
            image = QPixmap()
            image.loadFromData(buf.getvalue())
            
            return image

    def display_boxplot(self):
        # Get the QPixmap with the boxplot
        pixmap = self.save_boxplot_rig_values()

        # Set the pixmap directly to the QLabel
        self.boxplot_label.setPixmap(pixmap)

        # Optionally, adjust the size and layout
        self.boxplot_label.setScaledContents(True)  # Scale the contents to fit the label
        self.boxplot_label.show()

    def compute_cig(self):
        """
        Computes and displays the Categorical Information Gain (CIG) for selected columns in the DataFrame.
        """
        selected_columns = self.get_selected_columns()

        if not selected_columns:
            self.cig_table_widget.clear()  # Clear previous data
            self.cig_description_label.setText("No columns selected.")  # Inform user
            return

        df = self.data[selected_columns]

        # Debug: Print the selected DataFrame
        print("Selected DataFrame for CIG computation:")

        if df.empty:
            self.cig_table_widget.clear()  # Clear previous data
            self.cig_description_label.setText("DataFrame is empty.")  # Inform user
            return

        df = df.astype(object).where(pd.notnull(df), 'NaN')

        mask_value, ok = QInputDialog.getText(None, 'Input Mask Value', 'Enter a mask value (or type "NaN" for missing values):')

        if ok and mask_value != '':
            try:
                if mask_value.lower() == 'nan':
                    mask = df == 'NaN'
                else:
                    mask_value = float(mask_value)
                    mask = df == mask_value
            except ValueError:
                self.cig_table_widget.clear()  # Clear previous data
                self.cig_description_label.setText("Invalid mask value entered.")  # Inform user
                return

            cigs = pif.compute_cigs(df)
            # Use the original index when creating the DataFrame
            cigs_df = pd.DataFrame(cigs, index=df.index)  # Retain original index
            cigs_df[mask] = 0
        else:
            cigs = pif.compute_cigs(df)
            cigs_df = pd.DataFrame(cigs, index=df.index)  # Retain original index

        cigs_df['RIG'] = cigs_df.sum(axis=1)

        # Debug: Print the computed CIG DataFrame
        print("Computed CIG DataFrame:")

        percentile, ok = QInputDialog.getInt(None, 'Input Percentile', 'Enter percentile (0-100):', 95, 0, 100)

        if not ok:
            self.cig_table_widget.clear()  # Clear previous data
            self.cig_description_label.setText("Percentile input canceled.")  # Inform user
            return

        pif_value = np.percentile(cigs_df['RIG'], percentile)

        self.cigs_df = cigs_df
        self.cigs_df_display = cigs_df.sort_values(by='RIG', ascending=False)  # Ensure you set this correctly

        # Set up the QTableWidget
        self.cig_table_widget.setRowCount(len(self.cigs_df_display))  # Set the number of rows
        self.cig_table_widget.setColumnCount(len(self.cigs_df_display.columns))  # Set the number of columns
        self.cig_table_widget.setHorizontalHeaderLabels(self.cigs_df_display.columns.tolist())  # Set header labels
        self.cig_table_widget.horizontalHeader().setStretchLastSection(True)  # Allow the last section to stretch
        self.cig_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Stretch all columns


     

        # Populate the QTableWidget with data from the DataFrame
        for row in range(len(self.cigs_df_display)):
            for col in range(len(self.cigs_df_display.columns)):
                value = self.cigs_df_display.iat[row, col]
                # Format to 2 decimal places if numeric
                if isinstance(value, (int, float)):
                    value = f"{value:.2f}"
                item = QTableWidgetItem(str(value))  # Create a QTableWidgetItem
                self.cig_table_widget.setItem(row, col, item)  # Add item to the table
                
                # Make the RIG column bold and set background color
                if self.cigs_df_display.columns[col] == 'RIG':
                    font = item.font()
                    font.setBold(True)  # Set the font to bold
                    item.setFont(font)  # Apply the bold font to the item
                    item.setBackground(QColor(169, 169, 169))  # Set background color to light grey


        self.display_boxplot()

        # Resize columns to fit content
        for i in range(len(self.cigs_df_display.columns)):
            self.cig_table_widget.resizeColumnToContents(i)

        # Display the PIF value and percentile in the labels
        self.cig_description_label.setText(f"PIF at {percentile}th percentile: {pif_value:.2f}") 
        self.cig_description_label.setStyleSheet("color: white;")






    def save_cig_to_csv(self):
        """
        Saves the computed CIG DataFrame to a CSV file.
        Prompts the user to specify a file location and then saves the DataFrame.
        """
        if hasattr(self, 'cigs_df_display') and not self.cigs_df_display.empty:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self, "Save CIG to CSV", "", "CSV Files (*.csv)", options=options)

            if file_path:
                try:
                    self.cigs_df_display.to_csv(file_path, index=True)
                    QMessageBox.information(self, "Success", f"CIG data successfully saved to {file_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"An error occurred while saving the file: {str(e)}")
            else:
                QMessageBox.information(self, "Canceled", "Save operation canceled.")
        else:
            QMessageBox.warning(self, "Error", "No CIG data to save. Please compute CIG first.")

    def setupSudaInfoPage(self):
        """
        Setup the SUDA information page with smaller buttons at the top and two side-by-side frames.
        """
        self.suda_info_page = QWidget()
        suda_layout = QVBoxLayout(self.suda_info_page)
        suda_layout.setContentsMargins(10, 10, 10, 10)  # Outer margins for the main layout
        suda_layout.setSpacing(10)  # Set spacing between widgets in the layout

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()

        # Align buttons to the left
        button_layout.setAlignment(Qt.AlignLeft)

        # Create the 'SU' button (smaller button)
        su_button = QPushButton('SUDA2 Computation')
        su_button.setFixedSize(200, 20)  # Set the button size to 50x20
        su_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #94127e; 
                        color: white; 
                        font-family: 'Roboto'; /* Set font family */
                        font-weight: bold; 
                        font-size: 14px;
                        border-radius: 2px; 
                        padding: 5px;
                        min-height: 20px;
                    }}
                    QPushButton:pressed {{
                        background-color: #808080; /* Change color when pressed */
                        border-radius: 8px; /* Optional: slightly decrease border radius */
                    }}
                    QPushButton:hover {{
                        background-color: #b0529c; /* Change to a matte or darker color on hover */
                        color: white; /* Keep text color white */
                    }}
                """)
        su_button.clicked.connect(self.compute_and_display_suda2_results)

        # Create the 'Back to Main' button (smaller button)
        back_button = QPushButton('Back to Main')
        back_button.setFixedSize(200, 20)  # Set the button size to 100x20


        back_icon = QIcon("output-onlinepngtools copy 2.png")
        back_button.setIcon(back_icon)
        back_button.setIconSize(QSize(24, 24))  # Adjust icon size if needed


        back_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #94127e; 
                        color: white; 
                        font-family: 'Roboto'; /* Set font family */
                        font-weight: bold; 
                        font-size: 14px;
                        border-radius: 2px; 
                        padding: 5px;
                        min-height: 20px;
                    }}
                    QPushButton:pressed {{
                        background-color: #808080; /* Change color when pressed */
                        border-radius: 8px; /* Optional: slightly decrease border radius */
                    }}
                    QPushButton:hover {{
                        background-color: #b0529c; /* Change to a matte or darker color on hover */
                        color: white; /* Keep text color white */
                    }}
                """)

        back_button.clicked.connect(self.show_main_page)

        # Remove the space between the buttons
        button_layout.setSpacing(10)


                # Add Save CSV SUDA button
        save_csv_button = QPushButton('Save CSV')
        save_csv_button.setFixedSize(200, 20)
        save_csv_button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: #94127e; 
                            color: white; 
                            font-family: 'Roboto'; 
                            font-weight: bold; 
                            font-size: 14px;
                            border-radius: 2px; 
                            padding: 5px;
                            min-height: 20px;
                        }}
                        QPushButton:pressed {{
                            background-color: #808080; 
                            border-radius: 8px; 
                        }}
                        QPushButton:hover {{
                            background-color: #b0529c; 
                            color: white; 
                        }}
                    """)
        save_csv_button.clicked.connect(self.save_suda_dataframe_to_csv)  # Connect to the save function



        # Add buttons to the button layout (side by side, aligned to the left)
        button_layout.addWidget(su_button)
        button_layout.addWidget(save_csv_button)  # Add the Save CSV button to the layout
        button_layout.addWidget(back_button)


        # Add button layout at the top of the main layout
        suda_layout.addLayout(button_layout)
        suda_layout.addSpacing(10)

        # Create and add QLabel at the top below the buttons
        title_label = QLabel("SUDA Calculation DIS-Score & Individual Attribution Score")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")  # Set font size and weight
        title_label.setAlignment(Qt.AlignLeft)  # Align the label text
        suda_layout.addWidget(title_label)  # Add the title label to the layout

        # Use a QGridLayout to control the layout of info_frame, att_frame, and indi_frame
        frames_layout = QGridLayout()
        frames_layout.setContentsMargins(5, 5, 5, 5)  # 5px margins around the grid layout
        frames_layout.setSpacing(10)  # 5px spacing between frames

        # Create the info_frame
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("background-color: #2E2E2E; border: 1px solid #FFFFFF;")
        self.info_frame.setFixedHeight(350)  # Set a fixed height for the info_frame
        self.info_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Expand width, fixed height

        # Create a layout for the info_frame
        info_frame_layout = QVBoxLayout(self.info_frame)
        info_frame_layout.setContentsMargins(10, 10, 10, 10)  # Set 10px margins inside the info_frame
        info_label = QLabel("SUDA Information (No Initialized Computation)")
        info_label.setStyleSheet("color: #FFFFFF;")
        info_frame_layout.addWidget(info_label)

        # Add info_frame to the grid layout spanning columns 0 and 1
        frames_layout.addWidget(self.info_frame, 0, 0, 1, 2, Qt.AlignTop)  # Span across column 0 and 1

        # Ensure that the second and third columns do not stretch unnecessarily
        frames_layout.setColumnStretch(2, 0)  # Set the att_frame column not to stretch





        # Create the att_frame (to the right of info_frame)
        self.att_frame = QFrame()
        self.att_frame.setStyleSheet("background-color: #2E2E2E; border: 1px solid #FFFFFF;")
        self.att_frame.setFixedHeight(710)  # Set a fixed height for att_frame
        self.att_frame.setMinimumWidth(400)  # Set minimum width for att_frame
        self.att_frame.setMaximumWidth(400)  # Set maximum width for att_frame
        self.att_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Create a layout for the att_frame
        att_frame_layout = QVBoxLayout(self.att_frame)
        att_frame_layout.setContentsMargins(10, 10, 10, 10)  # Set 10px margins inside the att_frame
        att_label = QLabel("Individual Attribute Information (No Initialized Computation)")
        att_label.setStyleSheet("color: #FFFFFF;")
        att_frame_layout.addWidget(att_label)

        # Add att_frame to the grid layout (first row, second column)
        frames_layout.addWidget(self.att_frame, 0, 2, 2, 1, Qt.AlignTop)  # Span over two rows to keep it aligned with indi_frame

        # Create the indi_frame below the info_frame and aligned closely
        self.indi_frame = QFrame()
        self.indi_frame.setStyleSheet("background-color: #2E2E2E; border: 1px solid #FFFFFF;")
        self.indi_frame.setMaximumWidth(400)  # Set maximum width for indi_frame
        self.indi_frame.setFixedHeight(350)  # Set a fixed height for indi_frame
        self.indi_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Create a layout for indi_frame
        indi_frame_layout = QVBoxLayout(self.indi_frame)
        indi_frame_layout.setContentsMargins(10, 10, 10, 10)  # Set 10px margins inside the indi_frame
        indi_label = QLabel("Individual Frame Information (No Initialized Computation)")
        indi_label.setStyleSheet("color: #FFFFFF;")
        indi_frame_layout.addWidget(indi_label)

        # Create the new_frame (same size as indi_frame)
        self.new_frame = QFrame()
        self.new_frame.setStyleSheet("background-color: #2E2E2E; border: 1px solid #FFFFFF;")
        self.new_frame.setFixedHeight(350)  # Set a fixed height for indi_frame
        self.new_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


        # Create a layout for new_frame
        self.new_frame_layout = QVBoxLayout(self.new_frame)
        self.new_frame_layout.setContentsMargins(10, 10, 10, 10)  # Set 10px margins inside the new_frame
        new_label = QLabel("New Frame Information")
        new_label.setStyleSheet("color: #FFFFFF;")
        self.new_frame_layout.addWidget(new_label)

        # Add new_frame to the grid layout (row 1, column 0)
        frames_layout.addWidget(self.new_frame, 1, 0, Qt.AlignTop)

        # Add a spacer item between new_frame and indi_frame to create space between the frames
        spacer_between_frames = QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)  # 100px wide spacer

        # Add the spacer (row 1, column 1) to push indi_frame to the right
        frames_layout.addItem(spacer_between_frames, 1, 1)

        # Add indi_frame directly after the spacer (row 1, column 2)
        frames_layout.addWidget(self.indi_frame, 1, 1, Qt.AlignTop)


        # Add the frames_layout (containing all frames) to the main vertical layout (suda_layout)
        suda_layout.addLayout(frames_layout)

        # Add stretch to push the layout content down if needed
        suda_layout.addStretch()

        # Add the complete SUDA info page to the stacked widget
        self.stacked_widget.addWidget(self.suda_info_page)

        # Optionally, force the layout to update
        suda_layout.update()

    def save_suda_dataframe_to_csv(self):
        """
        This function saves the SUDA DataFrame (df) to a CSV file.
        """
        if hasattr(self, 'df') and not self.df.empty:
            # Show a file dialog to choose where to save the CSV
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getSaveFileName(self, "Save SUDA DataFrame as CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
            
            if file_name:
                try:
                    # Save the DataFrame (df) to the chosen CSV file
                    self.df.to_csv(file_name, index=False)
                    QMessageBox.information(self, "Success", f"SUDA DataFrame saved successfully to {file_name}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"An error occurred while saving the CSV file: {e}")
            else:
                QMessageBox.information(self, "Cancelled", "Saving SUDA DataFrame as CSV was cancelled.")
        else:
            QMessageBox.warning(self, "No Data", "The SUDA DataFrame is empty or not available.")

    def save_and_display_boxplot_in_frame(self):
        # Clear any previous widgets in the layout to avoid duplication
        while self.new_frame_layout.count():
            child = self.new_frame_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Check if 'dis-score' column exists in df_copy
        if 'dis-score' in self.df_copy.columns:
            # Extract the dis-score data
            dis_data = self.df_copy['dis-score'].values

            # Check if there's enough data to create a meaningful boxplot
            if len(dis_data) < 5:
                print("Not enough data to generate a boxplot.")
                return None

            # Calculate median and MAD
            median_value = np.mean(dis_data)
            mad = median_abs_deviation(dis_data)

            # Set the box bounds: 1.5 MADs above and below the median
            lower_bound = median_value - 1.5 * mad  # 1.5 MAD below the median
            upper_bound = median_value + 1.5 * mad  # 1.5 MAD above the median

            # Set the whiskers: 3 MADs above and below the median
            whisker_low = median_value - 3 * mad  # 3 MAD below the median
            whisker_high = median_value + 3 * mad  # 3 MAD above the median

            # Identify outliers: values outside the whiskers
            outliers = dis_data[(dis_data < whisker_low) | (dis_data > whisker_high)]

            # Create a figure and axis for the boxplot
            fig, ax = plt.subplots(figsize=(6, 4))  # Set the size of the plot

            # Create custom boxplot with the median in the middle and MAD-based whiskers
            ax.bxp([{
                'med': median_value,      # Center on the median
                'q1': lower_bound,        # 1.5 MAD below the median
                'q3': upper_bound,        # 1.5 MAD above the median
                'whislo': whisker_low,    # 3 MAD below the median
                'whishi': whisker_high,   # 3 MAD above the median
                'fliers': outliers        # Outliers
            }], showfliers=True)

            # Set title and labels
            ax.set_title(f'Custom Boxplot of DIS-Score (MAD Spread = 3) / MAD = {mad:.2f}')

            # Customize the boxplot style (remove spines)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)

            # Save the plot to a byte buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)  # Close the figure to free memory

            # Load the image from the buffer into a QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())

            # Create QLabel to display the boxplot
            self.boxplot_label_su = QLabel(self.new_frame)
            self.boxplot_label_su.setAlignment(Qt.AlignCenter)
            self.boxplot_label_su.setPixmap(pixmap)
            self.boxplot_label_su.setScaledContents(True)  # Scale the contents to fit the label

            # Add the QLabel with the boxplot to the new_frame layout
            self.new_frame_layout.addWidget(self.boxplot_label_su)

    def display_dis_score_boxplot(self):
        # Get the QPixmap with the boxplot for the dis-score
        pixmap = self.save_boxplot_dis_score()

        # Set the pixmap directly to the QLabel
        self.boxplot_label.setPixmap(pixmap)

        # Optionally, adjust the size and layout
        self.boxplot_label.setScaledContents(True)  # Scale the contents to fit the label

    def compute_and_display_suda2_results(self):
        """
        This function computes the SUDA2 metrics, converts object-type columns to numeric codes,
        and updates the frames with the results. The user is asked for the 'missing' value
        and 'DisFraction' in pop-up dialogs.
        """
        # Get selected columns from the DataFrame
        selected_columns = self.get_selected_columns()
        df = self.data[selected_columns]

        if df.empty:
            print("Error: The DataFrame is empty.")
            return

        try:
            # Step 1: Ask user for the 'missing' value (with a default of -999)
            missing_value, ok = QInputDialog.getText(self, "Input Missing Value", 
                                                     "Enter missing value (default: -999):", text="-999")
            if not ok:  # If user cancels the dialog
                return
            missing_value = float(missing_value)  # Convert input to float

            # Step 2: Ask user for the 'DisFraction' (with a default of 0.30)
            dis_fraction, ok = QInputDialog.getDouble(self, "Input DisFraction", 
                                                      "Enter DisFraction (default: 0.30):", 0.30, 0.0, 1.0, 2)
            if not ok:  # If user cancels the dialog
                return

            # Step 3: Convert object-type columns to numeric codes
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype('category').cat.codes

            # Step 4: Convert pandas DataFrame to an R DataFrame (ensure columns are floats)
            r_df = robjects.DataFrame({
                name: robjects.FloatVector(df[name].astype(float)) for name in df.columns
            })

            # Step 5: Call the suda2 function from the sdcMicro package using the user input
            suda_result = sdcMicro.suda2(r_df, missing=missing_value, DisFraction=dis_fraction)

            # Step 6: Extract the relevant components from the suda2 result
            contribution_percent = list(suda_result.rx2('contributionPercent'))
            score = list(suda_result.rx2('score'))
            dis_score = list(suda_result.rx2('disScore'))

            dis_score = [round(x, 4) for x in dis_score]

            

            # Extract attribute_contributions
            attribute_contributions = pd.DataFrame({
                'variable': list(suda_result.rx2('attribute_contributions').rx2('variable')),
                'contribution': list(suda_result.rx2('attribute_contributions').rx2('contribution'))
            })

            # Extract attribute_level_contributions
            attribute_level_contributions = pd.DataFrame({
                'variable': list(suda_result.rx2('attribute_level_contributions').rx2('variable')),
                'attribute': list(suda_result.rx2('attribute_level_contributions').rx2('attribute')),
                'contribution': list(suda_result.rx2('attribute_level_contributions').rx2('contribution'))
            })


            # Extract attribute_level_contributions
            attribute_contributions = pd.DataFrame({
                'variable': list(suda_result.rx2('attribute_contributions').rx2('variable')),
                'contribution': list(suda_result.rx2('attribute_contributions').rx2('contribution'))
            })




            # Round contribution values to 2 decimal places
            attribute_level_contributions['contribution'] = attribute_level_contributions['contribution'].round(2)
            attribute_contributions['contribution'] = attribute_contributions['contribution'].round(2)

            # Sort by 'variable' and 'contribution'
            attribute_level_contributions = attribute_level_contributions.sort_values(by=['variable', 'contribution'], ascending=[True, False])

            # Step 7: Update the info_frame with df_copy (including the dis_score column)
            df_copy = df.copy()
            df_copy['dis-score'] = dis_score
            df_copy = df_copy.sort_values(by='dis-score', ascending=False)

            self.df_copy = df.copy()  # Set df_copy as a class-level attribute
            self.df_copy['dis-score'] = dis_score

            df['dis-score'] = dis_score
            df['score'] = score

            self.df = df


            self.save_and_display_boxplot_in_frame()



            attribute_contributions = attribute_contributions.sort_values(by='contribution', ascending=False)


            self.update_frame_with_dataframe(self.info_frame, df_copy)

            # Step 8: Update the att_frame with attribute_level_contributions
            self.update_frame_with_dataframe(self.att_frame, attribute_level_contributions)

            self.update_frame_with_dataframe(self.indi_frame, attribute_contributions)

        except Exception as e:
            print(f"Error in SUDA2 computation: {e}")

    def update_frame_with_dataframe(self, frame, dataframe):
        """
        This function updates a frame with the contents of a DataFrame, displayed as a table.
        It dynamically applies colors to the 'variable' column if it exists, and adjusts the width
        of the indi_frame based on the size of the column names and the content of each column.
        """
        layout = frame.layout()

        # Clear existing widgets in the frame
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Create QTableWidget to display the DataFrame
        table = QTableWidget()
        table.setRowCount(dataframe.shape[0])  # Set number of rows based on DataFrame
        table.setColumnCount(dataframe.shape[1])  # Set number of columns based on DataFrame
        table.setHorizontalHeaderLabels(dataframe.columns)  # Set column headers

        # Check if 'variable' column exists for coloring
        if 'variable' in dataframe.columns:
            # Get unique variables from the 'variable' column
            unique_variables = dataframe['variable'].unique()
            num_unique_variables = len(unique_variables)

            # Generate colors using a colormap from matplotlib
            cmap = plt.get_cmap('tab20')  # You can try other colormaps like 'viridis', 'plasma', etc.
            variable_colors = {}

            # Assign colors for each unique variable
            for i, variable in enumerate(unique_variables):
                # Normalize color generation based on the number of unique variables
                rgba_color = cmap(i / num_unique_variables)
                # Convert to QColor and store in the variable_colors dictionary
                variable_colors[variable] = QColor(int(rgba_color[0] * 255), int(rgba_color[1] * 255), int(rgba_color[2] * 255))

        # Populate the table with DataFrame contents
        for row in range(dataframe.shape[0]):
            for col in range(dataframe.shape[1]):
                item = QTableWidgetItem(str(dataframe.iat[row, col]))

                # Apply color to the 'variable' column if it exists
                if 'variable' in dataframe.columns and dataframe.columns[col] == 'variable':
                    # Set text color based on the variable value
                    variable_value = dataframe.iat[row, col]
                    item.setForeground(variable_colors[variable_value])

                table.setItem(row, col, item)

        # Add the QTableWidget to the layout of the frame
        layout.addWidget(table)

        # --- Adjust the width of the `indi_frame` based on both column name size and content ---
        if frame == self.indi_frame:  # Ensure this adjustment is ONLY for indi_frame
            # Iterate through each column to calculate the required width based on both the column name and the content
            for col in range(dataframe.shape[1]):
                # Calculate the width needed for the column name
                column_name = dataframe.columns[col]
                column_name_width = table.fontMetrics().horizontalAdvance(column_name)

                # Calculate the width needed for the content in the column (longest cell content)
                max_content_width = max([table.fontMetrics().horizontalAdvance(str(dataframe.iat[row, col])) for row in range(dataframe.shape[0])])

                # Set the column width to the larger of the column name width or content width
                column_width = max(column_name_width, max_content_width) + 40  # Add some padding to the width
                table.setColumnWidth(col, column_width)

            # Calculate the total width of the table based on the column widths
            total_column_width = sum([table.columnWidth(i) for i in range(table.columnCount())])

            # Set the frame width to accommodate both the column names and content
            frame.setFixedWidth(total_column_width + table.verticalHeader().width() + 40)  # Add padding for the vertical header
            frame.adjustSize()  # Force layout to update the size



    def setupPreviewPage(self):
        """
        Setup the preview page with a table view and navigation buttons including a 'Back to Main' button.
        """
        self.preview_page = QWidget()
        preview_layout = QVBoxLayout(self.preview_page)
        preview_layout.setContentsMargins(0, 0, 0, 0)  # No outer margins
        preview_layout.setSpacing(10)  # Adjust spacing between widgets



        # Create the 'Back to Main' button and place it at the top of the layout
        back_button = QPushButton('Back to Main')
        back_button.setFixedSize(180, 30)  # Set the size for the back button

        back_icon = QIcon("output-onlinepngtools copy 2.png")
        back_button.setIcon(back_icon)
        back_button.setIconSize(QSize(24, 24))  # Adjust icon size if needed
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #94127e; 
                color: #FFFFFF;
                font-weight: bold; 
                font-size: 14px;
                border-radius: 1px; 
                padding: 5px;
                min-height: 20px;
                width: 180px;
            }
            QPushButton:hover {
                background-color: #b0529c;  /* Change to a lighter shade or different color */
                color: #FFFFFF;  /* Keep text color white */
            }
        """)
        back_button.clicked.connect(self.show_main_page)  # Ensure show_main_page is defined to handle the navigation
        preview_layout.addWidget(back_button, alignment=Qt.AlignLeft)

        # Add QLabel at the top
        label = QLabel("Preview of Loaded Data & Optinal Json File Load")
        label.setAlignment(Qt.AlignLeft)  # Center the label text
        label.setFixedHeight(30)  # Set a fixed height for the label
        label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0px; margin: 0px;")  # No padding or margins
        preview_layout.addWidget(label)

        # Create a horizontal layout for the table and frame
        table_frame_layout = QHBoxLayout()

        # Initialize and add the preview table to the layout
        self.preview_table = QTableView()
        self.preview_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_table.setStyleSheet("margin-top: 5px; margin-bottom: 0px;")  # Set margin for the table
        table_frame_layout.addWidget(self.preview_table)

        # Create an empty QFrame with the same dimensions as the preview table
        self.empty_frame = QFrame()
        self.empty_frame.setStyleSheet("background-color: #121212; border: 0.2px solid #FFFFFF;")  # Background color and border
        self.empty_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.empty_frame.setMaximumWidth(1000)
        self.empty_frame.setMinimumWidth(100)  # Adjust as needed
        self.empty_frame.setMaximumHeight(300)  # Set the same height as the table

        # Create a vertical layout for the empty frame
        empty_frame_layout = QVBoxLayout(self.empty_frame)

        # Create the inner frame that will act as a rectangular bar
        self.inner_frame = QFrame()
        self.inner_frame.setStyleSheet("background-color: #3E3E3E;border: 0.2px solid #FFFFFF;")  # Optional: set a different background color for the bar
        self.inner_frame.setFixedHeight(60)  # Set a fixed height for the inner frame
        self.inner_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Keep expanding width but allow flexible height

        # Add the inner frame to the layout of the empty frame
        empty_frame_layout.addWidget(self.inner_frame)  # Add the inner frame at the top

        # Create a QLabel for displaying metadata output
        self.metadata_output_label = QLabel("")  # Initialize the label with empty text
        self.metadata_output_label.setStyleSheet("color: #FFFFFF; padding: 5px; 0.2px solid #FFFFFF; border: none;")  # Set the style for the label
        empty_frame_layout.addWidget(self.metadata_output_label)  # Add the label to the empty frame layout

        # Ensure that the empty frame's layout also expands the table to fill the rest of the space
        empty_frame_layout.addStretch()  # This will push the rest of the empty frame content down

        # Add the empty frame to the main horizontal layout
        table_frame_layout.addWidget(self.empty_frame)

        # Add the horizontal layout to the main preview layout
        preview_layout.addLayout(table_frame_layout)

        # Add additional widgets like buttons through a separate method
        self.add_preview_page_widgets(preview_layout)


        # Add the complete preview page to the stacked widget
        self.stacked_widget.addWidget(self.preview_page)

    def add_preview_page_widgets(self, layout):
        """
        Add preview page widgets to the specified layout.

        This method creates and adds various widgets to the given layout, including:
        - A horizontal layout of buttons for rounding values, adding noise, reverting data, and combining values.
        - A 'Graph Categorical' button to display graphs for categorical data.
        - A label for metadata display and a dropdown for selecting columns.
        - A 'Load JSON Metadata' button for loading and displaying metadata.

        Parameters:
        -----------
        layout : QVBoxLayout
            The layout to which the widgets will be added.
        """

        button_layout = QHBoxLayout()

        button_data = [
            ('Round Continuous Values', '94127e', self.round_values),
            ('Add Laplacian Noise', '94127e', lambda: self.add_noise('laplacian')),
            ('Add Gaussian Noise', '94127e', lambda: self.add_noise('gaussian')),
            ('Combine Values', '94127e', self.show_combine_values_dialog),
            ('Revert to Original', '94127e', self.revert_to_original),  # Add Combine Values button
        ]

        for text, color, func in button_data:
            button = QPushButton(text)

            # Define normal and hover styles
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #{color}; 
                    color: #FFFFFF;
                    font-weight: bold; 
                    font-size: 14px;
                    border-radius: 1px; 
                    padding: 5px;
                    min-height: 20px;
                    width: 180px;      /* Set a fixed width */
                }}
                QPushButton:hover {{
                    background-color: #b0529c;  /* Change to a lighter shade or different color */
                    color: #FFFFFF;  /* You can also change the text color on hover */
                }}
            """)
            
            button.clicked.connect(func)
            button_layout.addWidget(button)

            if text == 'Revert to Original':
                revert_icon = QIcon("output-onlinepngtools-5.png")  # Replace with your icon file path
                button.setIcon(revert_icon)
                button.setIconSize(QSize(24, 24))  # Adjust icon size if needed
                button.setLayoutDirection(Qt.RightToLeft)

        self.graph_button = QPushButton('Graph Display')

        graph_icon = QIcon("output-onlinepngtools-5 copy.png")
        self.graph_button.setIcon(graph_icon)
        self.graph_button.setIconSize(QSize(24, 24))  # Adjust icon size as needed
        self.graph_button.setLayoutDirection(Qt.RightToLeft)
        self.graph_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #{color}; 
                    color: #FFFFFF;
                    font-weight: bold; 
                    font-size: 14px;
                    border-radius: 1px; 
                    padding: 5px;
                    min-height: 20px;
                    width: 180px;      /* Set a fixed width */
                }}
                QPushButton:hover {{
                    background-color: #b0529c;  /* Change to a lighter shade or different color */
                    color: #FFFFFF;  /* You can also change the text color on hover */
                }}
            """)
        self.graph_button.clicked.connect(self.show_graph_categorical_dialog)
        button_layout.addWidget(self.graph_button)

        # Create a new layout for the inner frame to hold the Load Metadata button and dropdown
        inner_frame_layout = QVBoxLayout(self.inner_frame)  # Assuming self.inner_frame is defined in setupPreviewPage

        layout.addLayout(button_layout)

        self.metadata_display = QLabel('')
        self.metadata_display.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.metadata_display)

        # Create a horizontal layout inside the inner frame for button and dropdown
        dropdown_button_layout = QHBoxLayout()

        self.column_dropdown = QComboBox()
        self.column_dropdown.addItem("Select Column")
        self.column_dropdown.currentIndexChanged.connect(self.show_metadata_for_column)
        self.column_dropdown.setStyleSheet("""
            QComboBox {
                border: 2px solid #FFFFFF;
                border-radius: 5px;
                padding: 2px 2px;
                background-color: #121212;
                color: #FFFFFF;
            }
            QComboBox::drop-down {
                border-left: 2px solid #FFFFFF;
            }
        """)
        
        # Add the dropdown and button to the horizontal layout
        dropdown_button_layout.addWidget(self.column_dropdown)
        
        # Move the Load JSON Metadata button to the inner frame's layout
        self.load_metadata_button = QPushButton('Load JSON Metadata')

        metadata_icon = QIcon("output-onlinepngtools.png")
        self.load_metadata_button.setIcon(metadata_icon)
        self.load_metadata_button.setIconSize(QSize(24, 24))  # Adjust icon size as needed


        self.load_metadata_button.setStyleSheet("""
            QPushButton {
                background-color: #94127e; 
                color: #FFFFFF; 
                font-weight: bold; 
                font-size: 13px; 
                border-radius: 5px; 
                padding: 30px 20px; /* Increase padding for more height */
                min-width: 200px; /* Set a minimum width for the button */
            }
            QPushButton:hover {
                background-color: #b0529c;  /* Change to a lighter shade or different color */
                color: #FFFFFF;  /* You can also change the text color on hover */
            }
        """)

        #self.load_metadata_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Allow button to expand
        self.load_metadata_button.clicked.connect(self.load_metadata)
        dropdown_button_layout.addWidget(self.load_metadata_button)  # Add to the horizontal layout

        # Add the horizontal layout to the inner frame
        inner_frame_layout.addLayout(dropdown_button_layout)  # Add the button and dropdown layout to inner frame

        # No need to add metadata_layout, remove that line

    def show_preview(self):
        """
        Displays the first 10 rows of the loaded dataset in a preview table.

        Raises:
        -------
        QMessageBox
            If no data is loaded.

        Example:
        --------
        Shows the first 10 rows of the dataset with column headers in a table view.

        Notes:
        ------
        - Table height is set to a maximum of 200 pixels.
        - Dropdown menu for columns is updated accordingly.
        """
        if self.data is not None:
            preview_data = self.data.head(10)
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(preview_data.columns)
            for row in preview_data.itertuples(index=False):
                items = [NumericStandardItem(str(item)) if isinstance(item, (int, float)) else QStandardItem(str(item)) for item in row]
                model.appendRow(items)
            
            self.preview_table.setModel(model)
            self.preview_table.setMaximumHeight(300)
            self.preview_table.setMaximumWidth(700)
            self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
            self.preview_table.horizontalScrollBar().setVisible(True)
            self.update_column_dropdown()
            self.stacked_widget.setCurrentWidget(self.preview_page)


        else:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")








    def show_privacy_info(self):
        self.stacked_widget.setCurrentWidget(self.privacy_info_page)

    def show_suda_info(self):
        self.stacked_widget.setCurrentWidget(self.suda_info_page)




    def add_buttons(self, layout):
        """
        Add a row of buttons to the specified layout.

        This method creates a horizontal layout containing a set of buttons, each
        associated with a specific functionality of the application. It then adds
        this horizontal layout to the provided `layout`. Each button is styled with
        a unique background color and connected to its corresponding event handler.

        Args:
            layout (QVBoxLayout): The layout to which the buttons will be added.
        
        Buttons:
            - "Load CSV/TSV File": Opens a dialog to load a CSV/TSV file.
            - "Privacy Calculation": Calculates unique rows for privacy analysis.
            - "Variable Optimization": Finds the lowest unique columns for optimization.
            - "Preview Data": Shows a preview of the loaded data.
            - "Compute SUDA": Computes SUDA (Statistical Disclosure Control).
            - "Privacy Information Factor": Displays privacy information.
        """

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        buttons = [
            ("Load CSV/TSV File", self.load_file, "#94127e"),
            ("Preview Data", self.show_preview, "#94127e"),
            ("Privacy Calculation", self.calculate_unique_rows, "#94127e"),
            ("Variable Optimization", self.find_lowest_unique_columns, "#94127e"),
            #("Compute SUDA", self.compute_suda, "#94127e"),
            ("Privacy Information Factor", self.show_privacy_info, "#94127e"),
            ("SUDA", self.show_suda_info, "#94127e"),
        ]

        # Load the icon for the "Load CSV/TSV File" button
        csv_icon = QIcon("output-onlinepngtools.png")  # Make sure to provide the correct path to your PNG file
        preview_icon = QIcon("output-onlinepngtools-2.png")

        for text, slot, color in buttons:
            btn = QPushButton(text)
            
            # Set common styling for all buttons
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}; 
                    color: white;  /* Change text color to white */
                    font-family: 'Roboto'; /* Set font family */
                    font-weight: bold; 
                    font-size: 14px;
                    border-radius: 1px; 
                    padding: 5px;
                    min-height: 20px;
                    width: 180px;      /* Set a fixed width */
                }}
                QPushButton:pressed {{
                    background-color: #808080; /* Change color when pressed */
                    border-radius: 8px; /* Optional: slightly decrease border radius */
                }}
                QPushButton:hover {{
                    background-color: #b0529c; /* Change to a matte or darker color on hover */
                    color: white; /* Keep text color white */
                }}
            """)

            # Set icon for "Load CSV/TSV File" button on both sides
            if text == "Load CSV/TSV File":
                btn.setIcon(csv_icon)
                btn.setIconSize(QSize(24, 24))  # Adjust icon size if needed
                btn.setStyleSheet(btn.styleSheet() + "QPushButton::icon { margin-right: 10px; margin-left: 10px; }")


            if text == "Preview Data":
                btn.setIcon(preview_icon)
                btn.setIconSize(QSize(24, 24))  # Adjust icon size if needed
                btn.setStyleSheet(btn.styleSheet() + "QPushButton::icon { margin-right: 10px; margin-left: 10px; }")


            btn.clicked.connect(slot)
            button_layout.addWidget(btn)


    def show_graph_categorical_dialog(self):

        """
        Opens a dialog to select and graph a categorical column from the loaded dataset.
    
        Steps:
        1. Checks if data is loaded.
        2. Retrieves the categorical columns from the dataset.
        3. Opens a dialog for the user to select a categorical column.
        4. Plots a tree graph for the selected column using combined values, if available.
        
        Raises:
        -------
            QMessageBox.Warning: If no data is loaded or no categorical columns are available.

        Parameters:
        -----------
            Column

        Returns:
        -------- 
            Visual display of graph

        """

        if self.data is not None:
            # Get categorical columns
            categorical_columns = self.get_categorical_columns()

            if not categorical_columns:
                QMessageBox.warning(self, "No Categorical Columns", "No categorical columns available for graphing.")
                return

            column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to graph:", categorical_columns, 0, False)

            if ok and column_name:
                self.plot_tree_graph(column_name)  # Plot with the updated combined values
        else:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")


    def plot_tree_graph(self, column_name):

        """
        Plots a tree graph representing the relationships between the unique values of a selected 
        categorical column, including combined values if applicable.

        This method constructs a directed graph (DiGraph) using NetworkX to represent the hierarchy 
        of values within the specified column. If there are combined values in the column 
        (based on the `combined_values_history`), they are included in the graph, showing how individual 
        values are combined into a replacement node. The graph is visualized using Matplotlib.

        Workflow:
        1. Creates a directed graph ('DiGraph') with the column name as the root node.
        2. Adds nodes and edges for combined values from 'combined_values_history'.
        3. Adds nodes and edges for unique values in the selected column.
        4. Removes edges related to combined values to prevent overlap.
        5. Uses Graphviz layout for proper positioning of nodes.
        6. Draws and displays the graph using Matplotlib and NetworkX.

        Parameters:
        -----------
        column_name : str
            The name of the categorical column from the dataset to plot.

        Notes:
        ------
        - The graph will include nodes for individual values, and if any values were combined 
          into a single entity, the relationship will be reflected in the graph.
        - Uses Graphviz for positioning (`prog='dot'`) to ensure a hierarchical tree layout.


        Returns:
        --------
        nx.drawing.nx_agraph
        """      
        G = nx.DiGraph()
        G.clear()
        G.add_node(column_name)

        replacement_node = None

        nodes_to_add = set()
        edges_to_add = set()

        combined_values_set = set()

        if column_name in self.combined_values_history:
            for combined_values, replacement_value in self.combined_values_history[column_name]:
      
                replacement_node = replacement_value
                nodes_to_add.add(replacement_node)
                edges_to_add.add((column_name, replacement_node))  

                for value in combined_values:
                    if pd.notna(value):
                        nodes_to_add.add(value)
                        edges_to_add.add((replacement_node, value))
                        combined_values_set.add(value)  

        unique_values = self.data[column_name].unique()
        for value in unique_values:
            if pd.notna(value) and value not in combined_values_set:
                nodes_to_add.add(value)
                edges_to_add.add((column_name, value)) 

        G.add_nodes_from(nodes_to_add)
        G.add_edges_from(edges_to_add)

        print("Initial Nodes:", G.nodes())
        print("Initial Edges:", G.edges())

        for node in G.successors(column_name):
            if node in combined_values_set:
                G.remove_edge(column_name, node)

        print("Nodes after cleanup:", G.nodes())
        print("Edges after cleanup:", G.edges())
        pos = nx.drawing.nx_agraph.graphviz_layout(G, prog='dot')

      
        plt.figure(figsize=(12, 8))
        nx.draw(G, pos, with_labels=True, node_size=1000, node_color='white', font_size=6, font_weight='normal', edge_color='black')

        plt.title(f'Tree Graph of Values in Column \"{column_name}\"', fontsize=12)
        plt.show()


    def show_combine_values_dialog(self):
        """
        Displays a dialog allowing the user to select and combine unique values from a specified 
        categorical column in the dataset.

        This method first checks if the dataset is loaded and then retrieves the categorical columns 
        from the dataset. It allows the user to select a column from which to combine unique values. 
        If the selected column has fewer than two unique values, a warning is shown. Otherwise, a dialog 
        is presented where the user can select multiple unique values to combine. The user can then confirm 
        the selection by clicking a button, which triggers the combination of selected values.

        Workflow:
        1. Checks if the dataset is loaded.
        2. Retrieves the categorical columns from the dataset.
        3. Opens a dialog for the user to select a categorical column.
        4. Checks if the selected column has at least two unique values.
        5. Opens another dialog to select and combine unique values from the column.
        6. Applies styling to the dialog and its components for better visibility and usability.


        Notes:
        ------
        - The method uses a 'QDialog' to allow the user to select values to combine.
        - If no categorical columns are available or if the dataset is not loaded, appropriate warnings are shown.

        Raises:
        -------
        QMessageBox.Warning: If no data is loaded, no categorical columns are available, or not enough unique values are present.

        Returns:
        --------
        QDialog Window
        """

        if self.data is not None:
         
            categorical_columns = self.get_categorical_columns()

            if not categorical_columns:
                QMessageBox.warning(self, "No Categorical Columns", "No categorical columns available for combining values.")
                return

            column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to combine values:", categorical_columns, 0, False)

            if ok and column_name:
                unique_values = self.data[column_name].unique()
                unique_values = [val for val in unique_values if pd.notna(val)] 

                if len(unique_values) < 2:
                    QMessageBox.warning(self, "Not Enough Values", "The selected column does not have enough unique values to combine.")
                    return

               
                unique_values = list(map(str, unique_values))

               
                dialog = QDialog(self)
                dialog.setWindowTitle("Select Values to Combine")
                dialog.setStyleSheet("background-color: #121212; color: #FFFFFF;")  
                layout = QVBoxLayout(dialog)

                list_widget = QListWidget(dialog)
                list_widget.setSelectionMode(QListWidget.MultiSelection)
                list_widget.addItems(unique_values)

             
                list_widget.setStyleSheet("""
                    QListWidget {
                        background-color: #2E2E2E;  /* Dark background */
                        color: #FFFFFF;  /* White text */
                    }
                    QListWidget::item {
                        border: 1px solid #444444;  /* Border to make items stand out */
                    }
                    QListWidget::item:selected {
                        background-color: #4CAF50;  /* Highlighted item background */
                        color: #FFFFFF;  /* White text for selected item */
                    }
                """)
                layout.addWidget(list_widget)

                combine_button = QPushButton("Combine", dialog)
                combine_button.setStyleSheet("background-color: #4CAF50; color: #FFFFFF;")
                combine_button.clicked.connect(lambda: self.combine_selected_values(column_name, list_widget.selectedItems()))
                layout.addWidget(combine_button)

                dialog.setLayout(layout)
                dialog.resize(400, 300)
                dialog.exec()  # Use exec() for QDialog
        else:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")


    def combine_selected_values(self, column_name, selected_items):
        """
        Combines selected values in a specified column with a new replacement value.

        This method allows the user to combine multiple selected values in a given categorical column 
        into a single replacement value. It performs the following actions:
        1. Validates that at least two values are selected for combination.
        2. Checks if the column's original values are stored; if not, stores them.
        3. Prompts the user to enter a replacement value for the selected items.
        4. Updates the dataset by replacing the selected values with the new replacement value.
        5. Records the combination in the history for potential future reference.
        6. Refreshes the preview to reflect the changes.

        Parameters:
        -----------
        column_name : str
            The name of the column where values are to be combined.

        selected_items : list of QListWidgetItem
            The list of selected items from the dialog containing the values to be combined.

        Notes:
        ------
        - The method requires that at least two values are selected for combining. If fewer than two 
          values are selected, a warning is shown.
        - The original values of the column are stored to allow for potential future reference or undo operations.
        - The method updates both the 'combined_values_history' and the dataset with the new combination.

        Raises:
        -------
        QMessageBox.Warning: If fewer than two values are selected or if the user does not provide a replacement value.

        Returns:
        --------
        QMessageBox
    """

        selected_values = [item.text() for item in selected_items]
        if len(selected_values) < 2:
            QMessageBox.warning(self, "Insufficient Selection", "Please select at least two values to combine.")
            return
        if column_name not in self.original_columns:
            self.original_columns[column_name] = self.data[column_name].copy()
        replacement_value, ok = QInputDialog.getText(self, "Combine Values", "Enter the new value for the selected items:")
        
        if ok and replacement_value:  # Check if the user clicked OK and provided a value
           
            selected_values = list(map(str, selected_values))
            replacement_value = str(replacement_value)
            
            
            if column_name not in self.combined_values_history:
                self.combined_values_history[column_name] = []
            self.combined_values_history[column_name].append((selected_values, replacement_value))
            self.data[column_name] = self.data[column_name].astype(str)
            self.data[column_name] = self.data[column_name].replace(selected_values, replacement_value)
 
            self.show_preview() 

            QMessageBox.information(self, "Success", "Values have been successfully combined.")



    def describe_cig(self):
        """
        Generates and displays a statistical description of the CIG (Categorical Information Gain) DataFrame.
        """
        if hasattr(self, 'cigs_df') and not self.cigs_df.empty:
            # Drop the 'RIG' column if it exists
            if 'RIG' in self.cigs_df.columns:
                cigs_df_for_description = self.cigs_df.drop(columns=['RIG'])
            else:
                cigs_df_for_description = self.cigs_df
            
            # Compute descriptive statistics
            description = cigs_df_for_description.describe()  # This includes mean, std, etc.
            description = description.drop('count', axis=0)

            # Transpose to have statistics as rows
            description = description.T  

            # Format to two decimal places
            description = description.applymap(lambda x: f"{x:.2f}")

            # Clear previous QTableWidget if it exists
            if hasattr(self, 'cig_description_table'):
                self.cig_description_frame.layout().removeWidget(self.cig_description_table)  # Remove previous QTableWidget
                self.cig_description_table.deleteLater()  # Delete the widget to free up memory

            # Create a new QTableWidget for displaying the description
            self.cig_description_table = QTableWidget(self.cig_description_frame)  
            self.cig_description_table.setRowCount(len(description))  # Set the number of rows
            self.cig_description_table.setColumnCount(len(description.columns) + 1)  # +1 for index names

            # Set header labels, including the index label for statistics and original column names
            self.cig_description_table.setHorizontalHeaderLabels(['Statistic'] + description.columns.tolist())

            # Populate the QTableWidget with data from the descriptive statistics
            for row in range(len(description)):
                # Set the index name (statistic) in the first column
                self.cig_description_table.setItem(row, 0, QTableWidgetItem(description.index[row]))  # Set index name
                for col in range(len(description.columns)):
                    value = description.iat[row, col]  # Get the value
                    item = QTableWidgetItem(str(value))  # Create a QTableWidgetItem
                    self.cig_description_table.setItem(row, col + 1, item)  # Add item to the table (offset by 1)

            # Highlight the largest numbers in the mean column
            self.highlight_highest_mean_value()

            # Set the style of the QTableWidget
            self.cig_description_table.setStyleSheet("""
                QTableWidget {
                    background-color: #121212; 
                    color: white;
                }
                QHeaderView::section {
                    background-color: #121212;  /* Set header background to dark grey */
                    color: white;  /* Set header text color to white */
                    font-weight: bold;  /* Make header text bold */
                }
            """)

            # Make the columns stretch to fit the width of the table
            self.cig_description_table.horizontalHeader().setStretchLastSection(True)  # Allow the last section to stretch
            self.cig_description_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Stretch all columns

            # Check if a scroll area already exists, if so, remove it
            if hasattr(self, 'cig_description_scroll_area'):
                self.cig_description_frame.layout().removeWidget(self.cig_description_scroll_area)
                self.cig_description_scroll_area.deleteLater()

            # Create a scroll area for the QTableWidget
            self.cig_description_scroll_area = QScrollArea(self.cig_description_frame)
            self.cig_description_scroll_area.setWidgetResizable(True)
            self.cig_description_scroll_area.setWidget(self.cig_description_table)  # Set the QTableWidget as the widget of the scroll area

            # Ensure the layout is initialized
            if self.cig_description_frame.layout() is None:
                self.cig_description_frame.setLayout(QVBoxLayout())  # Initialize the layout if not already done

            # Clear any existing layout and add the scroll area
            layout = self.cig_description_frame.layout()
            layout.addWidget(self.cig_description_scroll_area)  # Add the scroll area to the description frame

        else:
            self.cig_description_label.setText("Please compute CIG before summary statistics.")  # Inform user



    def highlight_highest_mean_value(self):
        """
        Highlights the largest values in the 'mean' column of the QTableWidget.
        """
        # Find the index of the 'mean' column by checking the header labels
        mean_col_index = -1
        for index in range(self.cig_description_table.columnCount()):
            if self.cig_description_table.horizontalHeaderItem(index).text() == 'mean':
                mean_col_index = index
                break

        # Ensure the 'mean' column was found
        if mean_col_index == -1:
            print("Mean column not found.")
            return  # Exit if the mean column is not found

        # Get the maximum value from the 'mean' column
        max_mean_value = float('-inf')

        # First pass: find the maximum mean value
        for row in range(self.cig_description_table.rowCount()):
            mean_value = float(self.cig_description_table.item(row, mean_col_index).text())
            if mean_value > max_mean_value:
                max_mean_value = mean_value

        # Second pass: highlight cells that match the maximum mean value
        for row in range(self.cig_description_table.rowCount()):
            mean_value = float(self.cig_description_table.item(row, mean_col_index).text())
            if mean_value == max_mean_value:
                item = self.cig_description_table.item(row, mean_col_index)
                item.setForeground(QBrush(QColor("red")))  # Set text color to red
                item.setFont(QFont("Arial", 14, QFont.Bold))  # Set font to bold



    def generate_heatmap(self):
        """
        Generates and displays a heatmap of the CIG (Categorical Information Gain) DataFrame.

        This method performs the following actions:
        1. Checks if the 'cigs_df' attribute exists and is not empty.
        2. Excludes the 'RIG' column from the DataFrame for heatmap generation.
        3. Creates a heatmap using seaborn with a custom color map and saves it as an image file ('heatmap.png').
        4. Displays the generated heatmap image in the user interface.
        5. Ensures that the heatmap label and close button are visible.

        If the 'cigs_df' attribute is not present or is empty, the method displays a message in 
        'cig_result_browser' prompting the user to compute CIG before generating the heatmap.


        Notes:
        ------
        - The heatmap is saved as 'heatmap.png' in the current working directory.
        - The method checks for and manages the presence of 'heatmap_label' to display the heatmap 
          and ensures the 'close_heatmap_button' is visible.

        Raises:
        -------
        Missing CIG computation: "Please compute CIG before generating the heatmap."

        Returns:
        --------
        Matplotlib plot (Heatmap)
        """

        if hasattr(self, 'cigs_df') and not self.cigs_df.empty:
            cigs_df_no_rig = self.cigs_df.drop(columns=['RIG'])
            color_map = sns.color_palette("RdYlGn", 256)

            # Create a new figure and show the heatmap in a standalone window
            plt.figure(figsize=(10, 8))  # Adjust the figure size as needed
            ax = sns.heatmap(cigs_df_no_rig, cmap=color_map, annot=False, fmt="g", cbar=True)
            plt.title("CIG Heatmap")

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right', fontsize=10)  # Rotate 45 degrees, right-align
            plt.yticks(fontsize=10)  # Adjust font size for y-axis labels

            plt.yticks(fontsize=6)

            # Automatically adjust the layout to fit the labels
            plt.tight_layout()

            # Display the heatmap in a separate Matplotlib window
            plt.show()

        else:
            self.cig_result_browser.setPlainText("Please compute CIG before generating the heatmap.")

      

    def compute_combined_column_contribution(self):
        """
        Computes and evaluates the contribution of various column combinations to unique row counts in the dataset.

        This method performs the following steps:
        1. Checks if data is loaded; if not, it displays a warning.
        2. Prompts the user to input minimum and maximum combination sizes for column combinations.
        3. Iterates over all column combinations of sizes ranging from 'min_size' to 'max_size'.
        4. For each combination:
        - Calculates the number of unique rows (rows with unique values) in the dataset for the selected columns.
        - Calculates the number of unique rows excluding the selected columns.
        - Stores the combination, the number of unique rows, and the number of unique rows excluding columns.
        5. Computes a score for each combination based on the total unique rows and the unique rows excluding columns.
        6. Displays the results in a Qdialog.

        Notes:
        ------
        - The results include the combination of columns, the count of unique rows, and a score based on the contribution to unique row counts.
        - The 'show_results_dialog' method is used to display the results to the user.

        Raises:
        -------
        QMessageBox: If no data is loaded or no columns are selected.

        Returns:
        --------
        Combined Column Contribution calculation.
        """

        if self.data is None:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")
            return
        
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            QMessageBox.warning(self, "Warning", "Please select at least one column.")
            return

        min_size, ok_min = QInputDialog.getInt(self, "Select Minimum Combination Size", "Enter minimum combination size:", 3, 1, len(selected_columns))
        if not ok_min:
            return  # User canceled the input dialog
        
        max_size, ok_max = QInputDialog.getInt(self, "Select Maximum Combination Size", "Enter maximum combination size:", 7, min_size, len(selected_columns))
        if not ok_max:
            return  # User canceled the input dialog
        
        results = []
        total_unique_rows = None

        for r in range(min_size, max_size + 1):  # Adjust based on user input
            print(f"Processing combinations of size {r}...")
            
            all_combinations = combinations(selected_columns, r)
            
            for comb in all_combinations:
                selected_cols = list(comb)
                value_counts = self.data[selected_cols].value_counts()
                num_unique_rows = len(value_counts[value_counts == 1])
                        
                remaining_columns = [col for col in selected_columns if col not in selected_cols]
                
       
                if remaining_columns:
                    value_counts_excluded = self.data[remaining_columns].value_counts()
                    num_excluded_unique_rows = len(value_counts_excluded[value_counts_excluded == 1])
                else:
                    num_excluded_unique_rows = 0  # If no remaining columns, set to 0
                
            
                results.append({
                    'Combination': ', '.join(selected_cols),
                    'Unique Rows': num_unique_rows,
                    'Unique Rows Excluding Columns': num_excluded_unique_rows
                })
        
      
        all_combinations_df = pd.DataFrame(results)
        
      
        if total_unique_rows is None:
            total_value_counts = self.data[selected_columns].value_counts()
            total_unique_rows = len(total_value_counts[total_value_counts == 1])
        
    
        all_combinations_df['Score'] = (total_unique_rows - all_combinations_df['Unique Rows Excluding Columns']) / all_combinations_df['Unique Rows']
        
  
        self.show_results_dialog(all_combinations_df)



    def show_results_dialog(self, results_df, result_type="combined", mad_value=None):
        """
        Display a dialog with calculation results in a table format.

        Shows the results of Combined Column Contributions or SUDA calculations in a modal dialog. 
        The dialog includes an optional Median Absolute Deviation (MAD) value and allows saving the results as a CSV file.

        Parameters:
        -----------
        results_df : pandas.DataFrame
        result_type : str, optional
        Type of results ("combined" or "suda") for setting the dialog title and default filename.
        mad_value : float.

        Returns:
        --------
        QMessageBox / QDialog. 

        Raises:
        -------
        FileNotFoundError
        If the file path for saving the CSV is invalid.

        Exception:
        ----------
        For unexpected errors during the save process.
        """

        dialog = QDialog(self)

        if result_type == "suda":
            dialog.setWindowTitle("SUDA Calculation Results")
        else:
            dialog.setWindowTitle("Combined Column Contribution Results")

        dialog.setStyleSheet("background-color: #121212; color: #FFFFFF;")
        layout = QVBoxLayout(dialog)

        if mad_value is not None:
            mad_label = QLabel(f"Median Absolute Deviation (MAD): {mad_value}")
            mad_label.setStyleSheet("font-size: 14px; color: #FFFFFF;")
            layout.addWidget(mad_label)

    
        results_table = QTableView()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(results_df.columns)

    
        for row in results_df.itertuples(index=False):
            items = [QStandardItem(str(item)) for item in row]
            model.appendRow(items)

        results_table.setModel(model)

        results_table.setSortingEnabled(True)  # Enable sorting of columns
        results_table.resizeColumnsToContents()  # Auto resize columns to fit content

        layout.addWidget(results_table)

        save_button = QPushButton("Save as CSV")
        save_button.setStyleSheet("background-color: #4CAF50; color: #FFFFFF;")
        layout.addWidget(save_button)




        def save_as_csv():
            """
            Save the displayed results as a CSV file.

            Opens a file dialog to specify the save location and filename. The default
            filename is set based on the result type: "sudaresult" or "combinedresult",
            appended with a timestamp. Saves the DataFrame as a CSV file at the specified
            location and displays a success message upon completion.

            Returns:
            --------
            str
                The file path where the CSV file was saved, or None if the save was canceled.
            """
      
            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
       
            if result_type == "suda":
                default_filename = f"sudaresult_{timestamp}.csv"
            else:
                default_filename = f"combinedresult_{timestamp}.csv"

            file_path, _ = QFileDialog.getSaveFileName(dialog, "Save as CSV", default_filename, "CSV Files (*.csv)")

            if file_path:
                results_df.to_csv(file_path, index=False)
                QMessageBox.information(dialog, "Success", f"File saved as {file_path}")

      
        save_button.clicked.connect(save_as_csv)

        dialog.resize(800, 600)
        dialog.exec()




    def update_value_list(self):
        """
        Update the column selection dropdown with the current data's columns.

        Clears the existing items in the column combobox and repopulates it with
        the columns from the loaded dataset. If no data is loaded, only the default 
        "Select Column" option is available.
        """

        self.column_combobox.clear()
        self.column_combobox.addItem("Select Column")

        if self.data is not None:
            for column in self.data.columns:
                self.column_combobox.addItem(column)



    def get_categorical_columns(self):
        """
        Retrieve a list of categorical columns from the model.

        Iterates through the rows of `columns_model` to find columns marked as "Categorical".
        Returns a list of the names of these columns.

        Returns:
        --------
        list of str
            A list containing the names of columns identified as categorical.
        """

        return [self.columns_model.item(row, 0).text() for row in range(self.columns_model.rowCount())
                if self.columns_model.item(row, 2).text() == "Categorical"]




    def add_frames(self, layout):

        """
        Add frames to the provided layout for displaying various sections of the UI.

        This method creates two frames ('load_results_frame' and 'variable_optimization_frame') 
        and adds them to the specified layout. Both frames are styled with a white border. 
        It then calls methods to populate these frames with their respective layouts. 
        Additionally, a 'QLabel' ('result_label') is created and added to the layout 
        for displaying result messages.

        Parameters:
        -----------
        layout : QVBoxLayout
            The layout to which the frames and the result label will be added.

        Returns:
        --------
        QWidget
        """

        self.load_results_frame, self.variable_optimization_frame = QFrame(), QFrame()
        for frame in (self.load_results_frame, self.variable_optimization_frame):
            frame.setStyleSheet("border: 0.5px solid #FFFFFF;")
            layout.addWidget(frame)
        self.add_load_results_layout()
        self.add_variable_optimization_layout()
        self.result_label = QLabel('')
        self.result_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.result_label)




    def add_load_results_layout(self):

        """
        Add a layout to the 'load_results_frame' for managing column selection and configuration.

        This method sets up a vertical layout within 'load_results_frame'. It creates a 'QTreeView' to 
        display columns with various attributes such as unique values and types. The tree view uses a 
        'QStandardItemModel' to manage the data, with headers: "Select Columns", "Unique Value", "Type", 
        and "Select Sensitive Attribute". A custom 'ComboBoxDelegate' is set for the "Type" column to 
        allow users to select a data type from a dropdown. The 'setup_treeview' method is called to 
        configure the tree view, and the view is added to the layout.

        Returns:
        --------
        QWidget
        """
        load_results_layout = QVBoxLayout(self.load_results_frame)
        self.columns_view = QTreeView()
        self.columns_model = QStandardItemModel()
        self.columns_model.setHorizontalHeaderLabels(["Select Columns", "Unique Value", "Type", "Select Sensitive Attribute"])
        self.columns_view.setModel(self.columns_model)


        self.type_delegate = ComboBoxDelegate(self.columns_view)
        self.columns_view.setItemDelegateForColumn(2, self.type_delegate)

        self.setup_treeview(self.columns_view)
        load_results_layout.addWidget(self.columns_view)



    def add_variable_optimization_layout(self):

        """
        Add a layout to the `variable_optimization_frame` for displaying variable optimization results.

        This method sets up a vertical layout within `variable_optimization_frame`. It creates a `QTreeView`
        (`results_view`) to display the variable optimization results using a `QStandardItemModel`. 
        The model's headers are set to "Quasi Identifiers", "Unique Rows After Removal", "Difference", 
        and "Normalized". The tree view is configured using `setup_treeview` and added to the layout.

        Returns:
        --------
        QVBoxLayout
            The layout containing the `QTreeView` for variable optimization results.
        """
        variable_optimization_layout = QVBoxLayout(self.variable_optimization_frame)
        self.results_view = QTreeView()
        self.results_model = QStandardItemModel()
        self.results_model.setHorizontalHeaderLabels(["Quasi Identifiers", "Unique Rows After Removal", "Difference", "Normalized"])
        self.results_view.setModel(self.results_model)
        self.setup_treeview(self.results_view)
        variable_optimization_layout.addWidget(self.results_view)


    def create_noise_menu(self):
        """
        Create a noise menu with options to add Laplacian or Gaussian noise.

        This method creates a QMenu with actions for adding Laplacian and Gaussian noise 
        to the data. Each action is connected to the `add_noise` method with the respective 
        noise type as a parameter.

        Returns:
        --------
        QMenu:
            The menu containing noise addition actions.
        """
        noise_menu = QMenu()
        laplacian_action = QAction('Add Laplacian Noise', self)
        laplacian_action.triggered.connect(lambda: self.add_noise('laplacian'))
        noise_menu.addAction(laplacian_action)
        gaussian_action = QAction('Add Gaussian Noise', self)
        gaussian_action.triggered.connect(lambda: self.add_noise('gaussian'))
        noise_menu.addAction(gaussian_action)
        return noise_menu


    def add_noise(self, noise_type):
        """
        Adds noise to a selected continuous column in the data.

        This method allows the user to select a continuous column from which noise will be added based on the specified noise type. The available noise types are Laplacian and Gaussian. The original column data is preserved before applying the noise.

        Parameters:
        -----------
        noise_type : str
            The type of noise to add. Options are:

            - 'laplacian': Adds Laplacian noise.
            - 'gaussian': Adds Gaussian noise.

        Raises:
        -------
        ValueError
            If an invalid 'noise_type' is provided.

        Notes:
        ------
        - The method first checks if there are any continuous columns available. If not, a warning is shown.
        - The user is prompted to select a column to which the noise will be added.
        - The method preserves the original data of the selected column before modifying it with the specified noise.
        - The 'show_preview' function is called after adding the noise to update any relevant displays.

        Returns:
        --------
        
        Continous Column with noise. 
        """


        print(f"Add noise triggered with type: {noise_type}") 
        continuous_columns = [self.columns_model.item(row, 0).text() for row in range(self.columns_model.rowCount())
                              if self.columns_model.item(row, 2).text() == "Continuous"]

        if not continuous_columns:
            QMessageBox.warning(self, "No Continuous Columns", "No continuous columns available for adding noise.")
            return

        column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to add noise:", continuous_columns, 0, False)
        if ok and column_name:
            try:
                if column_name in self.data.columns:
                    if column_name not in self.original_columns:
                        self.original_columns[column_name] = self.data[column_name].copy()  # Store original column data
                    if noise_type == 'laplacian':
                        noise = np.random.laplace(loc=0.0, scale=1.0, size=len(self.data[column_name]))
                    elif noise_type == 'gaussian':
                        noise = np.random.normal(loc=0.0, scale=1.0, size=len(self.data[column_name]))
                    self.data[column_name] += noise
                    self.show_preview()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while adding noise: {e}")




    def setup_treeview(self, view):

        """
        Configure the appearance and behavior of the given QTreeView.

        Sets the selection mode, background color, font, and sorting behavior for the provided
        QTreeView. Adjusts settings based on whether the view is the columns view.

        Parameters
        ----------
        view : QTreeView
            The tree view to be configured.
        """
    
        is_columns_view = view is self.columns_view
        view.setSelectionMode(QTreeView.MultiSelection if is_columns_view else QTreeView.NoSelection)
        view.setStyleSheet("background-color: #121212; color: #FFFFFF;")
        view.setSortingEnabled(True)
        view.header().setSectionResizeMode(QHeaderView.Stretch)
        view.header().setFont(QFont("Helvetica", 13))
        view.header().setStyleSheet("QHeaderView::section { background-color: #333; color: #FFFFFF; }")




    def load_file(self):

        """
        Open a file dialog to load a CSV or TSV file.

        Displays a file dialog allowing the user to select a CSV, TSV, or other file type. 
        If a file is selected, it calls `load_data` to load the file's content.
        """

        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath(), "CSV files (*.csv);;TSV files (*.tsv);;All files (*)")
        if file_path:
            self.load_data(file_path)




    def load_data(self, file_path):
        """
        Loads data from a specified file into the application's data structure.

        This method reads a CSV or TSV file from the provided file path and processes the data. It distinguishes between continuous and categorical columns based on the number of unique values and updates the internal data structures accordingly.

        Parameters:
        -----------
        file_path : str
            The path to the file to be loaded. The file extension should be either '.csv' or '.tsv'.

        Raises:
        -------
        FileNotFoundError
            If the specified file does not exist or cannot be found.
        pd.errors.EmptyDataError
            If the file is empty or cannot be read.
        pd.errors.ParserError
            If there is a parsing error in the file content.

        Notes:
        ------
      
        - Column names are stripped of leading and trailing whitespace.
        - Columns are classified as "Continuous" if they have more than 45 unique values; otherwise, they are classified as "Categorical".
        - The method stores a copy of the original data and updates the tree view with the column types and options for selecting columns.

        Returns:
        --------
        Loaded Data
        """

        try:
            sep = '\t' if file_path.lower().endswith('.tsv') else ','
            self.data = pd.read_csv(file_path, sep=sep)
            self.data.columns = self.data.columns.str.strip()
            self.column_unique_counts = {col: self.data[col].nunique() for col in self.data.columns}
            sorted_columns = sorted(self.column_unique_counts.items(), key=lambda x: x[1], reverse=True)
            column_types = [(col, count, "Continuous" if count > 45 else "Categorical") for col, count in sorted_columns]
            self.original_data = self.data.copy()  # Store the original data
            self.update_treeview(self.columns_model, column_types, add_checkbox=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")



    def update_treeview(self, model, data_list, add_checkbox=False):

        """
        Populate the given model with data and optionally add checkboxes.

        Clears the model and populates it with items from 'data_list'. 
        Optionally adds a checkable item to each row if 'add_checkbox' is True.

        Parameters
        ----------
        model : QStandardItemModel
            The model to update with the new data.
        data_list : list of list
            The data to populate the model, where each sublist represents a row.
        add_checkbox : bool, optional
            If True, adds a checkable item to each row (default is False).
        """
        model.removeRows(0, model.rowCount())
        for values in data_list:
            items = [NumericStandardItem(str(value)) if isinstance(value, (int, float)) else QStandardItem(str(value)) for value in values]
            if add_checkbox:
                checkbox_item = QStandardItem()
                checkbox_item.setCheckable(True)
                items.append(checkbox_item)
            model.appendRow(items)



    def calculate_unique_rows(self):
        """
        Calculates and displays various statistics related to the selected columns in the dataset.

        This method computes the number of unique rows based on the selected columns, as well as other metrics such as total rows, total columns, the number of selected columns, K-Anonymity, and L-Diversity. It updates a result label with these statistics.

        Computes:

        - Unique rows: The number of rows where the combination of values in the selected columns is unique.
        - K-Anonymity: A measure of how well the dataset is anonymized with respect to the selected columns.
        - L-Diversity: A measure of diversity within the sensitive attribute values if a sensitive attribute is selected.

        Uses:
        -----
        - 'self.get_selected_columns()': Retrieves the currently selected columns.
        - 'self.get_sensitive_attribute()': Retrieves the currently selected sensitive attribute.
        - 'self.calculate_k_anonymity(selected_columns)': Calculates the K-Anonymity for the selected columns.
        - 'self.calculate_l_diversity(selected_columns, sensitive_attr)': Calculates the L-Diversity for the selected columns and sensitive attribute.

        Updates:
        --------
        - 'self.result_label`: Displays the computed statistics including total rows, total columns, number of selected columns, number of unique rows, K-Anonymity, and L-Diversity.


        Raises:
        -------
        Exception
            If an error occurs during the computation of unique rows or other statistics.
        """

        selected_columns = self.get_selected_columns()
        if selected_columns:
            sensitive_attr = self.get_sensitive_attribute()
            try:
            
                value_counts = self.data[selected_columns].value_counts()
                num_unique_rows = len(value_counts[value_counts == 1])
            
                total_rows = len(self.data)
            
                total_columns = len(self.data.columns)
                num_selected_columns = len(selected_columns)
                k_anonymity = self.calculate_k_anonymity(selected_columns)
                l_diversity = self.calculate_l_diversity(selected_columns, sensitive_attr) if sensitive_attr else None
                
              
                result_text = (f"Total Rows: {total_rows}\n"
                               f"Total Columns: {total_columns}\n"
                               f"Selected Columns: {num_selected_columns}\n"
                               f"Unique Rows: {num_unique_rows}\n"
                               f"K-Anonymity: {k_anonymity}\n"
                               f"L-Diversity: {l_diversity}\n")
                self.result_label.setText(result_text)
            except Exception as e:
                self.result_label.setText(f"An error occurred: {e}")



    def get_selected_columns(self):

        """
        Retrieve the names of the selected columns in the columns view.

        Collects and returns the names of columns currently selected in 'columns_view'. 
        If no columns are selected, displays a message on 'result_label'.

        Returns:
        --------
        list of str
            The list of selected column names.
        """

        selected_indexes = self.columns_view.selectionModel().selectedRows()
        selected_columns = [self.columns_model.itemFromIndex(index).text() for index in selected_indexes]
        if not selected_columns:
            self.result_label.setText("Please select at least one column.")
        return selected_columns




    def get_sensitive_attribute(self):

        """
        Retrieve the name of the selected sensitive attribute.

        Iterates through the rows of `columns_model` to find the column marked 
        as the sensitive attribute (checked in the fourth column). Returns the 
        name of the first checked sensitive attribute or None if none are found.

        Returns:
        --------
        str or None
            The name of the sensitive attribute if one is selected, otherwise None.
        """
        for row in range(self.columns_model.rowCount()):
            if self.columns_model.item(row, 3).checkState() == Qt.Checked:
                return self.columns_model.item(row, 0).text()
        return None



    def calculate_k_anonymity(self, selected_columns):
        """
        Calculates the K-Anonymity for the specified columns in the dataset.

        Parameters:
        -----------
        selected_columns : list of str
            The list of column names used to calculate K-Anonymity.

        Returns:
        --------
        int:
            The K-Anonymity value, which is the smallest group size of records with the same values for the selected columns.

        Notes:
        ------
        - This method groups the dataset by the selected columns and calculates the size of each group.
        - It returns the minimum group size as the K-Anonymity value.

        Raises:
        -------
        ValueError
            If the 'selected_columns' list is empty or contains invalid column names.
        """

        grouped = self.data.groupby(selected_columns).size().reset_index(name='counts')
        return grouped['counts'].min()



    def calculate_l_diversity(self, selected_columns, sensitive_attr):
        """
        Calculates the L-Diversity for the specified columns in the dataset with respect to a sensitive attribute.

        L-Diversity measures the diversity of the sensitive attribute within each group defined by the selected columns. It is defined as the minimum number of distinct values of the sensitive attribute in any group. Higher L-Diversity indicates better protection of sensitive information.

        Parameters:
        -----------
        selected_columns : list of str
            The list of column names used to define the grouping in the dataset.
        
        sensitive_attr : str
            The name of the column that represents the sensitive attribute whose diversity is to be measured.

        Returns:
        --------
        int:
            The L-Diversity value, which is the minimum number of distinct values of the sensitive attribute within any group.
      
        Notes:
        ------
        - This method groups the dataset by the selected columns and calculates the number of unique values for the sensitive attribute in each group.
        - It returns the minimum number of distinct values of the sensitive attribute across all groups.

        Raises:
        -------
        ValueError
            If the 'selected_columns' list is empty, or if 'sensitive_attr' is not present in the dataset.
        """

        grouped = self.data.groupby(selected_columns)
        return grouped[sensitive_attr].nunique().min()



    def find_lowest_unique_columns(self):

        """
        Identify columns with the lowest impact on unique row counts when removed.

        This method analyzes the selected columns to determine their contribution 
        to the uniqueness of rows in the dataset. It performs the following steps:
        1. Retrieves selected columns.
        2. Calculates the number of unique rows using the selected columns.
        3. Iteratively removes each column to find the impact on the number of unique rows.
        4. Computes the difference in unique row counts and normalizes this difference based on the number of unique values in the column.
        5. Sorts and displays the results in descending order of normalized difference using `update_treeview`.

        Results are displayed in a tree view and include:
        - Column name
        - Unique rows after removal
        - Difference in unique row counts
        - Normalized difference

        If an error occurs, an error message is displayed on 'result_label'.

        """
        selected_columns = self.get_selected_columns()
        if selected_columns:
            try:
                subset_data = self.data[selected_columns]
                value_counts = subset_data.value_counts()
                unique_rows = value_counts[value_counts == 1].index
                all_unique_count = len(unique_rows)

                results = []
                for column in selected_columns:
                    temp_columns = [col for col in selected_columns if col != column]
                    if temp_columns:
                        subset_data_after_removal = self.data[temp_columns]
                        value_counts_after_removal = subset_data_after_removal.value_counts()
                        unique_rows_after_removal = value_counts_after_removal[value_counts_after_removal == 1].index
                        unique_count_after_removal = len(unique_rows_after_removal)
                        difference = all_unique_count - unique_count_after_removal
                        unique_values_count = subset_data[column].nunique()
                        normalized_difference = round(difference / unique_values_count, 1)
                        results.append((column, unique_count_after_removal, difference, normalized_difference))

                results.sort(key=lambda x: x[3], reverse=True)
                self.update_treeview(self.results_model, results, add_checkbox=False)
            except Exception as e:
                self.result_label.setText(f"An error occurred: {e}")


    def load_metadata(self):
        """
        Loads metadata from a JSON file and updates the column dropdown.

        Opens a file dialog to select a JSON file. Loads the selected file's content into 'self.metadata' and updates the column dropdown. Shows an error message if file loading fails.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", QDir.homePath(), "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.metadata = json.load(f)

                if self.metadata:  # Ensure metadata is not empty
                    self.update_column_dropdown()  # Update dropdown with new metadata
                    self.metadata_output_label.setText("Metadata loaded successfully. Please select a column.")  # Inform user to select a column
                else:
                    self.metadata_output_label.setText("No metadata found in the file.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")
                self.metadata_output_label.setText("Failed to load metadata.")  # Optional: display error message



    def update_column_dropdown(self):
        """
        Update the column dropdown menu with metadata keys.

        Clears the current items in the dropdown and repopulates it with column names 
        from the metadata. Adds a default "Select Column" option at the top.
        """
        self.column_dropdown.clear()
        self.column_dropdown.addItem("Select Column")
        if self.metadata:
            for column in self.metadata.keys():
                self.column_dropdown.addItem(column)


    def show_metadata_for_column(self):
        """
        Displays metadata for the currently selected column in the dropdown.

        Retrieves metadata for the selected column from `self.metadata` and displays it in `self.metadata_display`. Shows a warning if no metadata is available for the selected column.
        """
        column_name = self.column_dropdown.currentText()
        if column_name in self.metadata:
            metadata_info = self.metadata[column_name]
            # Update the QLabel in the empty frame to display the metadata
            self.metadata_output_label.setText(f"Metadata for {column_name}:\n{json.dumps(metadata_info, indent=4)}")
        else:
            QMessageBox.warning(self, "No metadata available for the selected column.")
            self.metadata_output_label.setText("")  # Clear the label if no metadata is available



    def round_values(self):
        """
        Rounds values in a selected continuous column to a specified precision.

        Rounds the values in the selected column according to the chosen precision. Stores the original data if not already stored and updates the preview.

        Raises:
        -------
        QMessageBox
            If no continuous columns are available or if an error occurs during rounding.
        """

        continuous_columns = [self.columns_model.item(row, 0).text() for row in range(self.columns_model.rowCount())
                              if self.columns_model.item(row, 2).text() == "Continuous"]

        if not continuous_columns:
            QMessageBox.warning(self, "No Continuous Columns", "No continuous columns available for rounding.")
            return

        column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to round:", continuous_columns, 0, False)
        if ok and column_name:
            precision, ok = QInputDialog.getItem(self, "Select Precision", "Select rounding precision:", ["10^1", "10^2", "10^3", "10^4", "10^5", "10^6"], 0, False)
            if ok and precision:
                try:
                    factor = 10 ** int(precision.split('^')[1])
                    if column_name in self.data.columns:
                        self.original_columns.setdefault(column_name, self.data[column_name].copy())  # Store original data if not already
                        self.data[column_name] = (self.data[column_name] / factor).round() * factor
                        self.show_preview()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"An error occurred while rounding: {e}")


    def revert_to_original(self):
        """
        Reverts the values in a selected column to their original state.

        Updates the preview to reflect the reverted column. If no original data is available for the selected column, shows a warning message.

        Raises:
        -------
        QMessageBox
            If an error occurs while reverting the column or if no original data is available.
        """

        column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to revert:", list(self.original_columns.keys()), 0, False)
        if ok and column_name:
            try:
                if column_name in self.original_columns:
                    self.data[column_name] = self.original_columns[column_name]
                    self.show_preview()
                else:
                    QMessageBox.warning(self, "Warning", f"No original data available for column {column_name}.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while reverting: {e}")



    def show_main_page(self):
        """
        Switches the displayed widget to the main page.

        Sets the 'stacked_widget' to show the 'main_page'. Function is used to navigate back to the main interface of the application.
        """

        self.stacked_widget.setCurrentWidget(self.main_page)



    def show_preview_page(self):
        """
        Switches the displayed widget to the preview page.

        Sets the 'stacked_widget' to show the 'preview_page'. 
        Function is used to navigate to the preview interface of the application.
        """
        self.stacked_widget.setCurrentWidget(self.preview_page)




def main():
   
    app = QApplication(sys.argv)
    window = metaprivBIDS()  # Assuming FileAnalyzer is your main window
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
