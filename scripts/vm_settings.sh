#!/bin/bash

sysctl -w vm.max_map_count=800000
sysctl -w fs.file-max=300000