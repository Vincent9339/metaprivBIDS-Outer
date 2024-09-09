import sys
import json
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QFileDialog, QMessageBox, QTreeView, QHeaderView, QLabel,
                               QFrame, QTableView, QStackedWidget, QComboBox, QInputDialog, QSizePolicy,
                               QStyledItemDelegate, QMenu, QListWidget, QDialog) 

from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QAction
from PySide6.QtCore import Qt, QDir
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from itertools import combinations
from .suda_adapted import suda_calculation, find_msu
import piflib.pif_calculator as pif
from PySide6.QtWidgets import QTextBrowser
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QDateTime



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

class FileAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_path, self.data, self.column_unique_counts, self.metadata, self.sensitive_attr = None, None, {}, {}, None
        self.original_data = pd.DataFrame()  # To store the original data for reverting changes
        self.original_columns = {}  # To store the original data of individual columns
        self.combined_values = {} 
        self.combined_values_history = {}  
        
        # Initialize main UI elements
        self.initUI()

     
    def initUI(self):
        self.setWindowTitle('File Analyzer')
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet("background-color: #121212; color: #FFFFFF;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Initialize stacked widget
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Initialize main page
        self.main_page = QWidget()
        self.main_page_layout = QVBoxLayout(self.main_page)
        self.add_buttons(self.main_page_layout)
        self.add_frames(self.main_page_layout)

  
        combine_button_layout = QHBoxLayout()
        combine_button_layout.addStretch(1)  # Pushes the button to the right

        # Create the "Combine Column Contribution" button
        self.combine_column_button = QPushButton('Combined Column Contribution')
        self.combine_column_button.setStyleSheet("background-color: #4CAF50; color: #FFFFFF;")
        self.combine_column_button.clicked.connect(self.compute_combined_column_contribution)


        combine_button_layout.addWidget(self.combine_column_button)

        # Add the horizontal layout to the main page layout
        self.main_page_layout.addLayout(combine_button_layout)

        # Add the main page to the stacked widget
        self.stacked_widget.addWidget(self.main_page)

        # Initialize privacy information page
        self.privacy_info_page = QWidget()
        self.privacy_info_layout = QVBoxLayout(self.privacy_info_page)
        self.privacy_info_layout.setContentsMargins(10, 10, 10, 10)
        self.privacy_info_layout.setSpacing(10)

        # Create a horizontal layout for the buttons in privacy info page
        button_layout = QHBoxLayout()

        # Create the "Compute CIG" button
        self.cig_button = QPushButton('Compute CIG')
        self.cig_button.setStyleSheet("background-color: #FF9800; color: #FFFFFF;")
        self.cig_button.clicked.connect(self.compute_cig)
        button_layout.addWidget(self.cig_button)

        # Create the heatmap button
        self.heatmap_button = QPushButton('Generate CIG Heatmap')
        self.heatmap_button.setStyleSheet("background-color: #ff0066; color: #FFFFFF;")
        self.heatmap_button.clicked.connect(self.generate_heatmap)
        button_layout.addWidget(self.heatmap_button)

        # Create the close heatmap button
        self.close_heatmap_button = QPushButton('Close Heatmap')
        self.close_heatmap_button.setStyleSheet("background-color: #00c3ff; color: #FFFFFF;")
        self.close_heatmap_button.clicked.connect(self.hide_heatmap)
        button_layout.addWidget(self.close_heatmap_button)

        # Add the horizontal layout to the privacy info layout
        self.privacy_info_layout.addLayout(button_layout)

        # Create a QTextBrowser to display the CIG result
        self.cig_result_browser = QTextBrowser()
        self.cig_result_browser.setOpenExternalLinks(True)
        self.privacy_info_layout.addWidget(self.cig_result_browser)

        # Create a horizontal layout for the back button and add it at the bottom
        privacy_back_button_layout = QHBoxLayout()
        self.privacy_back_button = QPushButton('Back to Main')
        self.privacy_back_button.setStyleSheet("background-color: #F44336; color: #FFFFFF;")
        self.privacy_back_button.clicked.connect(self.show_main_page)
        privacy_back_button_layout.addWidget(self.privacy_back_button)
        self.privacy_info_layout.addLayout(privacy_back_button_layout)

        # Create the "Describe CIG" button
        self.describe_cig_button = QPushButton('Describe CIG')
        self.describe_cig_button.setStyleSheet("background-color: #009688; color: #FFFFFF;")
        self.describe_cig_button.clicked.connect(self.describe_cig)
        button_layout.addWidget(self.describe_cig_button)


        # Add the privacy info page to the stacked widget
        self.stacked_widget.addWidget(self.privacy_info_page)

        # Initialize preview page
        self.preview_page = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_page)
        self.preview_layout.setContentsMargins(10, 10, 10, 10)
        self.preview_layout.setSpacing(10)

        # Create a vertical layout for the preview table and buttons
        preview_and_buttons_layout = QVBoxLayout()
        preview_and_buttons_layout.setSpacing(10)

        self.preview_table = QTableView()
        self.preview_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_and_buttons_layout.addWidget(self.preview_table)

        # Add the preview table and buttons layout to the main preview layout
        self.preview_layout.addLayout(preview_and_buttons_layout)
        

        # Add preview page widgets including buttons right below the preview data
        self.add_preview_page_widgets(preview_and_buttons_layout)

        # Create a horizontal layout for the back button and add it at the bottom
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton('Back to Main')
        self.back_button.setStyleSheet("background-color: #F44336; color: #FFFFFF;")
        self.back_button.clicked.connect(self.show_main_page)
        back_button_layout.addWidget(self.back_button)

        self.preview_layout.addLayout(back_button_layout)
        self.stacked_widget.addWidget(self.preview_page)

    def show_graph_categorical_dialog(self):
        """
        Opens a dialog to select and graph a categorical column from the loaded dataset.

        This method displays a dialog for the user to choose a column from the available categorical
        columns in the dataset. If the dataset contains categorical columns, the user can select one, 
        and a tree graph based on the selected column will be plotted. If no categorical columns are 
        found, or no data is loaded, appropriate warning messages are shown.

        Steps:
        1. Checks if data is loaded.
        2. Retrieves the categorical columns from the dataset.
        3. Opens a dialog for the user to select a categorical column.
        4. Plots a tree graph for the selected column using combined values, if available.
        
        Raises:
            QMessageBox.Warning: If no data is loaded or no categorical columns are available.

        Parameters:
            None

        Returns:
            None
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
        1. Creates a directed graph (`DiGraph`) with the column name as the root node.
        2. Adds nodes and edges for combined values from `combined_values_history`.
        3. Adds nodes and edges for unique values in the selected column.
        4. Removes edges related to combined values to prevent overlap.
        5. Uses Graphviz layout for proper positioning of nodes.
        6. Draws and displays the graph using Matplotlib.

        Parameters:
        ----------
        column_name : str
            The name of the categorical column from the dataset to plot.

        Notes:
        -----
        - The graph will include nodes for individual values, and if any values were combined 
          into a single entity, the relationship will be reflected in the graph.
        - Uses Graphviz for positioning (`prog='dot'`) to ensure a hierarchical tree layout.

        Raises:
        -------
        None

        Returns:
        -------
        None
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

        Parameters:
        ----------
        None

        Notes:
        -----
        - The method uses a `QDialog` to allow the user to select values to combine.
        - If no categorical columns are available or if the dataset is not loaded, appropriate warnings are shown.

        Raises:
        -------
        QMessageBox.Warning: If no data is loaded, no categorical columns are available, or not enough unique values are present.

        Returns:
        -------
        None
        """

        if self.data is not None:
            # Get categorical columns
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

                # Convert all unique values to string
                unique_values = list(map(str, unique_values))

                # Create a dialog to select unique values
                dialog = QDialog(self)
                dialog.setWindowTitle("Select Values to Combine")
                dialog.setStyleSheet("background-color: #121212; color: #FFFFFF;")  
                layout = QVBoxLayout(dialog)

                list_widget = QListWidget(dialog)
                list_widget.setSelectionMode(QListWidget.MultiSelection)
                list_widget.addItems(unique_values)

                # Style the list widget to ensure text visibility
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
        ----------
        column_name : str
            The name of the column where values are to be combined.

        selected_items : list of QListWidgetItem
            The list of selected items from the dialog containing the values to be combined.

        Notes:
        -----
        - The method requires that at least two values are selected for combining. If fewer than two 
          values are selected, a warning is shown.
        - The original values of the column are stored to allow for potential future reference or undo operations.
        - The method updates both the `combined_values_history` and the dataset with the new combination.

        Raises:
        -------
        QMessageBox.Warning: If fewer than two values are selected or if the user does not provide a replacement value.

        Returns:
        -------
        None
    """

        selected_values = [item.text() for item in selected_items]
        if len(selected_values) < 2:
            QMessageBox.warning(self, "Insufficient Selection", "Please select at least two values to combine.")
            return
        if column_name not in self.original_columns:
            self.original_columns[column_name] = self.data[column_name].copy()
        replacement_value, ok = QInputDialog.getText(self, "Combine Values", "Enter the new value for the selected items:")
        
        if ok and replacement_value:  # Check if the user clicked OK and provided a value
            # Convert both the selected values and the replacement value to string
            selected_values = list(map(str, selected_values))
            replacement_value = str(replacement_value)
            
            # Add the combination history
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

        This method provides a summary of statistics for the CIG DataFrame (`cigs_df`) by generating 
        descriptive statistics and formatting the output as an HTML table. The following actions are performed:
        1. Checks if `cigs_df` exists and is not empty.
        2. Excludes the 'RIG' column from the description if it exists.
        3. Computes descriptive statistics for the remaining columns.
        4. Formats the statistics to two decimal places and converts them to an HTML table.
        5. Applies custom CSS styles to the HTML table for better readability and displays it in the `cig_result_browser`.
        6. Sets a maximum height for the `cig_result_browser` to ensure proper display.

        If `cigs_df` is not available or is empty, a message prompting the user to compute CIG is shown instead.

        Parameters:
        ----------
        None

        Notes:
        -----
        - The method requires that the `cigs_df` attribute is present and contains data.
        - Custom CSS is used to enhance the visual appearance of the HTML table.

        Raises:
        -------
        None

        Returns:
        -------
        None
        """

        if hasattr(self, 'cigs_df') and not self.cigs_df.empty:
            if 'RIG' in self.cigs_df.columns:
                cigs_df_for_description = self.cigs_df.drop(columns=['RIG'])
            else:
                cigs_df_for_description = self.cigs_df
            
            description = cigs_df_for_description.describe()
            description = description.applymap(lambda x: f"{x:.2f}")
            description_html = description.to_html(classes='dataframe', border=0)
            custom_css = """
            <style>
            .dataframe {
                border-collapse: collapse;
                width: 100%;
                color: #FFFFFF;
                background-color: #333333;
            }
            .dataframe th, .dataframe td {
                border: 1px solid #666666;
                padding: 8px;
                text-align: right;
            }
            .dataframe th {
                background-color: #444444;
            }
            .dataframe tr:nth-child(even) {
                background-color: #2c2c2c;
            }
            </style>
            """    
            self.cig_result_browser.setHtml(f"{custom_css}<html><body>{description_html}</body></html>")
            self.cig_result_browser.setMaximumHeight(400)  
        else:
            self.cig_result_browser.setPlainText("Please compute CIG before describing it.")



    def hide_heatmap(self):
        """
        Hides the heatmap and its associated controls from the user interface.

        This method checks if the heatmap label and the close heatmap button exist as attributes. 
        If they are present, it hides both the heatmap label and the close heatmap button from view.

        The primary purpose of this method is to remove the heatmap visualization and related 
        controls from the user interface when they are no longer needed.

        Parameters:
        ----------
        None

        Notes:
        -----
        - The method relies on the presence of `heatmap_label` and `close_heatmap_button` attributes.
        - If these attributes are not present, the method does not perform any actions.

        Raises:
        -------
        None

        Returns:
        -------
        None
        """

        if hasattr(self, 'heatmap_label'):
            self.heatmap_label.hide()
        if hasattr(self, 'close_heatmap_button'):
            self.close_heatmap_button.hide()


    def generate_heatmap(self):
        """
        Generates and displays a heatmap of the CIG (Categorical Information Gain) DataFrame.

        This method performs the following actions:
        1. Checks if the `cigs_df` attribute exists and is not empty.
        2. Excludes the 'RIG' column from the DataFrame for heatmap generation.
        3. Creates a heatmap using seaborn with a custom color map and saves it as an image file (`heatmap.png`).
        4. Displays the generated heatmap image in the user interface.
        5. Ensures that the heatmap label and close button are visible.

        If the `cigs_df` attribute is not present or is empty, the method displays a message in 
        `cig_result_browser` prompting the user to compute CIG before generating the heatmap.

        Parameters:
        ----------
        None

        Notes:
        -----
        - The heatmap is saved as `heatmap.png` in the current working directory.
        - A custom color map from seaborn's "RdYlGn" palette is used for the heatmap.
        - The method checks for and manages the presence of `heatmap_label` to display the heatmap 
          and ensures the `close_heatmap_button` is visible.

        Raises:
        -------
        None

        Returns:
        -------
        None
        """

        if hasattr(self, 'cigs_df') and not self.cigs_df.empty:
            cigs_df_no_rig = self.cigs_df.drop(columns=['RIG'])
            color_map = mcolors.ListedColormap(sns.color_palette("RdYlGn", 256).as_hex()[::-1])
      
            heatmap_filename = "heatmap.png"
            plt.figure(figsize=(10, 8))
            sns.heatmap(cigs_df_no_rig, cmap=color_map, annot=False, fmt="g", cbar=True)
            plt.title("CIG Heatmap")
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.savefig(heatmap_filename, bbox_inches='tight', pad_inches=0.1)  # Save the heatmap image
            plt.close()  # Close the plot to free up memory


            if not hasattr(self, 'heatmap_label'):
                self.heatmap_label = QLabel()
                self.privacy_info_layout.addWidget(self.heatmap_label)

          
            self.heatmap_label.setPixmap(QPixmap(heatmap_filename))
            self.heatmap_label.show()
            self.close_heatmap_button.show()  # Ensure the close button is visible
        else:
            self.cig_result_browser.setPlainText("Please compute CIG before generating the heatmap.")



    def compute_cig(self):
        """
        Computes and displays the Categorical Information Gain (CIG) for selected columns in the DataFrame.

        This method performs the following steps:
        1. Retrieves the selected columns from the DataFrame.
        2. Prompts the user to input a mask value, which is used to set specific values to zero in the CIG computation.
           - If a valid numeric mask value is provided, it is applied to the DataFrame.
           - If the input is invalid or left blank, no masking is applied.
        3. Computes the CIG values using the `pif` module and stores the results in a DataFrame.
        4. Adds a 'RIG' column to the DataFrame, which contains the sum of CIG values for each row.
        5. Prompts the user to input a percentile value to calculate the PIF (Percentile Information Factor).
        6. Displays the computed CIG values in an HTML table, along with the calculated PIF at the specified percentile.
        7. Applies custom CSS to format the HTML table and sets a maximum height for the result display.

        If no columns are selected or if the DataFrame is empty, appropriate messages are displayed.
        If the user cancels the percentile input, a message is shown indicating cancellation.

        Parameters:
        ----------
        None

        Notes:
        -----
        - The method requires the `piflib.pif_calculator` module for computing CIG values.
        - The mask value is used to set specific values to zero in the CIG DataFrame if provided.
        - The percentile input is used to calculate the PIF value, which is displayed along with the CIG values.

        Raises:
        -------
        ValueError: If the mask value is not a valid number.
        ValueError: If the percentile input is not within the range 0-100.

        Returns:
        -------
        None
        """

        import piflib.pif_calculator as pif
        from PySide6.QtWidgets import QInputDialog
        import numpy as np
        selected_columns = self.get_selected_columns()

        if not selected_columns:
            self.cig_result_browser.setPlainText("Please select at least one column.")
            return
        df = self.data[selected_columns]

        if df.empty:
            self.cig_result_browser.setPlainText("Data not available.")
            return
        mask_value, ok = QInputDialog.getText(None, 'Input Mask Value', 'Enter a mask value (or leave blank to skip):')

        if ok and mask_value != '':
            try:
                mask_value = float(mask_value)
                mask = df == mask_value
            except ValueError:
                self.cig_result_browser.setPlainText("Invalid mask value. Please enter a number.")
                return

            cigs = pif.compute_cigs(df)
            cigs_df = pd.DataFrame(cigs)
            cigs_df[mask] = 0
        else:
       
            cigs = pif.compute_cigs(df)
            cigs_df = pd.DataFrame(cigs)

    
        cigs_df['RIG'] = cigs_df.sum(axis=1)

   
        percentile, ok = QInputDialog.getInt(None, 'Input Percentile', 'Enter percentile (0-100):', 95, 0, 100)

        if not ok:
            self.cig_result_browser.setPlainText("Percentile input canceled.")
            return

        # Calculate the PIF
        pif_value = np.percentile(cigs_df['RIG'], percentile)

     
        self.cigs_df = cigs_df
        cigs_df_display = cigs_df.sort_values(by='RIG', ascending=False)

   
        
        cigs_df_display = cigs_df_display.applymap(lambda x: f"{x:.2f}")


        cigs_html = cigs_df_display.to_html(classes='dataframe', index=True, border=0)
        custom_css = """
        <style>
        .container {
            max-height: 300px; /* Set your desired maximum height here */
            overflow-y: auto; /* Enable vertical scrolling */
        }
        table.dataframe {
            border-collapse: collapse;
            width: 100%;
        }
        table.dataframe, th, td {
            border: 1px solid black;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        </style>
        """

    
        self.cig_result_browser.setHtml(f"{custom_css}<html><body><p>PIF at {percentile}th percentile: {pif_value:.2f}</p>{cigs_html}</body></html>")
        self.cig_result_browser.setMaximumHeight(400)



    def show_privacy_info(self):
        self.stacked_widget.setCurrentWidget(self.privacy_info_page)

    def add_buttons(self, layout):
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        buttons = [
            ("Load CSV/TSV File", self.load_file, "#4CAF50"),
            ("Privacy Calculation", self.calculate_unique_rows, "#2196F3"),
            ("Variable Optimization", self.find_lowest_unique_columns, "#FFC107"),
            ("Preview Data", self.show_preview, "#009688"),
            ("Compute SUDA", self.compute_suda, "#4CAF50"),
            ("Privacy Information Factor", self.show_privacy_info, "#9C27B0"),
        ]

        for text, slot, color in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"background-color: {color}; color: #FFFFFF;")
            btn.clicked.connect(slot)
            button_layout.addWidget(btn)



    def compute_suda(self):
        """
        Computes the Sample Uniques Detection Algorithm (SUDA) metrics for the selected columns of data.

        This method performs the following steps:
        1. Checks if data is loaded; if not, it shows an error message and returns.
        2. Prompts the user to input values for `max_msu` and `dis`:
           - `max_msu`: The maximum number of minimum sample uniques (MSUs) to consider.
           - `dis`: The data intrusion simulation value for the SUDA calculation.
        3. Copies the original data and selects the columns specified by the user.
        4. Performs the SUDA computation, a sample uniques detection algorithm, using the provided parameters.
        5. Computes the Median Absolute Deviation (MAD) of the SUDA results.
        6. Displays the results in a dialog, including the MAD value.

        Parameters:
        ----------
        None

        Notes:
        -----
        - The `suda_calculation` function is used to perform the SUDA computation.
        - The `show_results_dialog` method is used to display the results to the user.

        Raises:
        -------
        QMessageBox: If no data is loaded or no columns are selected.

        Returns:
        -------
        None
        """

        if self.data is None:
            QMessageBox.warning(self, 'Error', 'No data loaded.')
            return


        max_msu, ok = QInputDialog.getInt(self, "Input", "Enter the max_msu value:", 2, 1, 10, 1)
        if not ok:
            return  # User cancelled or input is invalid

        dis, ok = QInputDialog.getDouble(self, "Input", "Enter the dis value:", 0.2, 0.0, 10.0, 4)
        if not ok:
            return  # User cancelled or input is invalid

 
        self.data = self.original_data.copy()

 
        selected_columns = self.get_selected_columns()
        original_index = self.data.index

        filtered_data = self.data[selected_columns]

        if not selected_columns:
            QMessageBox.warning(self, 'Error', 'No columns selected.')
            return

  
        suda_result = suda_calculation(filtered_data, max_msu=max_msu, dis=dis)
        suda_result['original_index'] = original_index
        columns = ['original_index'] + [col for col in suda_result.columns if col != 'original_index']

        suda_result = suda_result[columns]

        median = suda_result['dis-suda'].median()
        absolute_deviations = (suda_result['dis-suda'] - median).abs()
        mad = absolute_deviations.median()
        
        mad_formatted = f"{mad:.5f}"
        
        self.show_results_dialog(suda_result, result_type="suda", mad_value=mad_formatted)


        



    def compute_combined_column_contribution(self):
        """
        Computes and evaluates the contribution of various column combinations to unique row counts in the dataset.

        This method performs the following steps:
        1. Checks if data is loaded; if not, it displays a warning and returns.
        2. Prompts the user to input minimum and maximum combination sizes for column combinations.
        3. Iterates over all column combinations of sizes ranging from `min_size` to `max_size`.
        4. For each combination:
           - Calculates the number of unique rows (rows with unique values) in the dataset for the selected columns.
           - Calculates the number of unique rows excluding the selected columns.
           - Stores the combination, the number of unique rows, and the number of unique rows excluding columns.
        5. Computes a score for each combination based on the total unique rows and the unique rows excluding columns.
        6. Displays the results in a dialog.

        Parameters:
        ----------
        None

        Notes:
        -----
        - The results include the combination of columns, the count of unique rows, and a score based on the contribution to unique row counts.
        - The `show_results_dialog` method is used to display the results to the user.

        Raises:
        -------
        QMessageBox: If no data is loaded or no columns are selected.

        Returns:
        -------
        None
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
        self.column_combobox.clear()
        self.column_combobox.addItem("Select Column")

        if self.data is not None:
            for column in self.data.columns:
                self.column_combobox.addItem(column)

    def get_categorical_columns(self):
        return [self.columns_model.item(row, 0).text() for row in range(self.columns_model.rowCount())
                if self.columns_model.item(row, 2).text() == "Categorical"]



    def add_frames(self, layout):
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
        variable_optimization_layout = QVBoxLayout(self.variable_optimization_frame)
        self.results_view = QTreeView()
        self.results_model = QStandardItemModel()
        self.results_model.setHorizontalHeaderLabels(["Quasi Identifiers", "Unique Rows After Removal", "Difference", "Normalized"])
        self.results_view.setModel(self.results_model)
        self.setup_treeview(self.results_view)
        variable_optimization_layout.addWidget(self.results_view)

    def add_preview_page_widgets(self, layout):

        button_layout = QHBoxLayout()
        
  
        button_data = [
            ('Round Continuous Values', '673AB7', self.round_values),
            ('Add Laplacian Noise', '009688', lambda: self.add_noise('laplacian')),
            ('Add Gaussian Noise', '4CAF50', lambda: self.add_noise('gaussian')),
            ('Revert to Original', 'FF5722', self.revert_to_original),
            ('Combine Values', 'FF9800', self.show_combine_values_dialog)  # Add Combine Values button
        ]

        for text, color, func in button_data:
            button = QPushButton(text)
            button.setStyleSheet(f"background-color: #{color}; color: #FFFFFF;")
            button.clicked.connect(func)
            button_layout.addWidget(button)
        
     
        self.graph_button = QPushButton('Graph Categorical')
        self.graph_button.setStyleSheet("background-color: #3F51B5; color: #FFFFFF;")
        self.graph_button.clicked.connect(self.show_graph_categorical_dialog)
        button_layout.addWidget(self.graph_button)
        
        layout.addLayout(button_layout)

      
        self.metadata_display = QLabel('')
        self.metadata_display.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.metadata_display)

    
        metadata_layout = QVBoxLayout()
        self.column_dropdown = QComboBox()
        self.column_dropdown.addItem("Select Column")
        self.column_dropdown.currentIndexChanged.connect(self.show_metadata_for_column)
        self.column_dropdown.setStyleSheet("""
            QComboBox {
                border: 2px solid #FFFFFF;
                border-radius: 5px;
                padding: 2px 4px;
                background-color: #121212;
                color: #FFFFFF;
            }
            QComboBox::drop-down {
                border-left: 2px solid #FFFFFF;
            }
        """)
        metadata_layout.addWidget(self.column_dropdown)
        self.load_metadata_button = QPushButton('Load JSON Metadata')
        self.load_metadata_button.setStyleSheet("background-color: #3F51B5; color: #FFFFFF;")
        self.load_metadata_button.clicked.connect(self.load_metadata)
        metadata_layout.addWidget(self.load_metadata_button)

        layout.addLayout(metadata_layout)




    def create_noise_menu(self):
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
        ----------
        noise_type : str
            The type of noise to add. Options are:
            - 'laplacian': Adds Laplacian noise.
            - 'gaussian': Adds Gaussian noise.

        Raises:
        ------
        ValueError
            If an invalid `noise_type` is provided.

        Notes:
        -----
        - The method first checks if there are any continuous columns available. If not, a warning is shown.
        - The user is prompted to select a column to which the noise will be added.
        - The method preserves the original data of the selected column before modifying it with the specified noise.
        - The `show_preview` method is called after adding the noise to update any relevant displays.

        Returns:
        -------
        None
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
    
        is_columns_view = view is self.columns_view
        view.setSelectionMode(QTreeView.MultiSelection if is_columns_view else QTreeView.NoSelection)
        view.setStyleSheet("background-color: #121212; color: #FFFFFF;")
        view.setSortingEnabled(True)
        view.header().setSectionResizeMode(QHeaderView.Stretch)
        view.header().setFont(QFont("Helvetica", 13))
        view.header().setStyleSheet("QHeaderView::section { background-color: #333; color: #FFFFFF; }")


    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath(), "CSV files (*.csv);;TSV files (*.tsv);;All files (*)")
        if file_path:
            self.load_data(file_path)




    def load_data(self, file_path):
        """
        Loads data from a specified file into the application's data structure.

        This method reads a CSV or TSV file from the provided file path and processes the data. It distinguishes between continuous and categorical columns based on the number of unique values and updates the internal data structures accordingly.

        Parameters:
        ----------
        file_path : str
            The path to the file to be loaded. The file extension should be either '.csv' or '.tsv'.

        Raises:
        ------
        FileNotFoundError
            If the specified file does not exist or cannot be found.
        pd.errors.EmptyDataError
            If the file is empty or cannot be read.
        pd.errors.ParserError
            If there is a parsing error in the file content.

        Notes:
        -----
        - The file extension determines the delimiter used: tab (`\t`) for TSV files and comma (`,`) for CSV files.
        - Column names are stripped of leading and trailing whitespace.
        - Columns are classified as "Continuous" if they have more than 45 unique values; otherwise, they are classified as "Categorical".
        - The method stores a copy of the original data and updates the tree view with the column types and options for selecting columns.

        Returns:
        -------
        None
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
        ----------
        - Unique rows: The number of rows where the combination of values in the selected columns is unique.
        - K-Anonymity: A measure of how well the dataset is anonymized with respect to the selected columns.
        - L-Diversity: A measure of diversity within the sensitive attribute values if a sensitive attribute is selected.

        Uses:
        -----
        - `self.get_selected_columns()`: Retrieves the currently selected columns.
        - `self.get_sensitive_attribute()`: Retrieves the currently selected sensitive attribute.
        - `self.calculate_k_anonymity(selected_columns)`: Calculates the K-Anonymity for the selected columns.
        - `self.calculate_l_diversity(selected_columns, sensitive_attr)`: Calculates the L-Diversity for the selected columns and sensitive attribute.

        Updates:
        --------
        - `self.result_label`: Displays the computed statistics including total rows, total columns, number of selected columns, number of unique rows, K-Anonymity, and L-Diversity.

        Returns:
        -------
        None

        Raises:
        ------
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
        selected_indexes = self.columns_view.selectionModel().selectedRows()
        selected_columns = [self.columns_model.itemFromIndex(index).text() for index in selected_indexes]
        if not selected_columns:
            self.result_label.setText("Please select at least one column.")
        return selected_columns

    def get_sensitive_attribute(self):
        for row in range(self.columns_model.rowCount()):
            if self.columns_model.item(row, 3).checkState() == Qt.Checked:
                return self.columns_model.item(row, 0).text()
        return None



    def calculate_k_anonymity(self, selected_columns):
        """
        Calculates the K-Anonymity for the specified columns in the dataset.

        K-Anonymity is a measure of how well the dataset is anonymized with respect to the selected columns. It is defined as the smallest number of records that have the same values for the selected columns. Higher K-Anonymity indicates better anonymization.

        Parameters:
        -----------
        selected_columns : list of str
            The list of column names used to calculate K-Anonymity.

        Returns:
        --------
        int
            The K-Anonymity value, which is the smallest group size of records with the same values for the selected columns.

        Example:
        --------
        If the selected columns are `['Age', 'ZipCode']` and there are groups of 5 records with the same `Age` and `ZipCode` values, and groups of 10 records with other `Age` and `ZipCode` values, the method will return 5.

        Notes:
        ------
        - This method groups the dataset by the selected columns and calculates the size of each group.
        - It returns the minimum group size as the K-Anonymity value.

        Raises:
        -------
        ValueError
            If the `selected_columns` list is empty or contains invalid column names.
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
        int
            The L-Diversity value, which is the minimum number of distinct values of the sensitive attribute within any group.

        Example:
        --------
        If the selected columns are `['Age', 'ZipCode']` and there are groups of 3 records with 2 distinct values for the sensitive attribute (e.g., 'Income') in one group, and groups with 5 distinct values in other groups, the method will return 2.

        Notes:
        ------
        - This method groups the dataset by the selected columns and calculates the number of unique values for the sensitive attribute in each group.
        - It returns the minimum number of distinct values of the sensitive attribute across all groups.

        Raises:
        -------
        ValueError
            If the `selected_columns` list is empty, or if `sensitive_attr` is not present in the dataset.
        """

        grouped = self.data.groupby(selected_columns)
        return grouped[sensitive_attr].nunique().min()




    def find_lowest_unique_columns(self):
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



    def show_preview(self):
        """
        Displays the first 10 rows of the loaded dataset in a preview table.

        Updates the preview table with the first 10 rows of `self.data` and adjusts the table's height. Updates the column dropdown and switches to the preview page. Shows a warning if no data is loaded.

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
            self.preview_table.setMaximumHeight(200) 
            self.update_column_dropdown()
            self.stacked_widget.setCurrentWidget(self.preview_page)
        else:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")




    def load_metadata(self):
        """
        Loads metadata from a JSON file and updates the column dropdown.

        Opens a file dialog to select a JSON file. Loads the selected file's content into `self.metadata` and updates the column dropdown. Shows an error message if file loading fails.

        Example:
        --------
        Opens a file dialog to select a JSON file, loads the file's content, and updates UI elements.

        Raises:
        -------
        QMessageBox
            If an error occurs while loading the file.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", QDir.homePath(), "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.metadata = json.load(f)
                self.update_column_dropdown()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")



    def update_column_dropdown(self):
        self.column_dropdown.clear()
        self.column_dropdown.addItem("Select Column")
        if self.metadata:
            for column in self.metadata.keys():
                self.column_dropdown.addItem(column)



    def show_metadata_for_column(self):
        """
        Displays metadata for the currently selected column in the dropdown.

        Retrieves metadata for the selected column from `self.metadata` and displays it in `self.metadata_display`. Shows a warning if no metadata is available for the selected column.

        Example:
        --------
        Displays metadata information for the column selected in the dropdown menu.

        Raises:
        -------
        QMessageBox
            If no metadata is available for the selected column.
        """

        column_name = self.column_dropdown.currentText()
        if column_name in self.metadata:
            metadata_info = self.metadata[column_name]
            self.metadata_display.setText(f"Metadata for {column_name}:\n{json.dumps(metadata_info, indent=4)}")
        else:
            QMessageBox.warning(self, "No metadata available for the selected column.")




    def round_values(self):
        """
        Rounds values in a selected continuous column to a specified precision.

        Prompts the user to select a continuous column and rounding precision. Rounds the values in the selected column according to the chosen precision. Stores the original data if not already stored and updates the preview.

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

        Prompts the user to select a column and restores its values from the original data. Updates the preview to reflect the reverted column. If no original data is available for the selected column, shows a warning message.

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

        Sets the `stacked_widget` to show the `main_page`. This method is used to navigate back to the main interface of the application.
        """

        self.stacked_widget.setCurrentWidget(self.main_page)




    def show_preview_page(self):
        """
        Switches the displayed widget to the preview page.

        Sets the `stacked_widget` to show the `preview_page`. This method is used to navigate to the preview interface of the application.
        """
        self.stacked_widget.setCurrentWidget(self.preview_page)




    def show_hierarchical_page(self):
        self.stacked_widget.setCurrentWidget(self.hierarchical_page)




def main():
   
    app = QApplication(sys.argv)
    window = FileAnalyzer()  # Assuming FileAnalyzer is your main window
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
