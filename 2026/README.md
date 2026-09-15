# Probability course, 2026 material

Beamer decks and homework for lectures 5 and 6, written in the notation of the
2025 deck (probability space (Ω, 𝓕, ℙ), events as subsets of Ω, shorthand
ℙ(X ∈ A) defined once and then used).

| File | Content | Slides / pages |
|---|---|---|
| `refresher.pdf` | Refresher shown at the start of lecture 5: random variables, indicators, cdf, pmf, pdf, joint pdf, expectation, conditional probability, conditional density | 12 |
| `condexp.pdf` | Lecture 5: conditional expectation, built on the two-dice table (rows are the events {Y = y}) | 43 |
| `entropy.pdf` | Section 2: information, entropy, codes, joint and conditional entropy, mutual information, cross-entropy, relative entropy, models of text | 73 |
| `stochproc.pdf` | Lecture 6: stochastic processes, Bernoulli process and random walk, Brownian motion, risk of ruin, Markov chains | 96 |
| `quiz03.pdf` | Quiz 3 (homework for lectures 5 and 6): Part A conditional expectation, Part B entropy, Part C stochastic processes | 11 |
| `quiz03_solutions.pdf` | Quiz 3 with solutions | 23 |

Each deck is `<name>.tex` (wrapper) plus `<name>-frames.tex` (the slides).
`preamble.tex` holds the shared theme and the `exercise` block;
`refresher-macros.tex` holds the notation macros. The quiz is one problem
source per part; `quiz03.tex` hides the solutions and `quiz03_solutions.tex`
shows them (via the `comment` package).

## Building

```sh
make            # all PDFs
make condexp.pdf
make clean
```

## Reviewing

`python3 review/serve.py` serves http://localhost:8765 with every deck's
slides beside a comment box. Comments autosave to `review/comments-<deck>.md`
and are committed on blur; "Finish pass" archives them under
`review/passes/<deck>/` and clears the boxes. Earlier passes appear collapsed
under each slide.

## Conventions

- Every function is introduced with domain and codomain.
- One grey italic sentence of plain English after each definition or theorem, nothing more.
- Three to five slides per concept; slides are split, never trimmed, when they overflow.
- Examples are chosen to be hard without the concept being taught.
- An exercise battery follows each concept; answers are on the last slides of the deck; the homework pointer sits in the exercise slide's title.
