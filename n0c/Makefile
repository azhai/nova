t00:
	./app.py ../t00.al

t03:
	./app.py ../t03.al

test:
	(cd ../tests; make n0c)

grammar:
	@grep '//-' parser.py | grep -v 'Note:' | sed 's/\/\/-//;s/^ //'

clean:
	rm -rf __pycache__
	(cd ../tests; make clean)
