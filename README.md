# Ford
A development and build tool for javascript applications.

# Installation
Directions for installing the build tool can be found in INSTALL.md

# Getting started

## Creating a new project
Zero to working in three commands.

    mkdir foo
    cd foo
    ford update

# Important notes
Only reference images once per css document! If you have:

foo.css
    a, b { background-image: url(blah.gif); }
    c, d { background-image: url(blah.gif); }

You must condense the rules into one common rule:
   a, b, c, d { background-image: url(blah.gif); }

This is due to a sensible requirement that Juicer not embed the base64 image
content more than once per document.




