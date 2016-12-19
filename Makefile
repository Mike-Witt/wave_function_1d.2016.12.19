cython:
	python build_cython.py build_ext --inplace > build_cython.out 2>&1

clean:
	rm -rf build *.c *.so *.pyc *.out *.prof
