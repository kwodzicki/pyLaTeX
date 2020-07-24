# pyLaTeX

This package was originally written to be a LaTeX to DOCX converter; however, it has grown to include many other options:

  - Convert LaTeX to DOCX files with cross-references
  - Create tracked-changes file given a git branch name
  - Auto-compile document on changes with watchdog


## Best Practices

### Root LaTeX File

You can specify the root TeX file to compile by using the `% !TEX root = /path/to/root` variable at the top of a LaTeX file.
This is useful if you have a multifile document, such as a book or thesis.
Defining the `!TEX root` variable allows the compiler to location and compile the correct document as any 'child' documents will not have the proper `\documentclass` command.

### Inline Math

When writing inline math, it is best to use the `\( \)` notation.
While use of `$ $` notation works in basic cases, there tends to be issues with more complex equations.
For example, instead of writing

    The equation for this circle is $5 = x^2 + y^2$.

one would instead write

    The equation for this circle is \(5 = x^2 + y^2\).

