################################################################
#  Makefile
#
#  LgEval
#  Feb 8, 2022 - R. Zanibbi
#################################################################

all: conda

# Install python environment for LgEval
conda:
	./install


# 'make conda-remove' - remove LgEval conda environment
conda-remove:
	conda env remove -n lgeval

	
