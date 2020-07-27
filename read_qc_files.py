import matplotlib.pyplot as plt
import os
import datetime
import sys
from collections import OrderedDict
import inspect
import config as config
from jinja2 import Environment, FileSystemLoader


class trend_analysis():
    """
    """
    def __init__(self, input_folder, output_folder, runtype):
        self.timestamp = datetime.datetime.now().strftime('%d-%B-%Y %H:%M')
        self.dictionary = OrderedDict({})
        self.plots = []
        self.runtype = runtype
        self.input_folder = input_folder
        self.output_folder = output_file

    def call_tools(self):
        """
        Loop through the list of plots in the sorted list (config.plot_order)
        For each module, it determine which module should be used to parse the data (defined by the function property of the tool config)
        For each tool a dictionary is returned, containing the run numbers as the keys, and a list of values as the value
        A plot is created for the tool (box_plot or table functions), using the plot type defined in the tool config and a html module created for the tool (self.create_tool_plot)
        """
        # for each tool in the prescribed order
        for tool in config.plot_order:
            # check the plot is applicable to this run type, eg coverage at 20X and contamination plots are only applicable to WES
            if config.tool_settings[tool][self.runtype]:
                # parse the list of available modules in this script
                for name,obj in inspect.getmembers(sys.modules[__name__]):
                    # if the module is described in the tool config (function) call that object
                    if config.tool_settings[tool]["function"] in name:
                        # eg if config.tool_settings[tool]["function"] == parse_multiqc_output
                        # that function is called, supplying tool and self.input_folder variables as inputs
                        # a dictionary is returned, with the run as a key, and a list of values as the value
                        self.dictionary[tool] = obj(tool,self.input_folder)
                        # Next determine what plot type is required for this tool (as defined in config)
                        if config.tool_settings[tool]["plot_type"]=="box_plot":
                            # box_plot function returns the location of a plot it has saved
                            self.dictionary[tool]["image_location"] = box_plot(tool,self.dictionary)
                        elif config.tool_settings[tool]["plot_type"]=="table":
                            # table function returns a html string
                            self.dictionary[tool]["table_text"] = table(tool,self.dictionary)
                        # call function which creates the html module for this tool
                        # append output to self.plots
                        self.plots.append(self.create_tool_plot(tool))
        # after looping through all tools generate report
        self.generate_report()

    def create_tool_plot(self, tool):
        """
        This function build a tool specific html module.
        This html is build using a template within the config file
        Plot specific settings are defined and passed to populate_html_template() which populates the placeholders within template
        Input:
            Tool that is being plotted. allows tool config and data to be accessed
        Returns:
            A populated html template
        """
        # define the template to be used and the content of the plot (eg a html string, or a path to a image)
        if config.tool_settings[tool]["plot_type"] == "table":
            template = config.table_template
            plot_content = self.dictionary[tool]["table_text"]
        else:
            template = config.plot_template
            plot_content =self.dictionary[tool]["image_location"]
        # pass plot title, plot text (both defined in tool config), plot content and the template to be used
        # the populated html template is returned, and this is returned from this function
        return self.populate_html_template(config.tool_settings[tool]["plot_title"],plot_content,config.tool_settings[tool]["plot_text"],template)



    def populate_html_template(self, plot_title, plot_image, plot_text, template):
        """
        Populates a html template for a single plot, which can then be added to the larger template
        Inputs:
            plot_title (string to put at top of section)
            plot_image (path to image saved earlier)
            plot_text (any plot specific text to go underneath the image)
            template (the template from the config file)
        Returns:
            populated template (html string) with placeholders complete
        """
        return template.format(plot_title, plot_text, plot_image)

    def generate_report(self):
        """
        This function takes all the plot specific html segments and inserts these into the report template
        The report html template is loaded, the placeholders filled and this report is saved to the provided location
        """

        # specify the folder containing the html templates
	# this should be a subfolder of this repository with the name defined in config file.
        html_template_dir = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__),config.template_dir)))

        # specify which html template to use, and load this as a python object, template
        html_template = html_template_dir.get_template("internal_report_template.html")

        # the template has a number of placeholders.
        # When the report is rendered these are populated from this dictionary
        # self.plots is a list of html sections created for each plot. join these into a single string, joint with a newline
        place_holder_values = {
            "reports":config.body_template.format("\n".join(self.plots)),
            "logo_path":config.logopath,
            "timestamp":self.timestamp
            }

        # open a html file, saved to the provided path
        with open(os.path.join(self.output_folder,self.runtype+"_trend_report.html"), "wb") as html_file:
            # write the template, rendering with the placeholders using the dictionary
            html_file.write(html_template.render(place_holder_values))

def table(tool,dictionary):
    """
    This function builds a html table.
    Currently, this is designed to describe the run names included in this trend analysis,
    and to build upon the template in the config file.
    A table row is added for each run in the dictionary
    The dictionary key go into the first column and it's value into the second column
    Inputs:
        dictionary - dictionary of qc data for all tools
        tool name - allows access to tool specific config settings and of dictionary
    Returns:
        String containing the table body html
    """
    # start string
    rows_html=""
    # define the html for a table row
    html_table_row="<tr><td >{}</td><td>{}</td></tr>"
    # for each sample, add to rows_html with the html_table_row, witht he placeholders filled
    # we need to sort the dictionary, as the order of dictionary keys aren't maintained (like a list is).
    for i in sorted(dictionary[tool]):
        rows_html+=html_table_row.format(i, dictionary[tool][i])
    # close table body tag
    rows_html+="</tbody>"
    # return string
    return rows_html

def box_plot(tool,dictionary):
    """
    This function builds a box plot and saves the image to a location defined in the config
    The x axis is labelled with the number of runs included, from oldest to newest
    Where specified in config, horizontal lines are added to define cutoffs

    Inputs:
        dictionary - dictionary of qc data for all tools
        tool name - allows access to tool specific config settings and of dictionary
    Returns:
        path to the plot specific image saved
    """
    # close the any previous plots to prevent previous data from being included on same axis
    plt.close()
    # build list of x axis labels
    # We don't know how many runs may be included so label the first as oldest and last as newest (use len of dictionary.keys())
    xlabels=[]
    for i in range(1,len(dictionary[tool].keys())+1):
        if i == 1:
            xlabels.append(str(i)+"\noldest")
        elif i == len(dictionary[tool].keys()):
            xlabels.append(str(i)+"\nnewest")
        else:
            xlabels.append(str(i))
    # Add the data to the plot
    # dictionary[tool] is a dictionary, with the run name as key, and a list of values as the value
    plt.boxplot(dictionary[tool].values(),labels=xlabels)

    # so we can draw horizontal cutoffs capture the axis ranges
    xmin, xmax, ymin, ymax = plt.axis()
    # add horizontal lines using plt.hlines
    # the positioning and labels are defined in the config (labels aren't working at the moment for some reason)
    if config.tool_settings[tool]["upper_lim"]:
        plt.hlines(config.tool_settings[tool]["upper_lim"],xmin, xmax,label=config.tool_settings[tool]["upper_lim_label"], linestyles=config.tool_settings[tool]["upper_lim_linestyle"],colors=config.tool_settings[tool]["upper_lim_linecolour"])
    if config.tool_settings[tool]["lower_lim"]:
        plt.hlines(config.tool_settings[tool]["lower_lim"],xmin, xmax,label=config.tool_settings[tool]["lower_lim_label"], linestyles=config.tool_settings[tool]["lower_lim_linestyle"],colors=config.tool_settings[tool]["lower_lim_linecolour"])
    # add the x ticks
    plt.xticks()
    # set the path to save image using the config location, run type (WES, PANEL, ONC) and tool name.
    image_path=os.path.join(config.images_folder,self.runtype + "_" + tool+".png")
    plt.savefig(image_path,bbox_inches="tight",dpi=200)
    # return the path to the save image
    return image_path

def sorted_runs(run_list):
    """
    The runs should be plotted in date order.
    The runs included in the analysis are saved in run specific folders, named with the runfolder name (002_YYMMDD_...)
    Extract the date of the run from the folder name and create an ordered list
    Input:
        List of run folders to be included in trend analysis
    Returns:
        sorted list of runfolder names
    """
    dates = []
    # for run in folder
    for run in run_list:
        # extract the date and add to list
        dates.append(int(run.split("_")[1]))

    # sort the list of dates, identify the full run name and append to sorted list
    sortedruns= []
    # if there are 2 runs on same day, both runs will be added for each date so use set()
    for date in sorted(set(dates)):
        for run in run_list:
            if str(date) in run:
                sortedruns.append(run)
    # return the sorted dates
    return sortedruns

def describe_run_names(tool,input_folder):
    """
    This function is specified as the function to be used in the tool config
    It's specific use is to populate a table describing the runs included in this analysis
    A sorted list of runs is determined
    A dictionary is built, with the key as the order and value the run name
    Inputs:
        dictionary - dictionary of qc data for all tools
        tool name - allows access to tool specific config settings and of dictionary
    Returns:
        dictionary with key as the order, and value the run name
    """
    # get date sorted list of runfolders
    sorted_run_list = sorted_runs(os.listdir(input_folder))
    run_name_dictionary = {}
    # build dictionary with key as the order and value as run name.
    # Add oldest and newest to first and last
    for i in range(1,len(sorted_run_list)+1):
        if i == 1:
            run_name_dictionary[str(i)+" oldest"] = sorted_run_list[i-1]
        elif i == len(sorted_run_list):
            run_name_dictionary[str(i)+" newest"] = sorted_run_list[i-1]
        else:
            run_name_dictionary[str(i)] = sorted_run_list[i-1]
    # return the dictionary
    return run_name_dictionary

def parse_multiqc_output(tool, input_folder):
    """
    This function is specified as the function to be used in the tool config
    It's specific use is to read a tool specific file output by multiqc
    these files tend to have a header line and then one row per sample
    Using the tool specific settings in the config file:
    for each runfolder the find function is used to find the file
    the return columns function is used to parse the file, returning the relevant data
    A dictionary is built with the run name as the key and value is a list of data points
    Inputs:
        dictionary - dictionary of qc data for all tools
        tool name - allows access to tool specific config settings and of dictionary
    Returns:
        dictionary with run name as the key and value is a list of data points
    """
    # get the name of the raw data file
    input_file_name = config.tool_settings[tool]["input_file"]
    tool_dict=OrderedDict({})
    # for each run find the file and pass it to return_columns, which generates a list
    # add this to the dictionary
    for run in sorted_runs(os.listdir(input_folder)):
        input_file = find(input_file_name,os.path.join(input_folder,run))
        tool_dict[run] = return_columns(input_file,tool)
    return tool_dict

def find(name, path):
    """
    Use os.walk to recursively search through all files in a folder
    Return the path to identified file
    Input:
        filename - file to look for
        path - path to the file containing all QC files for that run
    Returns:
        Path to file of interest
    """
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

def return_columns(file_path,tool):
    """
    For a given file, open and for each line (excluding header if required) extract the column of interest as a float
    Create and return a list of all meaurements
    Input:
        filepath - file to parse
        tool name - tool name - allows access to tool specific config settings
    Returns:
        a list of measurements from the column of interest,
    """
    # list for sample specific measurements
    to_return=[]
    # open file
    with open(file_path,'r') as input_file:
        # enumerate the list of lines as loop through it so we can skip the header if needed
        for linecount,line in enumerate(input_file):
            if config.tool_settings[tool]["header_present"] and linecount == 0:
                pass
            else:
                # split the line and pull out column of interest and add to list
                measurement = float(line.split("\t")[config.tool_settings[tool]["column_of_interest"]])
                to_return.append(measurement)
    # return list
    return to_return

def check_for_update():
    """
    Look to see if the index.html, which contains the links to multiqc reports has been modified in the last hour
    """
    # see when the index.html file was last modified
    index_last_modified = os.path.getmtime(config.index_file)
    # if the date modified is more than the frequency the script is run (using now - timedelta) a multiqc report has been added and we need to run the script.
    if index_last_modified >= datetime.datetime.now()-datetime.timedelta(hours=config.run_frequency):
	return True


def main():
    if check_for_update():
	for runtype in config.run_types:
            t=trend_analysis(input_folder=config.input_folder,output_folder=config.output_folder, runtype=runtype)
            t.call_tools()


if __name__ == '__main__':
    main()
