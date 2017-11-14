
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

In case you are using conda to install the packages, you might need to add the **paulscherrerinstitute** channel to 
your conda config:

```
conda config --add channels paulscherrerinstitute
```

## Docker build
**Warning**: When you build the docker image with **build.sh**, your built will be pushed to the PSI repo as the 
latest cam_server version. Please use the **build.sh** script only if you are sure that this is what you want.

To build the docker image, run the build from the **docker/** folder:
```bash
./build.sh
```

Before building the docker image, make sure the latest version of the library is available in Anaconda.

**Please note**: There is no need to build the image if you just want to run the docker container. 
Please see the **Run Docker Container** chapter.

## Run Docker Container
To execute the application inside a docker container, you must first start it (from the project root folder):
```bash
docker run --net=host -it docker.psi.ch:5000/frontend_digitizers_calibration /bin/bash
```
