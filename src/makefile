all: black tst
black:
	black --check *.py
fmt:
	black *.py

tst:
	./loadshed.py

dbg:
	ipdb3 loadshed.py
