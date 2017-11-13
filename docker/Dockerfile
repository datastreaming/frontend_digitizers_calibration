FROM continuumio/miniconda3
RUN conda install -c paulscherrerinstitute frontend_digitizers_calibration && conda clean --all

ENV CFG_DIR /cfg

ADD cfg/ ${CFG_DIR}/