# dlg_perl_scrolllist.pl --
#
# UI generated by GUI Builder v1.0on 2002-09-12 10:44:06 from:
#	C:/p4/depot/main/Apps/Komodo-devel/src/samples/dlg_perl_scrolllist.ui
# This file is auto-generated.  It may be modified with the
# following restrictions:
#	1. Only code in 'sub' functions is round-tripped.
#

# Declare the package for this dialog
package dlg_perl_scrolllist;

# FindBin locates the real dir location of this script
use FindBin qw($RealBin);
use lib $RealBin;
eval 'require "dlg_perl_scrolllist_ui.pl";';
die $@ if $@;

# insertButton_command --
#
# Here we create a command that handles the 
# -command option for the widget insertButton
#
# ARGS:
#    
#
sub insertButton_command {
    $myListbox->insert("end", rand());
};


# Standalone Code Initialization

if (defined &dlg_perl_scrolllist::userinit) {
dlg_perl_scrolllist::userinit();
}

our($top) = MainWindow->new();
$top->title("dlg_perl_scrolllist");
dlg_perl_scrolllist::ui($top);

if (defined &dlg_perl_scrolllist::run) {
dlg_perl_scrolllist::run();
}

Tk::MainLoop();

1;
