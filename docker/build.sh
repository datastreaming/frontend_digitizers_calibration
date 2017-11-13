#!/bin/bash
VERSION=0.0.3
docker build --no-cache=true -t docker.psi.ch:5000/frontend_digitizers_calibration .
docker tag docker.psi.ch:5000/frontend_digitizers_calibration docker.psi.ch:5000/frontend_digitizers_calibration:$VERSION
docker push docker.psi.ch:5000/frontend_digitizers_calibration:$VERSION
docker push docker.psi.ch:5000/frontend_digitizers_calibration
