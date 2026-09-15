# Build every deck and quiz. Requires TeX Live (latexmk, pdflatex).
DECKS   = refresher condexp entropy stochproc
QUIZZES = quiz03 quiz03_solutions
PDFS    = $(addsuffix .pdf,$(DECKS) $(QUIZZES))

all: $(PDFS)

%.pdf: %.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error $<

refresher.pdf: refresher-frames.tex preamble.tex refresher-macros.tex
condexp.pdf:   condexp-frames.tex   preamble.tex refresher-macros.tex
entropy.pdf:   entropy-frames.tex   preamble.tex refresher-macros.tex
stochproc.pdf: stochproc-frames.tex preamble.tex refresher-macros.tex
quiz03.pdf quiz03_solutions.pdf: quiz03-condexp.tex quiz03-entropy.tex quiz03-stochproc.tex refresher-macros.tex

review:
	python3 review/serve.py

clean:
	latexmk -C
	rm -f *.nav *.snm *.vrb comment.cut

.PHONY: all review clean
