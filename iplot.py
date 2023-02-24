#!/usr/bin/env python3
#
#  Copyright (c) 2014, Rolf Camps (rolf.camps@scarlet.be)

import roc_input as r_in
import roc_string as r_str
import roc_datetime as r_dt
import roc_cli
import plot

NO_INIT = "canvas not initiated"

canvas = None
    
    
###################################################
#
# Main cli
#
###################################################

def main():
    settings = {
        "prompt": "canvas> ",
    }
    commands = {
        "quit": quit,
        "init": init_canvas,
        "close": close_canvas,
        "activate": activate_canvas,
        "new": add_new_element_to_canvas,
        "def": define_new_var_or_function,
        "inject_code": inject_code,
        "info": show_info_cli,
    }
    r = roc_cli.CommandLineInterface(settings, commands).start()
    print('last cli return value: ', r)

def quit(split_line):
    return "Fin"
####
quit.def_t = (
    ("exit", "q"),
    "stop program",
    (quit, roc_cli.CommandLineInterface.stop),
)
    
def init_canvas(split_line):
    global canvas
    if canvas is not None:
        return "canvas already initiated"
    print("\ninit canvas")
    kw_d = dict()
    title = r_in.get_string(
        "title for canvas: ",
        empty=True, 
    )
    if title: kw_d['title'] = title
    canvas_is_chart = r_in.get_bool(
        "use canvas as single chart {}:",
        default=True,
    )
    if canvas_is_chart: kw_d['canvas_is_chart'] = canvas_is_chart
    canvas = plot.Canvas(**kw_d)
    canvas.instructions = [
        "import plot",
        "canvas = plot.Canvas({})".format(
            r_str.dict_as_funtion_argument_str(kw_d)),
    ]
    return "canvas initiated"
####
init_canvas.def_t = (
    ("i",),
    "initialise canvas",
    (init_canvas,),
)
    
def activate_canvas(split_line):
    global canvas
    if canvas is None:
        return NO_INIT
    canvas.draw()
    canvas.instructions.append(
        "canvas.draw()")
    print("activated canvas")
####
activate_canvas.def_t = (
    ("a",),
    "start gnuplot, show canvas",
    (activate_canvas,),
)
    
def close_canvas(split_line):
    global canvas
    if canvas is None:
        return
    canvas.close()
    canvas = None
    print("closed canvas")
####
close_canvas.def_t = (
    ("c",),
    "close canvas and remove settings",
    (close_canvas,),
)
    
def add_new_element_to_canvas(split_line):
    global canvas
    if canvas is None:
        return NO_INIT
    if len(split_line) < 2:
        add_new_element_to_canvas_cli()
        return
    element_type = split_line[1]
    if element_type in ("ds", "data_serie"):
        return add_data_serie_to_canvas(split_line)
    if element_type in ("vline", "vertical_line"):
        return add_vline_to_canvas(split_line)
    return "unknown element type: {}".format(element_type)
####
add_new_element_to_canvas.def_t = (
    ("n",),
    "add new element to canvas",
    (add_new_element_to_canvas,),
)

def inject_code(split_line):
    global canvas
    a = input("code: ")
    a +='\n'
    canvas.send(a)
####
inject_code.def_t = (
    ("ic",),
    "inject code",
    (inject_code,)
)

def define_new_var_or_function(split_line):
    if len(split_line) < 2:
        return define_cli()
    define_type = split_line[1]
    if define_type in ("var", "v"):
        return define_variable(split_line)
    return "unknown define type: {}".format(define_type)
####
define_new_var_or_function.def_t = (
    ("d",),
    "define variable or function",
    (define_new_var_or_function,),
)
   
###################################################
#
# add new elements cli
#
###################################################

def add_new_element_to_canvas_cli():
    settings = {
        "cli_start_mss": False,
        "prompt": "canvas - ad_new_element> ",
    }
    commands = {
        "abort": abort,
        "data_serie": add_data_serie_to_canvas,
        "vertical_line": add_vline_to_canvas,
    }
    return roc_cli.CommandLineInterface(settings, commands).start()

def add_data_serie_to_canvas(split_line):
    global canvas
    ds_dict = read_ds_parameters()
    canvas.add_data_serie(**ds_dict)
    canvas.instructions.append(
        "canvas.add_data_serie({})".format(
            r_str.dict_as_funtion_argument_str(ds_dict)))
    return "add a data serie"
####
add_data_serie_to_canvas.def_t = (
    ("ds",),
    "add data serie to canvas",
    (add_data_serie_to_canvas, roc_cli.CommandLineInterface.stop),
)

def add_vline_to_canvas(split_line):
    global canvas
    id_ = r_in.get_string('line id: ')
    if r_in.get_bool('time serie on x-aś {}: ', default=False):
        x_value = r_in.get_datetime(
             "set verical line @:",
             r_dt.ISO_8601_DATETIME_FORMAT,
        )
    else:
        x_value = r_in.get_float(
            'set vertical line @: ')
    canvas.add_vertical_line(id_, x_value)
####
add_vline_to_canvas.def_t = (
    ("vline",),
    "add vertical line to canvas",
    (add_vline_to_canvas, roc_cli.CommandLineInterface.stop),
)
   
###################################################
#
# show info cli
#
###################################################

def show_info_cli (line):
    settings = {
        "cli_start_mss": False,
        "prompt": "canvas/info> ",
    }
    commands = {
        "abort": roc_cli.abort,
        "code": show_sended_code,
        "set_show_gnu_plot_code":  set_show_gnu_plot_code,
        "unset_show_gnu_plot_code":  unset_show_gnu_plot_code,
    }
    return roc_cli.CommandLineInterface(settings, commands).start(line)
show_info_cli.def_t = (
    ("?",),
    "acces info",
    (show_info_cli,),
)
    
    
def show_sended_code(split_line):
    global canvas
    print (">>>>>>>>>>>>>>>>>>>>>\n")
    for line in canvas.instructions:
        print(line)
    print("\n<<<<<<<<<<<<<<<<<<<<<<")
####
show_sended_code.def_t = (
    ("c",),
    "print sended code",
    (show_sended_code, roc_cli.CommandLineInterface.stop),
)

def set_show_gnu_plot_code(split_line):
    global canvas
    canvas.show_code = True
    return "show code SET"
####
set_show_gnu_plot_code.def_t = (
    ("sgpc",),
    "Show running gnuplot code",
    (set_show_gnu_plot_code, roc_cli.CommandLineInterface.stop),
)
    
def unset_show_gnu_plot_code(split_line):
    global canvas
    canvas.show_code = False
    return "show code UNSET"
####
unset_show_gnu_plot_code.def_t = (
    ("usgpc",),
    "Don't show running gnuplot code",
    (unset_show_gnu_plot_code, roc_cli.CommandLineInterface.stop),
)

###################################################
#
# define variables and functions cli
#
###################################################

def define_cli():
    settings = {
        "cli_start_mss": False,
        "prompt": "canvas/define> ",
    }
    commands = {
        "abort": abort,
        "variables": define_variable,
    }
    return roc_cli.CommandLineInterface(settings, commands).start()

def define_variable(split_line):
    global canvas
    name = r_in.get_string("name: ")
    if r_in.get_bool('number {}', default=True):
        value = r_in.get_float('value: ')
    else:
        value = r_in.get_string('value: ')
    canvas.var(name, value)
    return "var {} set to {}".format(name, value)
####
define_variable.def_t = (
    ("v",),
    "define variable",
    (define_variable, roc_cli.CommandLineInterface.stop),
)

    
###################################################
#
# cli helper
#
###################################################

def abort(parameters):
    return roc_cli.CommandLineInterface.STOP, "abort"
####
abort.def_t = (
    ("a",),
    "abort current action",
    (abort,),
)

###################################################
#
# helpers
#
###################################################

def read_ds_parameters():
    parameters = dict()
    name = r_in.get_string(
        "name: ",
        empty = True,
    )
    if name: parameters["name"] = name
    title = r_in.get_string(
        "title: ",
        empty = True,
    )
    if title: parameters["title"] = title
    function = read_ds_function()
    if function: parameters["function"] = function
    filename = read_ds_filename()
    if filename: parameters["filename"] = filename
    x_ranges = read_ds_ranges('x')
    if x_ranges: parameters["x_ranges"] = x_ranges
    y_ranges = read_ds_ranges('y')
    if y_ranges: parameters["y_ranges"] = y_ranges
    style = read_ds_style()
    if style: parameters["style"] = style
    color = read_ds_color()
    if color: parameters["color"] = color
    return parameters

def read_ds_function():
    function = r_in.get_string(
        "function: ",
        empty = True,
    )
    return function

def read_ds_filename():
    filename = r_in.get_string(
        "filename: ",
        empty = True,
    )
    return filename

def read_ds_ranges(axis_name):
    range_begin = r_in.get_string(
        "{}-start".format(axis_name),
        empty = True,
    )
    range_end = r_in.get_string(
        "{}-end".format(axis_name),
        empty = True,
    )
    if not(range_begin or range_end):
        return
    return (range_begin, range_end)

def read_ds_style():
    style = r_in.get_string(
        "style: ",
        empty = True,
    )
    return style

def read_ds_color():
    color = r_in.get_string(
        "color: ",
        empty = True,
    )
    return color
    
if __name__ == "__main__":
    main()