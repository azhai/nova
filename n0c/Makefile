test001:
	./app.py -d ../tests/test001.al

test:
	(cd ../tests; make n0c)

grammar:
	@grep '//-' parser.py | grep -v 'Note:' | sed 's/\/\/-//;s/^ //'

clean:
	rm -rf __pycache__
	(cd ../tests; make clean)
