This folder is used to change css(attribute "StyleSheet") of widgets on runtime.

Stylesheet of widgets is changed either by the widgets "objectName" attribute or
its class(type).
Each txt file must be located in this directory("\css") and the format of the files
is either "class_%CLASS_NAME_%.txt" or "%OBJECT_NAME%.txt".
For example, to set css stylesheet for class 'MainWindow', you can:
    - create css file 'class_MainWindow.txt'
    - create css file 'main_window.txt'

The stylesheet is applied by clicking button "Load CSS(development mode)" in
the main window's toolbar.

NOTE: App mode "DEVELOPMENT_MODE" must be activated, in module 'config', for this
feature to be available.
