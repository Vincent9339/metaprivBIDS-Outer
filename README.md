# metaprivBIDS

[![Documentation Status](https://readthedocs.org/projects/metaprivbids/badge/?version=latest)](https://metaprivbids.readthedocs.io/en/latest/?badge=latest)




This Python build tool enables a given user to calculate a variety of different data privacy metrics on tabular data from a user interface. 

# Methods

#### Assesing Privacy risk: 

- K-anonymity [^1]
- ℓ-diversity [^2]
- Sample Unique Detection Algorithm (SUDA) [^3]
- Privacy Information Factor (PIF) [^4]

[^1]: Sweeney, L. (2002). k-Anonymity: A Model for Protecting Privacy. *International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems*, 10(05), 557-570.
[^2]: Machanavajjhala, A., Kifer, D., Gehrke, J., & Venkitasubramaniam, M. (2007). ℓ-Diversity: Privacy Beyond k-Anonymity. *ACM Transactions on Knowledge Discovery from Data (TKDD)*, 1(1), 3-es.
[^3]: Elliott, M. J., & Skinner, C. J. (2000). Identifying population uniques using limited information. *Proceedings of the Annual Meeting of the American Statistical Association*.
[^4]: Information Governance ANZ. (2019). *Privacy Impact Assessment eReport.* [Link](https://www.infogovanz.com/wp-content/uploads/2020/01/191202-ACS-Privacy-eReport.pdf)


#### Mitigating Privacy Risk

- Noise addition
- Field generalisation
- Rounded Approximation 


# Input data format

Input can be in either CSV or TSV format. 
For meta information an option of load of json file is possible. 

# Software installation

### Option 1 
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

### Option 2 

 In the event of permission issues for system dependent files, you might want to set the pkgs_dirs option in Conda's configuration to use a directory that is writable by you.
 
```console 
conda config --add pkgs_dirs ~/conda_pkgs
```
Creates the enviroment. 

```console 
conda create --name venv python=3.x.x
```

Activates the environment. 

```console
conda activate venv 
```

Graphviz requires system level dependencies and might need to be installed with 

```console
conda install graphviz pygraphviz
```

if not avaliable. 

You can then install metaprivBIDS by cloning the git respository.

```console
git clone https://github.com/CPernet/metaprivBIDS.git
```


# Dependencies

To execute the program make sure all dependencies from pyproject.toml is avalible in a python 3.7 enviroment as stated in the software installation. 
This can be done by first ```cd``` into the MetaprivBIDS directiory and then running

```console
pip install -e . 
```

# Usage

To execute the program run from command line 

```console
metaprivBIDS
```

prompting the program to start.



## Related tools

- https://github.com/JiscDACT/suda/blob/main/test/test_suda.py






