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
pip install -e . 
```

# Usage

To execute the program run from command line 

```console
metaprivBIDS
```

prompting the program to start
# NIMH Use Case 

A comprehensive dataset characterizing healthy research volunteers in terms of clinical assessments, mood-related psychometrics, cognitive function neuropsychological tests, structural and functional magnetic resonance imaging (MRI), along with diffusion tensor imaging (DTI), and a comprehensive magnetoencephalography battery (MEG).[^1]

[^1]: [The National Institute of Mental Health (NIMH) Intramural Healthy Volunteer Dataset.](https://openneuro.org/datasets/ds004215/versions/1.0.3)


The dataset consists of 30 sub-dataset including measurements such as blood panels, intelligence, health rating ect. for the examle the focus is on the demographical aspect of the dataset (demographics.tsv)[^2] as these poses the largest risk for re-identification of research subjects.

[^2]: [Demographics File Download Link.](https://openneuro.org/datasets/ds004215/versions/1.0.3/file-display/phenotype:demographics.tsv)

## Main Page 
Running the 

```console
metaprivBIDS
```

prompts the program to start and opens up the main page of metaprivBIDS. within the main page we then have a variety of data handling options. 

### **Load TSV/CSV File:** 

Prompts the user with a window to select files avalible on their device. 

After the selected data has been loaded, the user is then able to select columns in the **Select Columns** field by simply clicking on the column name. For the NIMH data 11 columns has been selected as quasi-identifiers and by such, a potential risk for data privacy with an adversary using these to re-identify specfific participants.

>[!NOTE]
>Selecting which data field qualify as quasi-identifers is a subjective matter but is broadly defined as "A variable that can be used to identify an individual through association with another variable."


The **Unique Value** field is sum of combined unique values in the column. So for this example the Age variable has 67 unique associated ages. The **Type** Field indicates if a variable is categorical e.g. Female Male or continous e.g. Age 20,21,22,23 ect. In case the user want to change a categorical variable to continuous or vice versa they double click on the cell in the type field and a drop down menu will appear. 
The **Select Sensitive Attribute** is an option associated with L-diversity. 

### **Privacy Calculation:** 

Clicking on the Privacy Calculation button after selection of chosen fields, computes the metrics seen in the lower left corner. Here L-diversity is **None** indicating that no sensitive attribute has been selected for this specific use case. Importanly we notice that 997 rows are unique meaning that if an adversary were to have background knowledge of a specific invidual or be in posession of external data that could be linked to this dataset (linkage attack) he/she would with high probability be able to uniquely identify a participant. 

<img width="978" alt="Screenshot 2024-08-30 at 15 00 04" src="https://github.com/user-attachments/assets/11cab63a-b029-4573-9685-0946e4687422">

This is also indicated by **K-Anonymity**, a privacy-preserving technique ensuring that each record in the dataset is indistinguishable from at least k-1 other records, being equal to 1.
K-anonymisation gets improved by generalising the data, thus increasing K's value, ensuring that every participant is in at least k-1 other records. 



>[!NOTE]
>Determining the value of K is up to the individual user. Higher values of k imply a lower probability of re-identification, but also more distortion to the data hence a lower utility. 



### **Variable Optimization:** 

The Variable Optimization button calculates the metrics found in the second window below the initial load of data window in the top. Here the **Quasi Identifer** field display the fields chosen. The **Unique Rows After Removal** fields indicates how many unique rows would be left after removing the specfic field from the dataset completely. The **Difference** is calculated by the the *Unique rows - Unique Rows After Removal*. The **Normalized** field is calculated by $\frac{\text {Difference}}{\text{Unique Value}}$,  giving the normalized value score for the individual field.

### **Combined Column Contribution**

The combined column contribution button computes the normalized value score for the all possible combination of combined fields, providing an overview of which columns in combination results in the highest number of unique rows normalized based on the columns unique values.

##  SUDA Compute

Computes the "Special unique" using the Special Uniques Detection Algorithm (SUDA).
The principle behind this concept is that a microdata record that is unique within a dataset based on broader, less detailed information is more vulnerable to re-identification than a record that is unique based on finer, more detailed information. A specific example of this occurs when a record is unique based on a set of variables, K, and remains unique on a subset of K. Such a record is referred to as a "special unique" with respect to the variable set K.

In order to estimate record-level disclosure risks, SUDA scores can be used in combination with the Data Intrusion Simulation (DIS) metric 

$$
\text { Data Intrusion Simulation DIS: } =\frac{U \times S}{U \times S+P \times(1-S)}
$$


U: Number of unique records in the sample.
S: Sampling fraction (percentage of data removed and replaced).
P: Number of records in pairs (records that have duplicates or are not unique).



The DIS-SUDA method allocates the file-level risk assessed by the DIS metric across individual records based on their SUDA scores. 
By calibrating the SUDA scores against this consistent measure, it generates DIS-SUDA scores, which reflect the disclosure risk at the record level.

Computing the metric on the NIMH dataset would result in the display below

<img width="790" alt="Screenshot 2024-09-03 at 12 11 36" src="https://github.com/user-attachments/assets/eeb6ae58-7d45-4cf0-be87-c5d518d2f4fd">

###### Elliot, M., Manning, A., Mayes, K., Gurd, J. and Bane, M., 2005. SUDA: A program for detecting special uniques. Proceedings of the Joint UNECE/Eurostat Work Session on Statistical Data Confidentiality, pp.353-362.


## Privacy Information Factor (PIF)

Pushing the privacy Information Factor button and then the Compute CIG button prompts the window below

<img width="966" alt="Screenshot 2024-09-03 at 12 57 44" src="https://github.com/user-attachments/assets/d2302d56-d3fa-475a-8e92-27d806c1f5d5">

The PIF tool enables the user to compute the Cell Information Gain (CIG) through the KL-divergence between the distribution of values of the whole dataset (the features' priors) and the distribution of a feature values given all remaining features' values (posterior).


$$
\begin{aligned}
D_{\mathrm{KL}}(P \| Q) & =-\sum_{x \in \mathcal{X}} p(x) \log q(x)+\sum_{x \in \mathcal{X}} p(x) \log p(x) \\
& =\mathrm{H}(P, Q)-\mathrm{H}(P)
\end{aligned}
$$

P(x): is the posterior distribution (the actual distribution of values given the context).
Q(x): the prior distribution (the expected distribution of values without knowing the context).

Quantifies  how "surprising" or "unexpected" the value of a feature is, given everything else we know about the person. If the value is highly unexpected, it provides more information, and thus, the information gain (CIG) is higher.
After computation of the CIG values the **RIG** field is calculated by summation of the individual cell in the given row, the user is then able to quantify which rows pose the highest risk of reidentifcation. 

Likewise we can compute the Field Information Gain (FIG) and visualise it through the **Generate CIG Heatmap** button. 


<img width="769" alt="Screenshot 2024-09-03 at 13 56 54" src="https://github.com/user-attachments/assets/53295987-bac9-47bc-aac1-4dca3715613e">





## Preview Data  
Takes the user to a different page where an example of the data is avilable along with different anonymisation tool as well as an option to load in json files for metadata specifications. 


<img width="961" alt="Screenshot 2024-09-04 at 11 13 30" src="https://github.com/user-attachments/assets/2834e65c-f6d1-49c4-91a7-b6139174c317">

The graph categorical button enables the user to keep track of the combined variables from different columns so the user is able track changes. Below is an example of 1,3,4,5 and 6 being combined into a new variable Single. 

<img width="1036" alt="Screenshot 2024-09-04 at 11 17 22" src="https://github.com/user-attachments/assets/dc8b03ff-5591-4021-bbdf-3cb4651df816">


## Related tools

- https://github.com/JiscDACT/suda/blob/main/test/test_suda.py






