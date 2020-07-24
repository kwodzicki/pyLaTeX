# pyLaTeX

This package was originally written to be a LaTeX to DOCX converter; however, it has grown to include many other options:

  - Convert LaTeX to DOCX files with cross-references
  - Create tracked-changes file given a git branch name
  - Auto-compile document on changes with watchdog


## Best Practices

### Inline Math

When writing inline math, it is best to use the `\( \)` notation.
While use of `$ $` notation works in basic cases, there tends to be issues with more complex equations.
For example, instead of writing

    The equation for this circle is $5 = x^2 + y^2$.

one would instead write

    The equation for this circle is \(5 = x^2 + y^2\).

