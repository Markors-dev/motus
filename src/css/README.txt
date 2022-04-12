This folder is used to change css(attribute "StyleSheet") of widgets on runtime.

Stylesheet of widgets is changed either by the widgets "objectName" attribute or
its class(type).
Each txt file must be located in this directory("\css") and the format of the files
is either "class_%widget.__class__.__name__%.txt" or "%objectName%.txt".
The stylesheet is applied by clicking button "Load CSS(development mode)" in
the main window's toolbar.

NOTE: App mode "DEVELOPMENT_MODE" must be activated, in module 'config', for this
feature to be available.
