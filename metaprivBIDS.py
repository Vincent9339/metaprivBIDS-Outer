import sys
import json
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QFileDialog, QMessageBox, QTreeView, QHeaderView, QLabel,
                               QFrame, QTableView, QStackedWidget, QComboBox, QInputDialog, QSizePolicy,
                               QStyledItemDelegate, QMenu, QListWidget, QDialog)  # Added QDialog

from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QAction
from PySide6.QtCore import Qt, QDir
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from itertools import combinations
from suda_adapted import suda_calculation, find_msu
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

        # Create a horizontal layout for the "Combine Column Contribution" button
        combine_button_layout = QHBoxLayout()
        combine_button_layout.addStretch(1)  # Pushes the button to the right

        # Create the "Combine Column Contribution" button
        self.combine_column_button = QPushButton('Combined Column Contribution')
        self.combine_column_button.setStyleSheet("background-color: #4CAF50; color: #FFFFFF;")
        self.combine_column_button.clicked.connect(self.compute_combined_column_contribution)

        # Add the button to the bottom-right layout
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
        # Step 1: Create a new directed graph
        G = nx.DiGraph()

        # Step 2: Clear the graph completely
        G.clear()

        # Step 3: Add the column name as the root node
        G.add_node(column_name)

        # Step 4: Initialize the replacement node
        replacement_node = None

        # Step 5: Track nodes and edges to add
        nodes_to_add = set()
        edges_to_add = set()

        # Step 6: Track combined values so they don't get direct edges from the column name
        combined_values_set = set()

        # Step 7: Process combined values from history
        if column_name in self.combined_values_history:
            for combined_values, replacement_value in self.combined_values_history[column_name]:
                # Add the replacement value as a new node
                replacement_node = replacement_value
                nodes_to_add.add(replacement_node)
                edges_to_add.add((column_name, replacement_node))  # Edge from column_name to replacement_node

                # For each combined value, link to the replacement node
                for value in combined_values:
                    if pd.notna(value):
                        nodes_to_add.add(value)
                        edges_to_add.add((replacement_node, value))  # Edge from replacement_node to old combined value
                        combined_values_set.add(value)  # Track combined values

        # Step 8: Add values from the column that are not part of combined values directly to the column
        unique_values = self.data[column_name].unique()
        for value in unique_values:
            if pd.notna(value) and value not in combined_values_set:
                nodes_to_add.add(value)
                edges_to_add.add((column_name, value))  # Direct edge from column_name to value

        # Step 9: Add nodes and edges to the graph
        G.add_nodes_from(nodes_to_add)
        G.add_edges_from(edges_to_add)

        # Debugging: Print initial state
        print("Initial Nodes:", G.nodes())
        print("Initial Edges:", G.edges())

        # Step 10: Remove edges from the root node to any nodes that are part of combined values
        # Root should only connect to nodes that are not in combined values
        for node in G.successors(column_name):
            if node in combined_values_set:
                G.remove_edge(column_name, node)

        # Debugging: Print state after cleanup
        print("Nodes after cleanup:", G.nodes())
        print("Edges after cleanup:", G.edges())

        # Step 11: Get positions for the nodes in the graph using graphviz_layout for hierarchy
        pos = nx.drawing.nx_agraph.graphviz_layout(G, prog='dot')

        # Step 12: Create a plot
        plt.figure(figsize=(12, 8))
        nx.draw(G, pos, with_labels=True, node_size=1000, node_color='white', font_size=6, font_weight='normal', edge_color='black')

        # Step 13: Add title and show plot
        plt.title(f'Tree Graph of Values in Column \"{column_name}\"', fontsize=12)
        plt.show()



    def show_combine_values_dialog(self):
        if self.data is not None:
            # Get categorical columns
            categorical_columns = self.get_categorical_columns()

            if not categorical_columns:
                QMessageBox.warning(self, "No Categorical Columns", "No categorical columns available for combining values.")
                return

            column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to combine values:", categorical_columns, 0, False)

            if ok and column_name:
                unique_values = self.data[column_name].unique()
                unique_values = [val for val in unique_values if pd.notna(val)]  # Remove NaN values

                if len(unique_values) < 2:
                    QMessageBox.warning(self, "Not Enough Values", "The selected column does not have enough unique values to combine.")
                    return

                # Convert all unique values to string
                unique_values = list(map(str, unique_values))

                # Create a dialog to select unique values
                dialog = QDialog(self)
                dialog.setWindowTitle("Select Values to Combine")
                dialog.setStyleSheet("background-color: #121212; color: #FFFFFF;")  # Dialog background color
                layout = QVBoxLayout(dialog)

                list_widget = QListWidget(dialog)
                list_widget.setSelectionMode(QListWidget.MultiSelection)
                list_widget.addItems(unique_values)  # Add values as strings

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
        selected_values = [item.text() for item in selected_items]

        # Check if at least two items are selected
        if len(selected_values) < 2:
            QMessageBox.warning(self, "Insufficient Selection", "Please select at least two values to combine.")
            return

        # Store original data for the column if not already stored
        if column_name not in self.original_columns:
            self.original_columns[column_name] = self.data[column_name].copy()

        # Ask the user for the replacement value
        replacement_value, ok = QInputDialog.getText(self, "Combine Values", "Enter the new value for the selected items:")
        
        if ok and replacement_value:  # Check if the user clicked OK and provided a value
            # Convert both the selected values and the replacement value to string
            selected_values = list(map(str, selected_values))
            replacement_value = str(replacement_value)
            
            # Add the combination history
            if column_name not in self.combined_values_history:
                self.combined_values_history[column_name] = []
            self.combined_values_history[column_name].append((selected_values, replacement_value))

            # Ensure the column data is also treated as strings for replacement
            self.data[column_name] = self.data[column_name].astype(str)

            # Replace the selected values with the new combined value in the data
            self.data[column_name] = self.data[column_name].replace(selected_values, replacement_value)

            # Show the updated data in the preview (refresh the view)
            self.show_preview()  # This should refresh the data in your UI so you see the combined values

            # Notify the user that the combination was successful
            QMessageBox.information(self, "Success", "Values have been successfully combined.")







    def describe_cig(self):
        if hasattr(self, 'cigs_df') and not self.cigs_df.empty:
            # Remove the 'RIG' column if it exists
            if 'RIG' in self.cigs_df.columns:
                cigs_df_for_description = self.cigs_df.drop(columns=['RIG'])
            else:
                cigs_df_for_description = self.cigs_df
            
            # Compute descriptive statistics
            description = cigs_df_for_description.describe()

            # Format the DataFrame to 2 decimal places
            description = description.applymap(lambda x: f"{x:.2f}")

            # Convert the DataFrame to HTML table
            description_html = description.to_html(classes='dataframe', border=0)

            # Define custom CSS to style the HTML content
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

            # Update the QTextBrowser with the HTML content
            self.cig_result_browser.setHtml(f"{custom_css}<html><body>{description_html}</body></html>")
            self.cig_result_browser.setMaximumHeight(400)  # Optional: Set maximum height
        else:
            self.cig_result_browser.setPlainText("Please compute CIG before describing it.")



    def hide_heatmap(self):
        if hasattr(self, 'heatmap_label'):
            self.heatmap_label.hide()
        if hasattr(self, 'close_heatmap_button'):
            self.close_heatmap_button.hide()


    def generate_heatmap(self):
        if hasattr(self, 'cigs_df') and not self.cigs_df.empty:
            cigs_df_no_rig = self.cigs_df.drop(columns=['RIG'])

            # Generate a colormap
            color_map = mcolors.ListedColormap(sns.color_palette("RdYlGn", 256).as_hex()[::-1])

            # Save the heatmap to a file
            heatmap_filename = "heatmap.png"
            plt.figure(figsize=(10, 8))
            sns.heatmap(cigs_df_no_rig, cmap=color_map, annot=False, fmt="g", cbar=True)
            plt.title("CIG Heatmap")
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.savefig(heatmap_filename, bbox_inches='tight', pad_inches=0.1)  # Save the heatmap image
            plt.close()  # Close the plot to free up memory

            # Create QLabel for the heatmap if it does not exist
            if not hasattr(self, 'heatmap_label'):
                self.heatmap_label = QLabel()
                self.privacy_info_layout.addWidget(self.heatmap_label)

            # Update the QLabel with the heatmap image
            self.heatmap_label.setPixmap(QPixmap(heatmap_filename))
            self.heatmap_label.show()
            self.close_heatmap_button.show()  # Ensure the close button is visible
        else:
            self.cig_result_browser.setPlainText("Please compute CIG before generating the heatmap.")



    def compute_cig(self):
        import piflib.pif_calculator as pif
        from PySide6.QtWidgets import QInputDialog
        import numpy as np

        # Get the selected columns
        selected_columns = self.get_selected_columns()

        if not selected_columns:
            self.cig_result_browser.setPlainText("Please select at least one column.")
            return

        # Use the full data stored in self.data
        df = self.data[selected_columns]

        if df.empty:
            self.cig_result_browser.setPlainText("Data not available.")
            return

        # Ask the user if they want to apply a mask
        mask_value, ok = QInputDialog.getText(None, 'Input Mask Value', 'Enter a mask value (or leave blank to skip):')

        if ok and mask_value != '':
            try:
                mask_value = float(mask_value)
                mask = df == mask_value
            except ValueError:
                self.cig_result_browser.setPlainText("Invalid mask value. Please enter a number.")
                return

            # Compute CIGs using the selected columns DataFrame and apply the mask
            cigs = pif.compute_cigs(df)
            cigs_df = pd.DataFrame(cigs)

            # Apply the mask by setting masked positions to 0
            cigs_df[mask] = 0
        else:
            # Compute CIGs without masking
            cigs = pif.compute_cigs(df)
            cigs_df = pd.DataFrame(cigs)

        # Calculate RIG column (sum across rows)
        cigs_df['RIG'] = cigs_df.sum(axis=1)

        # Ask user for percentile value
        percentile, ok = QInputDialog.getInt(None, 'Input Percentile', 'Enter percentile (0-100):', 95, 0, 100)

        if not ok:
            self.cig_result_browser.setPlainText("Percentile input canceled.")
            return

        # Calculate the PIF
        pif_value = np.percentile(cigs_df['RIG'], percentile)

        # Store the computed CIGs for heatmap generation
        self.cigs_df = cigs_df
        cigs_df_display = cigs_df.sort_values(by='RIG', ascending=False)

        # Format the DataFrame for display, excluding the RIG column
        
        cigs_df_display = cigs_df_display.applymap(lambda x: f"{x:.2f}")

        # Convert the DataFrame to an HTML table with custom CSS
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

        # Update the QTextBrowser with the HTML content
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
        if self.data is None:
            QMessageBox.warning(self, 'Error', 'No data loaded.')
            return

        # Prompt user for max_msu and dis values
        max_msu, ok = QInputDialog.getInt(self, "Input", "Enter the max_msu value:", 2, 1, 10, 1)
        if not ok:
            return  # User cancelled or input is invalid

        dis, ok = QInputDialog.getDouble(self, "Input", "Enter the dis value:", 0.2, 0.0, 10.0, 4)
        if not ok:
            return  # User cancelled or input is invalid

        # Reset the data to its original state to avoid issues with subsequent runs
        self.data = self.original_data.copy()

        # Get the selected columns
        selected_columns = self.get_selected_columns()
        original_index = self.data.index

        filtered_data = self.data[selected_columns]

        if not selected_columns:
            QMessageBox.warning(self, 'Error', 'No columns selected.')
            return

        # Perform SUDA calculation with user-specified parameters
        suda_result = suda_calculation(filtered_data, max_msu=max_msu, dis=dis)
        suda_result['original_index'] = original_index
        columns = ['original_index'] + [col for col in suda_result.columns if col != 'original_index']

        suda_result = suda_result[columns]

        median = suda_result['dis-suda'].median()
        absolute_deviations = (suda_result['dis-suda'] - median).abs()
        mad = absolute_deviations.median()
        
        mad_formatted = f"{mad:.5f}"
        
        # Add MAD as a new column in suda_result
        
        
        
        
        # Show the SUDA results
        self.show_results_dialog(suda_result, result_type="suda", mad_value=mad_formatted)


        



    def compute_combined_column_contribution(self):
        if self.data is None:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")
            return
        
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            QMessageBox.warning(self, "Warning", "Please select at least one column.")
            return

        # Ask user for the combination range (min and max)
        min_size, ok_min = QInputDialog.getInt(self, "Select Minimum Combination Size", "Enter minimum combination size:", 3, 1, len(selected_columns))
        if not ok_min:
            return  # User canceled the input dialog
        
        max_size, ok_max = QInputDialog.getInt(self, "Select Maximum Combination Size", "Enter maximum combination size:", 7, min_size, len(selected_columns))
        if not ok_max:
            return  # User canceled the input dialog
        
        results = []
        total_unique_rows = None

        # Generate combinations for different sizes based on user input
        for r in range(min_size, max_size + 1):  # Adjust based on user input
            print(f"Processing combinations of size {r}...")
            
            # Generate all combinations of size r
            all_combinations = combinations(selected_columns, r)
            
            for comb in all_combinations:
                selected_cols = list(comb)
                
                # Compute value counts for the selected columns
                value_counts = self.data[selected_cols].value_counts()
                
                # Count how many rows have exactly one occurrence (i.e., unique rows)
                num_unique_rows = len(value_counts[value_counts == 1])
                
                # Calculate unique rows excluding the specified columns
                remaining_columns = [col for col in selected_columns if col not in selected_cols]
                
                # Ensure remaining_columns is not empty
                if remaining_columns:
                    value_counts_excluded = self.data[remaining_columns].value_counts()
                    num_excluded_unique_rows = len(value_counts_excluded[value_counts_excluded == 1])
                else:
                    num_excluded_unique_rows = 0  # If no remaining columns, set to 0
                
                # Store the results in a dictionary
                results.append({
                    'Combination': ', '.join(selected_cols),
                    'Unique Rows': num_unique_rows,
                    'Unique Rows Excluding Columns': num_excluded_unique_rows
                })
        
        # Convert the results into a DataFrame
        all_combinations_df = pd.DataFrame(results)
        
        # Compute total unique rows
        if total_unique_rows is None:
            total_value_counts = self.data[selected_columns].value_counts()
            total_unique_rows = len(total_value_counts[total_value_counts == 1])
        
        # Compute the score
        all_combinations_df['Score'] = (total_unique_rows - all_combinations_df['Unique Rows Excluding Columns']) / all_combinations_df['Unique Rows']
        
        # Show results in the dialog
        self.show_results_dialog(all_combinations_df)




    def show_results_dialog(self, results_df, result_type="combined", mad_value=None):
        # Create a QDialog window
        dialog = QDialog(self)

        # Set the window title based on the result type
        if result_type == "suda":
            dialog.setWindowTitle("SUDA Calculation Results")
        else:
            dialog.setWindowTitle("Combined Column Contribution Results")

        # Style the dialog window
        dialog.setStyleSheet("background-color: #121212; color: #FFFFFF;")
        layout = QVBoxLayout(dialog)

        # If mad_value is provided, show it as a QLabel at the top of the dialog
        if mad_value is not None:
            mad_label = QLabel(f"Median Absolute Deviation (MAD): {mad_value}")
            mad_label.setStyleSheet("font-size: 14px; color: #FFFFFF;")
            layout.addWidget(mad_label)

        # Create a QTableView for displaying the results
        results_table = QTableView()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(results_df.columns)

        # Populate the table with the results
        for row in results_df.itertuples(index=False):
            items = [QStandardItem(str(item)) for item in row]
            model.appendRow(items)

        results_table.setModel(model)

        # Set table properties
        results_table.setSortingEnabled(True)  # Enable sorting of columns
        results_table.resizeColumnsToContents()  # Auto resize columns to fit content

        # Add the table to the layout
        layout.addWidget(results_table)

        # Add a "Save as CSV" button
        save_button = QPushButton("Save as CSV")
        save_button.setStyleSheet("background-color: #4CAF50; color: #FFFFFF;")
        layout.addWidget(save_button)

        # Save the CSV file when the button is clicked
        def save_as_csv():
            # Get the current timestamp
            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")

            # Create a default filename based on result type and timestamp
            if result_type == "suda":
                default_filename = f"sudaresult_{timestamp}.csv"
            else:
                default_filename = f"combinedresult_{timestamp}.csv"

            # Show a QFileDialog to allow the user to choose the save location
            file_path, _ = QFileDialog.getSaveFileName(dialog, "Save as CSV", default_filename, "CSV Files (*.csv)")

            # If the user provided a path, save the CSV file
            if file_path:
                results_df.to_csv(file_path, index=False)
                QMessageBox.information(dialog, "Success", f"File saved as {file_path}")

        # Connect the button click event to the save_as_csv function
        save_button.clicked.connect(save_as_csv)

        # Resize and show the dialog
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

        # Set up the delegate for the "Type" column
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
        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()
        
        # Existing buttons
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
        
        # Add the new "Graph Categorical" button
        self.graph_button = QPushButton('Graph Categorical')
        self.graph_button.setStyleSheet("background-color: #3F51B5; color: #FFFFFF;")
        self.graph_button.clicked.connect(self.show_graph_categorical_dialog)
        button_layout.addWidget(self.graph_button)
        
        layout.addLayout(button_layout)

        # Metadata display
        self.metadata_display = QLabel('')
        self.metadata_display.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.metadata_display)

        # Create vertical layout for metadata controls
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

        print(f"Add noise triggered with type: {noise_type}") 
        # Get columns of type "Continuous"
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
        # Configure tree view
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
        selected_columns = self.get_selected_columns()
        if selected_columns:
            sensitive_attr = self.get_sensitive_attribute()
            try:
                # Calculate the number of unique rows
                value_counts = self.data[selected_columns].value_counts()
                num_unique_rows = len(value_counts[value_counts == 1])
                
                # Calculate the total number of rows
                total_rows = len(self.data)
                
                # Calculate the total number of columns and the number of selected columns
                total_columns = len(self.data.columns)
                num_selected_columns = len(selected_columns)
                
                # Calculate k-anonymity and l-diversity
                k_anonymity = self.calculate_k_anonymity(selected_columns)
                l_diversity = self.calculate_l_diversity(selected_columns, sensitive_attr) if sensitive_attr else None
                
                # Prepare the result text
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
        grouped = self.data.groupby(selected_columns).size().reset_index(name='counts')
        return grouped['counts'].min()

    def calculate_l_diversity(self, selected_columns, sensitive_attr):
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
        if self.data is not None:
            preview_data = self.data.head(10)
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(preview_data.columns)
            for row in preview_data.itertuples(index=False):
                items = [NumericStandardItem(str(item)) if isinstance(item, (int, float)) else QStandardItem(str(item)) for item in row]
                model.appendRow(items)
            self.preview_table.setModel(model)
            self.preview_table.setMaximumHeight(200)  # Set a maximum height for the preview table
            self.update_column_dropdown()
            self.stacked_widget.setCurrentWidget(self.preview_page)
        else:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")

    def load_metadata(self):
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
        column_name = self.column_dropdown.currentText()
        if column_name in self.metadata:
            metadata_info = self.metadata[column_name]
            self.metadata_display.setText(f"Metadata for {column_name}:\n{json.dumps(metadata_info, indent=4)}")
        else:
            QMessageBox.warning(self, "No metadata available for the selected column.")

    def round_values(self):
        # Get continuous columns
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
        self.stacked_widget.setCurrentWidget(self.main_page)

    def show_preview_page(self):
        self.stacked_widget.setCurrentWidget(self.preview_page)

    def show_hierarchical_page(self):
        self.stacked_widget.setCurrentWidget(self.hierarchical_page)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileAnalyzer()
    window.show()
    sys.exit(app.exec())
