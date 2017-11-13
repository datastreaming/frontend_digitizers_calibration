
# frontend_digitizers_calibration
Arturo will fill this out.

## Conda setup
If you use conda, you can create an environment with the frontend_calibration library by running:

```bash
conda create -c paulscherrerinstitute --name <env_name> frontend_digitizers_calibration
```

After that you can just source you newly created environment and start using the library.

## Local build
You can build the library by running the setup script in the root folder of the project:

```bash
python setup.py install
```

or by using the conda also from the root folder of the project:

```bash
conda build conda-recipe
conda install --use-local frontend_digitizers_calibration
```

### Requirements
The library relies on the following packages:

- python
- bsread
- pyepics
- matplotlib

In case you are using conda to install the packages, you might need to add the **paulscherrerinstitute** channel to 
your conda config:

```
conda config --add channels paulscherrerinstitute
```
