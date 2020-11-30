import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import os
import datetime
import pdfkit
import sys
from collections import OrderedDict
import inspect
import config as config
from jinja2 import Environment, FileSystemLoader
import argparse
from shutil import copyfile

def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments and help menu
    """
    parser = argparse.ArgumentParser()
    # Define the arguments that will be taken.
    parser.add_argument(
        '-d', '--dev', action='store_true', help="uses development output file locations (ensures live "
        "app isn't refreshed during development and testing)",
    )
    # Return the arguments
    return parser.parse_args()

class trend_analysis:
    """
    """
    def __init__(self, input_folder, output_folder, runtype, images_folder, archive_folder):
        self.timestamp = datetime.datetime.now().strftime('%d-%B-%Y %H:%M')
        self.filename_timestamp = datetime.datetime.now().strftime('%y%m%d_%H_%M')
        self.dictionary = OrderedDict({})
        self.plots = []
        self.runtype = runtype
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.images_folder = images_folder
        self.archive_folder = archive_folder

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
                print tool, self.runtype
                # parse the list of available modules in this script
                for name,obj in inspect.getmembers(sys.modules[__name__]):
                    # if the module is described in the tool config (function) call that object
                    if config.tool_settings[tool]["function"] in name:
                        # eg if config.tool_settings[tool]["function"] == parse_multiqc_output
                        # that function is called, supplying tool and self.input_folder variables as inputs
                        # a dictionary is returned, with the run as a key, and a list of values as the value
                        self.dictionary[tool] = obj(tool,self.input_folder, self.runtype)
                        # if the dictionary is populated (might not find the expected inputs)
                        if self.dictionary[tool]:
                            # Next determine what plot type is required for this tool (as defined in config)
                            if config.tool_settings[tool]["plot_type"]=="box_plot":
                                # box_plot function returns the location of a plot it has saved
                                self.dictionary[tool]["image_location"] = box_plot(tool, self.dictionary,
                                                                                       self.runtype, self.images_folder)
                            elif config.tool_settings[tool]["plot_type"]=="table":
                                # table function returns a html string
                                self.dictionary[tool]["table_text"] = table(tool,self.dictionary)
                            # call function which creates the html module for this tool
                            # append output to self.plots
                            self.plots.append(self.create_tool_plot(tool))
        # after looping through all tools generate report
        self.generate_report()
        # generate archive html
        self.generate_archive_html()

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



    @staticmethod
    def populate_html_template(plot_title, plot_image, plot_text, template):
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

        html_path = os.path.join(self.output_folder,self.runtype+"_trend_report.html")
        # open a html file, saved to the provided path
        with open(html_path, "wb") as html_file:
            # write the template, rendering with the placeholders using the dictionary
            html_file.write(html_template.render(place_holder_values))

        # the html file should be saved as a pdf (with all images) for long terms records. This uses the pdfkit package and wkhtmltopdf software 
        # # specify pdfkit options to turn off standard out and also allow access to the images
        # pdfkit needs the [ath tp wkhtmltopdf ninary file - defined in config]
        pdfkit_options = {'enable-local-file-access': None, "quiet": ''}
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=config.wkhtmltopdf_path)
        # using the pdfkit package, specify the html file to be converted, name the pdf kit using the timestamp and run type
        pdfkit.from_file(html_path, os.path.join(self.archive_folder, str(self.filename_timestamp) + "_" + self.runtype + "_trend_report.pdf"), configuration=pdfkit_config, options=pdfkit_options)

    def generate_archive_html(self):
        html_path = os.path.join(self.output_folder,"archive.html")
        archive_directory = os.listdir(self.archive_folder)
        with open(html_path, "wb") as html_file:
            html_file.write('<html><head align="center">ARCHIVED TREND ANALYSIS REPORTS</head><body><ul>')
            html_file.writelines(['<li><a href="archive/%s">%s</a></li>' % (f, f) for f in archive_directory])
            html_file.write('</ul></body></html>')

def table(tool, dictionary):
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
    # for each sample, add to rows_html with the html_table_row, with the placeholders filled
    # we need to sort the dictionary, as the order of dictionary keys aren't maintained (like a list is).
    for i in sorted(dictionary[tool]):
        rows_html+=html_table_row.format(i, dictionary[tool][i])
    # close table body tag
    rows_html+="</tbody>"
    # return string
    return rows_html

def box_plot(tool, dictionary, runtype, images_folder):
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
    # only add legends to plots with bound lines specified in config file
    if (config.tool_settings[tool]["lower_lim_label"] is not False) or (config.tool_settings[tool]["upper_lim_label"] is not False):
        plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
    # add the x ticks
    plt.xticks()
    plt.ticklabel_format(axis='y', useOffset=False, style='plain')
    # set the path to save image using the config location, run type (WES, PANEL, ONC) and tool name.
    image_path=os.path.join(images_folder,runtype + "_" + tool+".png")
    html_image_path = "images/"+runtype + "_" + tool+".png"
    plt.savefig(image_path, bbox_inches="tight",dpi=200)
    # return the path to the save image
    return html_image_path

def sorted_runs(run_list, input_folder, runtype):
    """
    The runs should be plotted in date order, oldest to newest.
    The runs included in the analysis are saved in run specific folders, named with the runfolder name (002_YYMMDD_[*WES*,*NGS*,*ONC*])
    Extract the date of the run from the folder name and create an ordered list

    Input:
        List of run folders to be included in trend analysis
        Runtype - one of WES, PANEL or SWIFT to filter the available runs
    Returns:
        list of most recent runfolder names, in date ascending order (oldest first)
    """
    dates = {}
    # for run in folder
    for run in run_list:
        # need to filter for only runs of this runtype, and only runs with non-empty runfolders
        # if run of interest, extract the date and add this as a key to the  dict
        # add run name as the value
        if runtype == "WES" and "WES" in run:
            if not len(os.listdir(input_folder +'/'+ run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "PANEL" and "NGS" in run and "WES" not in run:
            if not len(os.listdir(input_folder +'/'+ run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "SWIFT" and "ONC" in run:
            if not len(os.listdir(input_folder +'/'+ run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "NEXTSEQ_LUIGI" and "NB552085" in run:
            if not len(os.listdir(input_folder +'/'+ run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "NEXTSEQ_MARIO" and "NB551068" in run:
            if not len(os.listdir(input_folder +'/'+ run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "MISEQ_ONC" and "M02353" in run:
            if not len(os.listdir(input_folder +'/'+ run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "MISEQ_DNA" and "M02631" in run:
            if not len(os.listdir(input_folder +'/'+ run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "NOVASEQ_PIKACHU" and "A01229" in run:
            if not len(os.listdir(input_folder +'/'+ run)) == 0:
                dates[(int(run.split("_")[1]))] = run

    # sort the list of dates, identify the full run name and append to sorted list
    sortedruns= []
    # if there are 2 runs on same day, both runs will be added for each date so use set()
    # sort the list of dictionary keys (dates) in ascending order (oldest first)
    for date in sorted(set(dates)):
        sortedruns.append(dates[date])
    # return the x most recent runs (x is defined in config)
    return sortedruns[-config.number_of_runs_to_include:]

def describe_run_names(tool, input_folder, runtype):
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
    sorted_run_list = sorted_runs(os.listdir(input_folder), input_folder, runtype)
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

def parse_multiqc_output(tool, input_folder, runtype):
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
    for run in sorted_runs(os.listdir(input_folder), input_folder, runtype):
        input_file = find(input_file_name, os.path.join(input_folder, run))
        #input_file = select_input_file(input_file_name, input_folder, run, tool)
        if input_file:
            tool_dict[run] = return_columns(input_file, tool)
    return tool_dict

def find(name, path):
    """
    Use os.walk to recursively search through all files in a folder
    Return the path to identified file
    Input:
        name - filename from config file
        filename - full file name obtained using name
        path - path to the file containing all QC files for that run
    Returns:
        Path to file of interest
    """
    for root, dirs, files in os.walk(path):
        for filename in files:
            if name in filename:
                return os.path.join(root, filename)
    print "no output named {} for run {}".format(name, path)
    return False

def return_columns(file_path,tool):
    """
    For a given file, open and for each line (excluding header if required) extract the column of interest as a float.
    If the tool is the cluster density plot, skips the first seven rows as these are headers.
    For all other plots, skips the first row as this is the header.
    Create and return a list of all measurements
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
        for linecount, line in enumerate(input_file):
            if config.tool_settings[tool]["input_file"] == "illumina_lane_metrics":
                if config.tool_settings[tool]["header_present"] and 0<=linecount<=6:
                    pass
                else:
                    # ignore blank lines, split the line, pull out column of interest, divide by 1000, add to list
                    if not line.isspace():
                        measurement = float(line.split("\t")[config.tool_settings[tool]["column_of_interest"]])/1000
                    to_return.append(measurement)
            else:
                if config.tool_settings[tool]["header_present"] and linecount == 0:
                    pass
                else:
                    # for all other rows that aren't header rows, split line, pull out column of interest, add to list
                    if config.tool_settings[tool]["conversion_to_percent"]:
                        measurement = float(line.split("\t")[config.tool_settings[tool]["column_of_interest"]])*100
                    else:
                        measurement = float(line.split("\t")[config.tool_settings[tool]["column_of_interest"]])
                    to_return.append(measurement)
    # return list
    return to_return

def check_for_update():
    """
    Look to see if the index.html, which contains the links to multiqc reports has been modified in the last hour
    """
    # see when the index.html file was last modified
    index_last_modified = datetime.datetime.utcfromtimestamp(os.path.getmtime(config.index_file))
    # if the date modified is more than the frequency the script is run (using now - timedelta) a multiqc report has been added and we need to run the script.
    if index_last_modified >= datetime.datetime.now()-datetime.timedelta(hours=config.run_frequency):
        return True
    else:
        #print "index not modified since script run last"
	# whilst debugging
	#return True
	return False


def main():
    args = get_arguments()
    # If the user runs the script during development
    if args.dev:
        for runtype in config.run_types:
            t = trend_analysis(input_folder=config.dev_input_folder, output_folder=config.dev_output_folder,
                               images_folder=config.dev_images_folder, runtype=runtype,
                               archive_folder=config.dev_archive_folder)
            t.call_tools()
        copyfile(src=config.index_file,dst=config.dev_index_file)

   # If the script is run in the production environment
    else:
        if check_for_update():
            for runtype in config.run_types:
                t=trend_analysis(input_folder=config.input_folder,output_folder=config.output_folder,
                                 images_folder=config.images_folder, runtype=runtype,
                                 archive_folder=config.archive_folder)
                t.call_tools()


if __name__ == '__main__':
    main()
