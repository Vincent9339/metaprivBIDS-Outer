# metaprivBIDS

This Python build tool enables a given user to calculate a variety of different data privacy metrics on tabular data from a user interface.  

# Input data format

Input can be in either CSV or TSV format. 
For meta information an option of load of json file is possible. 

# Software installation

The metaprivBIDS software runs on multiple platforms (e.g. Linux, MacOS, Windows) that have a Python 3 installation.
It is recommended (but not required) to first create a virtual environment.

```console 
python -m venv venv
source venv/bin/activate
```

You can then install metaprivBIDS by cloning the git respository.

```console
git clone https://github.com/CPernet/metaprivBIDS.git
```

# Dependencies

To execute the program make sure all dependencies from pyproject.toml is avalible in a python 3.7 enviroment. 
This can be done by running

```console
pip install .
```

# Usage

To execute the program run from command line 

```console
python metaprivBIDS.py
```

# NIMH Use Case 

A comprehensive dataset characterizing healthy research volunteers in terms of clinical assessments, mood-related psychometrics, cognitive function neuropsychological tests, structural and functional magnetic resonance imaging (MRI), along with diffusion tensor imaging (DTI), and a comprehensive magnetoencephalography battery (MEG).[^1]

[^1]: [The National Institute of Mental Health (NIMH) Intramural Healthy Volunteer Dataset.](https://openneuro.org/datasets/ds004215/versions/1.0.3)


The dataset consists of 30 sub-dataset including measurements such as blood panels, intelligence, health rating ect. for the examle the focus is on the demographical aspect of the dataset (demographics.tsv)[^2] as these poses the largest risk for re-identification of research subjects.

[^2]: [Demographics File Download Link.](https://openneuro.org/datasets/ds004215/versions/1.0.3/file-display/phenotype:demographics.tsv)

## Main Page 
Running the 

```console
python metaprivBIDS.py
```

prompts the program to start and opens up the main page of metaprivBIDS. within the main page we then have a variety of data handling options. 

#### **Load TSV/CSV File:** 

Prompts the user with a window to select files avalible on their device. 

After the selected data has been loaded, the user is then able to select columns in the **Select Columns** field by simply clicking on the column name. For the NIMH data 11 columns has been selected as quasi-identifiers and by such, a potential risk for data privacy with an adversary using these to re-identify specfific participants.

>[!NOTE]
>Selecting which data field qualify as quasi-identifers is a subjective matter but is broadly defined as "A variable that can be used to identify an individual through association with another variable."


The **Unique Value** field is sum of combined unique values in the column. So for this example the Age variable has 67 unique associated ages. The **Type** Field indicates if a variable is categorical e.g. Female Male or continous e.g. Age 20,21,22,23 ect. In case the user want to change a categorical variable to continuous or vice versa they double click on the cell in the type field and a drop down menu will appear. 
The **Select Sensitive Attribute** is an option associated with L-diversity. 

#### **Privacy Calculation:** 

Clicking on the Privacy Calculation button after selection of chosen fields, computes the metrics seen in the lower left corner. Here L-diversity is **None** indicating that no sensitive attribute has been selected for this specific use case. Importanly we notice that 997 rows are unique meaning that if an adversary were to have background knowledge of a specific invidual or be in posession of external data that could be linked to this dataset (linkage attack) he/she would with high probability be able to uniquely identify a participant. 

<img width="978" alt="Screenshot 2024-08-30 at 15 00 04" src="https://github.com/user-attachments/assets/11cab63a-b029-4573-9685-0946e4687422">

This is also indicated by **K-Anonymity**, a privacy-preserving technique ensuring that each record in the dataset is indistinguishable from at least k-1 other records, being equal to 1.
K-anonymisation gets improved by generalising the data, thus increasing K's value, ensuring that every participant is in at least k-1 other records. 



>[!NOTE]
>Determining the value of K is up to the individual user. Higher values of k imply a lower probability of re-identification, but also more distortion to the data hence a lower utility. 



#### **Variable Optimization:** 

The Variable Optimization button calculates the metrics found in the second window below the initial load of data window in the top. Here the **Quasi Identifer** field display the fields chosen. The **Unique Rows After Removal** fields indicates how many unique rows would be left after removing the specfic field from the dataset completely. The **Difference** is calculated by the the *Unique rows - Unique Rows After Removal*. The **Normalized** field is calculated by $\frac{\text {Difference}}{\text{Unique Value}}$,  giving the normalized value score for the individual field.

#### **Combined Column Contribution**

#### **SUDA Compute** 

Computes the "Special unique" using the Special Uniques Detection Algorithm (SUDA).
The principle behind this concept is that a microdata record that is unique within a dataset based on broader, less detailed information is more vulnerable to re-identification than a record that is unique based on finer, more detailed information. A specific example of this occurs when a record is unique based on a set of variables, K, and remains unique on a subset of K. Such a record is referred to as a "special unique" with respect to the variable set K.

###### Elliot, M., Manning, A., Mayes, K., Gurd, J. and Bane, M., 2005. SUDA: A program for detecting special uniques. Proceedings of the Joint UNECE/Eurostat Work Session on Statistical Data Confidentiality, pp.353-362.

#### **Preview Data:** 
Takes the user to a different page where an example of the data is avilable along with different anonymisation tool.

#### **Privacy Information Factor (PIF)**




# Related tools

- https://github.com/JiscDACT/suda/blob/main/test/test_suda.py






