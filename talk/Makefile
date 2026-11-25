# Run "make -C talk" from the repository root.
LATEXMK = latexmk -lualatex -halt-on-error -interaction=nonstopmode -outdir=build
.PHONY: all slides notes
all: slides notes

slides:
	$(LATEXMK) -jobname=talk main.tex
	mkdir -p ../output/talk
	cp build/talk.pdf ../output/talk/talk.pdf

notes:
	$(LATEXMK) -jobname=talk_notes -usepretex='\def\WithNotes{1}' main.tex
	mkdir -p ../output/talk
	cp build/talk_notes.pdf ../output/talk/talk_notes.pdf
