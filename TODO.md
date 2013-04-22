# Ford

## Project management tasks

* Write project documentation
* Create example code
* Be more explicit in the README with regards to community commit process.
* Create a github pages site for the documentation.
* Make the documentation site a working example of the builder.

## Software update tasks

### Defects to fix

* Address the confusing, bulky, and over-engineered update logic for images.
* Refactor `ford/project.py`, breaking it up into more sensible modules.
* Implement the manifest update process for templates, instead of `setuptools`.
* Fix the update process to no longer forcibly create modified directories.
* Revisit the basic mechanics of the update process in general:
    - Should missing files always be copied?
    - Should missing directories always be copied?
    - Should all project files always be updated?
* Update the stdout for update/build. (It's terrible; like really bad.)

### Feature enhancements to add

* Add command line arguments to do common tasks, like:
    - Creating a new project resource and add it to the manifest.
    - Create external manifests. (Might be an interactive process?)
    - Build headless projects.
    - Compile libraries for individual release/distribution
