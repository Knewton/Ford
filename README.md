# Ford

## What is it?

Ford is a web application development and compilation tool. It is designed to
vastly simplify the creation and distribution of framework agnostic
applications. The tool uses JSON manifest files to describe the composition
and dependencies of the Javascript resources used to build your application.
The main focus of this tool is to reduce or remove the common headaches
associated with creating and using modular open-source code within your front
end tools.

## The latest version

This project is being actively maintained and developed by the educational
technology company [Knewton](http://www.knewton.com/). The most up-to-date
stable version of this code can be found at: http://github.com/Knewton/Ford

## Documentation

The documentation available as of the date of this release is included in
Markdown format in the docs/ directory. This documentation is available online
at: https://github.com/Knewton/Ford/blob/master/docs/index.md

## Installation

These instructions are reproduced within `INSTALL.md`.

### Requirements

* Python 2.6+
* Ruby 1.8.7+
* RubyGems 1.3.7+

### Web installation (Recommended)

Ford can be quickly and effortlessly installed or updated over the web with
the following cURL:

    curl https://raw.github.com/Knewton/Ford/master/web_install.sh | sh

### Source installation

Ford can be installed and updated from source by running:

    git clone github.com:/Knewton/Ford
    cd Ford
    bin/install_dependencies.sh
    sudo ./setup.py install
    ford upgrade
    ford import

### Updating the tool

Once ford has been installed successfully, you can keep it up to date simply by
running:

    ford latest

### Important note about Gems

Ford uses Ruby and RubyGems for [Juicer](http://cjohansen.no/en/ruby/juicer_a_css_and_javascript_packaging_tool)
which is used to compile a Ford project into a single javascript and a single
css file. However, depending on how you configured your local Gem install, the
gem may or may not be on your path once you've installed!

Depending on what version of Ruby and Gems you're using, and depending on if
you have already done this or not, you may need to add a line to `~/.bashrc` or
`~/.bash_profile` to proceed. Once you have completed the installation, try and
run:

    which juicer

If the command is not found, you will need to put your Ruby gems on your PATH.
The following destination will differ depending on the configuration of your
system, but you should only need add:

    export PATH=$PATH:/home/$YOUR_HOME_DIR/.gem/ruby/1.8/bin

or, if your gems are installed system-wide:

    export PATH=$PATH:/usr/lib/ruby/gems/1.8/bin

## Licensing

Ford is dual licensed and free of use providing you follow the criteria set
forth in at least one of the two licenses (of your choice).

  MIT: http://www.opensource.org/licenses/mit-license.php
  GPLv3: http://www.opensource.org/licenses/gpl-3.0.html

The license text is available in `LICENSE.md`.

## Contributions

Contributions are always welcome and encouraged!

If you would like to contribute to this project, please contact the current
project maintainer, or use the Github pull request feature.

Current project maintainer: [Eric Garside](https://github.com/garside)

## Support

This program is provided as-is for no cost. Bugs and feature requests can be
submitted through its [issue tracker](https://github.com/Knewton/Ford/issues).

This project is actively maintained; bugs will be addressed based on
their severity and impact. Good reproduction steps are the best way to get a
bug noticed and fixed quickly!

