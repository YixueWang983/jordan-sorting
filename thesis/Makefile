LATEXMK ?= latexmk

.PHONY: pdf clean distclean

pdf:
	mkdir -p build/texmf-var build/texmf-cache
	TEXMFVAR="$(CURDIR)/build/texmf-var" \
	TEXMFCACHE="$(CURDIR)/build/texmf-cache" \
	$(LATEXMK) main.tex

clean:
	$(LATEXMK) -c main.tex

distclean:
	$(LATEXMK) -C main.tex
