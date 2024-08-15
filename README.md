# Enginesys

Enginesys is software for financial portafolio analisys.


## Features

Enginesys aims to support numerous analisys, including:

- [ ] Portfolio management
- [ ] Seasonality analisys
- [ ] Historical analisys


## Installation

The current recommended way to install enginesys is from source.

### From source
```python
git clone https://github.com/VIP1Alliance/enginesys.git
cd enginesys
python -m pip install -e .
```

### Direct (master)

Install the package directly from the repository as follows:

```python
pip install git+https://<your_key>@github.com/VIP1Alliance/enginesys.git

```

### Upgrade
```python
cd enginesys
python -m pip install --upgrade -e.
```

## Addition and Maintenance of Code
Before adding or maintaining (fixing bugs, improving code quality, better documenting existing functionalities, adding missing unit tests, etc.) code to Enginesys, it must have good documentation, unit tests, performance benchmarks, and correct code style.

### Unit Tests
Create unit tests that push the code to its limits. This is to ensure a certain level of confidence that your code runs correctly. Use the [Unit test](https://docs.python.org/3/library/unittest.html) and/or [Pytest](https://docs.pytest.org/en/stable/).

### Performance Benchmarks
Monitor execution times. Not all code needs to contain a benchmark, but it should.

### Documentation
Having complete and clear documentation is essential forV being able to find and understand the code. Documentation for individual functions and classes should include a basic description, type and meaning of all parameters and return values, and examples of use if necessary (see NumPy style documentation).

### Code Style
A uniform code style makes it easy for others to read your code. Enginesys follows the standard Python style guide, [PEP8](https://peps.python.org/pep-0008/), with the exception of the maximum recommended line length, which is set to a maximum of 79 characters. Always consider reducing complexity and increasing readability in your written code.

### Checklist Before Submitting a PR
- Are there unit tests covering the functionality of the code?
- Do all unit tests pass locally?
- Do the relevant functions have documentation?
- Is the code style correct?


## To do


## Usage example

### The Filter module

The Filter module, allows you to prepare the (financial) sectors where is recommended open a position:

```python
import os
import sys
import logging
import pandas as pd

from enginesys import FilterThreshold

BASE_DIR = os.path.abspath("../")
if BASE_DIR not in sys.path:
    sys.path = [BASE_DIR] + sys.path

# read and write paths (place the correonded paths to your directories)
dir_models = BASE_DIR + "/enginesys_test/GEA/data/input/Modelos"
dir_output = BASE_DIR + "/enginesys_test/GEA/data/output/"

models = [f.name for f in os.scandir(dir_models) if f.is_dir()]
backtesting = [
for model in models:
    logging.info(f"Processing model: {model}")
    dir_model = os.path.join(dir_models, model
    all_files = []
    for root, _, files in os.walk(dir_model):
        for file in files:
            if file.endswith('.xlsx'):
                all_files.append(os.path.join(root, file)
    for file_path in all_files:
        try:
            # read data
            df = pd.read_excel(file_path)
            # instance object
            filter = FilterThreshold(df)
            # apply filter
            selected_df = filter.process_file()
            if not selected_df.empty:
                backtesting.append(selected_df
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}"
if backtesting:
    backtesting_df = pd.concat(backtesting, axis=0).reset_index(drop=True)
    # filter sectors
    filter_sectors = filter.format_data(backtesting_df)
else:
    logging.warning("No backtesting data to save.")
```

