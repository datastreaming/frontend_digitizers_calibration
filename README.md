
# Frontend digitizers calibration
This library is meant to be a stream device for calibration of digitizers channels.

## Conda setup
If you use conda, you can create an environment with the frontend_digitizers_calibration library by running:

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
latest frontend_digitizers_calibration version. Please use the **build.sh** script only if you are sure that this is 
what you want.

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
docker run --net=host -it -v /YOUR_CONFIG_DIR:/configuration docker.psi.ch:5000/frontend_digitizers_calibration /bin/bash
```

**WARNING**: Docker needs (at least on OSX) a full path for the -v option.

Once inside the container, start the application by running (append the parameters you need.)
```bash
calibrate_digitizer
```

**Please note**: You need the calibration configuration (**Calibration configuration** chapter) in order to be 
able run this program.

## Calibration configuration

The production configurations are not part of this repository but are available on:
- https://git.psi.ch/controls_highlevel_applications/frontend_digitizers_calibration_configuration

You can download it using git:
```bash
git clone https://git.psi.ch/controls_highlevel_applications/frontend_digitizers_calibration_configuration.git
```

And later, when you start the docker container, map the configuration using the **-v** parameter of the docker 
executable.

## Deploy in production

Before deploying in production, make sure the latest version was tagged in git (this triggers the Travis build) and 
that the Travis build completed successfully (the new frontend_digitizers_calibration package in available in anaconda). 
After this 2 steps, you need to build the new version of the docker image (the docker image checks out the latest 
version of frontend_digitizers_calibration from Anaconda). 
The docker image version and the frontend_digitizers_calibration version should always match - 
If they don't, something went wrong.

### Production configuration
Login to the target system, where frontend_digitizers_calibration will be running. Checkout the production configuration 
into the **/git/** folder of on target system filesystem.

```bash
cd /
mkdir git
cd git
git clone https://git.psi.ch/controls_highlevel_applications/frontend_digitizers_calibration_configuration.git
```

### Setup the frontend_digitizers_calibration as a service
On the target system, copy all **docker/\*.service** files into 
**/etc/systemd/system**.

Then you need to reload the systemctl daemon:
```bash
systemctl daemon-reload
```

### Run the services
Using systemctl you then run all the services:
```bash
systemctl start [name_of_the_service_file_1].service
systemctl start [name_of_the_service_file_2].service
...
```

### Inspecting service logs
To inspect the logs for each server, use journalctl:
```bash
journalctl -u [name_of_the_service_file_1].service -f
```

Note: The '-f' flag will make you follow the log file.