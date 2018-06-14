FROM continuumio/miniconda3
RUN conda install -c paulscherrerinstitute frontend_digitizers_calibration && conda update zeromq pyzmq mflow pyepics && conda clean --all && apt-get update
