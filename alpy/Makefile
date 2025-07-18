t00:
	./app.py ../t00.al

t03:
	./app.py ../t03.al

test:
	(cd ../tests; make apy)

grammar:
	@grep '//-' parser.c | grep -v 'Note:' | sed 's/\/\/-//;s/^ //'

clean:
	rm -rf __pycache__
	(cd ../tests; make clean)
