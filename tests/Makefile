.PHONY : help viewprofiles clean $(wildcard *.dat)
help :
	@echo "clean       	: Remove auto-generated files."
	@echo "test		: Run tests."
	@echo "viewprofiles	: View all *.dat profile files."

now=$(shell date +%d-%m_%H-%M-%S)

test:
	rm -f *.pkl
	python3 -m pytest

viewprofiles: $(wildcard *.dat)

$(wildcard *.dat):
	$(eval name=$(patsubst %64,%,$(basename $(notdir $@))))
	gprof2dot -f pstats $@ | dot -Tpng -o profile_$(name)_$(now).png
	xdg-open profile_$(name)_$(now).png

clean:
	rm -f *.pkl
	rm -f -r __pycache__
	rm -f *.dat
	rm -f profile_*.png
	rm -f *.gz
	rm -f *.gv.png
	rm -f *.gv.pdf
	rm -f *.gv