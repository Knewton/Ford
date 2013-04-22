# Ford

## Installation

### Requirements
* Python 2.6+
* Ruby 1.8.7+
* RubyGems 1.3.7+

### Web installation (Recommended)
Once the required software has been installed, Ford can be quickly and
effortlessly installed or updated over the web with the following cURL:

    curl https://raw.github.com/Knewton/Ford/master/web_install.sh | sh

### Source installation
Once the required software has been installed, Ford can be installed and
updated by running:

    git clone github.com:/Knewton/Ford
    cd Ford
    bin/install_dependencies.sh
    sudo ./setup.py install
    ford upgrade
    ford import

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
