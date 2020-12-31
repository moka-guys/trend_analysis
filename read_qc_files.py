import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import subprocess
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
import smtplib
from email.message import Message
import pandas as pd
import time


def arg_parse():
    """
    Uses argparse module to create an argument parser and define and handle command line arguments
        :return:
            (Namespace object) :  parsed command line attributes
    """
    parser = argparse.ArgumentParser()
    # defines command line arguments
    parser.add_argument(
        '-d', '--dev', action='store_true', help="uses development output file locations (ensures live "
                                                 "app isn't refreshed during development and testing)",
    )
    return parser.parse_args()


class TrendAnalysis(object):
    """
    A class to create a trend report.

    Attributes
    __________
    dictionary : OrderedDict
        populated with qc data from multiqc outputs required for each plot
    plots : list
        list of plots to be included in the trend report
    runtype : str
        a html trend report is generated for each runtype specified in config.py
    input_folder : str
        path to multiqc data per run
    output_folder : str
        path to save location for html trend reports and archive_index.html
    template_dir : str
        path to html templates
    archive_folder : str
        path to archived html reports

    Methods
    _______
    call_tools(self):
        For each tool in the config file, determines the modules used to parse the data.
        Returns a dictionary for each tool which is used to create the plot for that tool.
        Creates a html module for that tool.
    create_tool_plot(self, tool):
        Builds tool-specific html modules using a template within the config file.
    populate_html_template(plot_title, plot_image, plot_text, template):
        Populates a html template for a single plot, which can then be added to the larger template.
    generate_report(self):
        Inserts all plot specific html segments into the report template, and save report to provided location.
    generate_archive_html(self):
        Add created trend report as a link to the archive_index.html so legacy reports are available to users.
    """

    def __init__(self, input_folder, output_folder, runtype, images_folder, template_dir, archive_folder):
        self.dictionary = OrderedDict({})
        self.plots = []
        self.runtype = runtype
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.images_folder = images_folder
        self.template_dir = template_dir
        self.archive_folder = archive_folder

    def call_tools(self):
        """
        Loop through the list of tools in config.plot_order
        For each tool, determine which module should be used to parse the data (defined by the function property of the tool config)
        For each tool return a dictionary containing run numbers as keys, and a list of values as the value
        Create a plot using the plot type defined in the tool config (box_plot or table functions)
        Create a html module for the tool (self.create_tool_plot)
        """
        # for each tool in the prescribed order
        for tool in config.plot_order:
            # check the plot is applicable to run type (specified in tool settings for each tool)
            if config.tool_settings[tool][self.runtype]:
                print tool, self.runtype
                # parse the list of available modules in this script
                for name, obj in inspect.getmembers(sys.modules[__name__]):
                    # if the module is described in the tool config (function) call that object
                    if config.tool_settings[tool]["function"] in name:
                        # eg if config.tool_settings[tool]["function"] == parse_multiqc_output
                        # parse_multiqc_output function is called and dictionary returned
                        self.dictionary[tool] = obj(tool, self.input_folder, self.runtype)
                        # if the dictionary is populated (might not find the expected inputs)
                        if self.dictionary[tool]:
                            # determine plot type required for tool as defined in config
                            if config.tool_settings[tool]["plot_type"] == "box_plot":
                                # box_plot function returns path to saved plot
                                self.dictionary[tool]["image_location"] = box_plot(tool, self.dictionary,
                                                                                   self.runtype, self.images_folder)
                            elif config.tool_settings[tool]["plot_type"] == "stacked_bar":
                                # stacked_bar function returns path to saved plot
                                self.dictionary[tool]["image_location"] = stacked_bar(tool, self.dictionary,
                                                                                      self.runtype, self.images_folder)
                            elif config.tool_settings[tool]["plot_type"] == "table":
                                # table function returns a html string
                                self.dictionary[tool]["table_text"] = table(tool, self.dictionary)
                            # call function which creates the html module for this tool and append output to self.plots
                            self.plots.append(self.create_tool_plot(tool))
        # after looping through all tools generate report
        self.generate_report()
        # generate archive html
        self.generate_archive_html()

    def create_tool_plot(self, tool):
        """
        Builds a tool-specific html module using a template within the config file
        Defines plot specific settings and passes to populate_html_template() which populates placeholders within template
            :param tool: (str) Tool that is being plotted. Allows tool config and data to be accessed
            :return: (html string) Populated html template
        """
        # define the template to be used and the content of the plot (eg a html string, or a path to a image)
        if config.tool_settings[tool]["plot_type"] == "table":
            template = config.table_template
            plot_content = self.dictionary[tool]["table_text"]
        else:
            template = config.plot_template
            # Deals with browser caching - appends a GET value (the UNIX timestamp) to the image URL
            # This makes the browser think the image is dynamic, so reloads it every time the modification date changes
            # Means the new image is used when a new plot is generated, rather than the cached one
            plot_content = os.path.join(
                self.dictionary[tool]["image_location"] + '?" . filemtime(' + self.dictionary[tool][
                    "image_location"] + ') . "')
        # pass plot title, plot text (both defined in tool config), plot content and the template to be used
        # the populated html template is returned, and this is returned from this function
        return self.populate_html_template(config.tool_settings[tool]["plot_title"], plot_content,
                                           config.tool_settings[tool]["plot_text"], template)

    @staticmethod
    def populate_html_template(plot_title, plot_image, plot_text, template):
        """
        Populates a html template for a single plot, which can then be added to the larger template
            :param plot_title: (str) String to put at top of section
            :param plot_image: (str) Path to image saved earlier
            :param plot_text: (str) Any plot specific text to go underneath the image
            :param template: (str) Template from the config file
            :return: (html string) Populated template with placeholders complete
        """
        return template.format(plot_title, plot_text, plot_image)

    def generate_report(self):
        """
        Inserts all plot specific html segments into the report template
        Loads report html template, fills placeholders, and saves report to the provided location using pdfkit package and wkhtmltopdf software
        """
        # specify folder containing the html templates
        html_template_dir = Environment(loader=FileSystemLoader(self.template_dir))
        # specify which html template to use, and load this as a python object, template
        html_template = html_template_dir.get_template("internal_report_template.html")
        # the template has a number of placeholders
        # When the report is rendered these are populated from this dictionary
        # self.plots is a list of html sections created for each plot. join these into a single string, joint with a newline
        place_holder_values = {
            "reports": config.body_template.format("\n".join(self.plots)),
            "logo_path": config.logopath,
            "timestamp": datetime.datetime.now().strftime('%d-%B-%Y %H:%M'),
            "app_version": git_tag()
        }
        html_path = os.path.join(self.output_folder, self.runtype + "_trend_report.html")
        # open a html file, saved to the provided path
        with open(html_path, "wb") as html_file:
            # write the template, rendering with the placeholders using the dictionary
            html_file.write(html_template.render(place_holder_values))
        # saves html file as pdf (with all images) for long term records
        # specify pdfkit options to turn off standard out and also allow access to the images
        # pdfkit needs the path tp wkhtmltopdf binary file - defined in config
        pdfkit_options = {'enable-local-file-access': None, "quiet": ''}
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=config.wkhtmltopdf_path)
        # using the pdfkit package, specify the html file to be converted, name the pdf kit using the timestamp and run type
        pdfkit.from_file(html_path, os.path.join(self.archive_folder, str(
            datetime.datetime.now().strftime('%y%m%d_%H_%M')) + "_" + self.runtype + "_trend_report.pdf"),
                         configuration=pdfkit_config, options=pdfkit_options)

    def generate_archive_html(self):
        """
        Adds the created trend report as a link to the archive_index.html
        This means the archived version is still accessible after the live report has been overwritten with more recent runs.
        """
        html_path = os.path.join(self.output_folder, "archive_index.html")
        archive_directory = os.listdir(self.archive_folder)
        with open(html_path, "wb") as html_file:
            html_file.write('<html><head align="center">ARCHIVED TREND ANALYSIS REPORTS</head><body><ul>')
            html_file.writelines(['<li><a href="archive/%s">%s</a></li>' % (f, f) for f in archive_directory])
            html_file.write('</ul></body></html>')


class Emails(object):
    """
    A class to handle email sending and logs. Determines new runs, sends emails and creates logfiles.

    Attributes
    __________
    input_folder : str
        path to multiqc data per run
    runtype : str
        required as provides one of the elements of the saved plot image name
    wes_email : str
        recipient for completed WES trend analysis email alerts
    oncology_ops_email : str
        recipient for completed SWIFT trend analysis email alerts
    custom_panels_email : str
        recipient for completed custom panels trend analysis email alerts
    mokaguys_email : str
        mokaguys email address
    logfile_path : str
        Path to email logfile

    Methods
    _______
    call_tools(self):
        Calls the methods required for email sending.
    determine_new_runs(self, run_list):
        Checks whether runs for that runtype have previously been analysed/email sent by checking the logfiles.
    check_sent(self, run_list):
        Check whether runs for runtype have previously been analysed/emails sent by checking logfiles.
    """

    def __init__(self, input_folder, runtype, wes_email, oncology_ops_email, custom_panels_email,
                 email_subject):
        self.input_folder = input_folder
        self.runtype = runtype
        self.wes_email = wes_email
        self.oncology_ops_email = oncology_ops_email
        self.custom_panels_email = custom_panels_email
        self.email_subject = email_subject
        self.mokaguys_email = config.mokaguys_email
        self.logfile_path = os.path.join(self.input_folder + '/{}/email_logfile')

    def call_tools(self):
        """
        Call methods required for email sending.
        """
        # create runlist for all runs of the runtype
        run_list = sorted_runs(os.listdir(self.input_folder), self.input_folder, self.runtype)
        # check whether any of these runs are new and not yet included in the trend reports
        new_runs = self.check_sent(run_list)
        if new_runs:
            # send new trend report alert email to relevant team
            self.send_email(new_runs)
            # create logfile in runfolder denoting mail has been sent
            self.create_email_logfile(new_runs)

    def check_sent(self, run_list):
        """
        Checks whether runs for that runtype have previously been analysed/email sent by checking the logfiles.
            :param run_list: (list) List of run folders to be included in trend analysis
            :return new_runs: (list) list of runs that have not yet been analysed
        """
        new_runs = []
        for run in run_list:
            logfile_path = self.logfile_path.format(run)
            run_folder = os.listdir(os.path.join(self.input_folder + '/' + run))
            # if the run has previously been analysed (logfile present and 'Email sent' logged)
            if "email_logfile" in run_folder and "email sent" in open(logfile_path, "r").read():
                pass
            else:
                # run has not been analysed so append to new_runs list
                new_runs.append(run)
        return new_runs

    def send_email(self, new_runs):
        """
        Sends email per runtype for runtypes with newly analysed runs to notify users of new trend report.
        Uses smtplib.
            :param new_runs: (list) list of runs that have not yet been analysed
        """
        # set email message and recipients
        email_message = ("The MultiQC report is available for " + ", ".join(
            new_runs) + " and the trend analysis has been updated")

        if self.runtype == "WES":
            recipients = [self.wes_email, self.mokaguys_email]
        if self.runtype == "PANEL":
            recipients = [self.custom_panels_email, self.mokaguys_email]
        if self.runtype == "SWIFT":
            recipients = [self.oncology_ops_email, self.mokaguys_email]

        # create message object, set priority, subject, recipients, sender and body
        m = Message()
        m["X-Priority"] = str("3")
        m["Subject"] = self.email_subject.format(", ".join(new_runs))
        m['To'] = ", ".join(recipients)
        m['From'] = config.moka_alerts_email
        m.set_payload(email_message)

        # server details
        server = smtplib.SMTP(host=config.host, port=config.port, timeout=10)
        server.set_debuglevel(False)  # verbosity turned off - set to true to get debug messages
        server.starttls()
        server.ehlo()
        server.login(config.user, config.pw)
        server.sendmail(config.moka_alerts_email, recipients, m.as_string())

    def create_email_logfile(self, new_runs):
        """
        Creates a logfile to record that the run has been analysed and a notification email sent to the relevant team.
        :param new_runs: (list) list of runs that have not yet been analysed
        """
        # for run in new_runs:
        for run in new_runs:
            logfile_path = self.logfile_path.format(run)
            with open(logfile_path, "w") as logfile_path:
                logfile_path.write(datetime.datetime.now().strftime(
                    '%d-%B-%Y %H:%M') + ": Run has been analysed and notification email sent")
        return


def table(tool, dictionary):
    """
    Builds a html table using the template in the config file and the run names included in this trend analysis.
    A table row is added for each run in the dictionary, with dictionary key in column 1 and its value in column 2.
        :param dictionary: (OrderedDict) dictionary of qc data for all tools
        :param tool: (str) Tool name which allows access to tool-specific config settings and of dictionary
        :return rows_html: (str) contains the table body html
    """
    # start string
    rows_html = ""
    # define the html for a table row
    html_table_row = "<tr><td >{}</td><td>{}</td></tr>"
    # for each sample, add to rows_html with the html_table_row, with the placeholders filled
    # we need to sort the dictionary, as the order of dictionary keys aren't maintained (like a list is).
    for i in sorted(dictionary[tool]):
        rows_html += html_table_row.format(i, dictionary[tool][i])
    # close table body tag
    rows_html += "</tbody>"
    return rows_html


def box_plot(tool, dictionary, runtype, images_folder):
    """
    Builds a box plot and saves the image to a location defined in the config
    The x axis is labelled with the number of runs included, from oldest to newest
    Where specified in config, horizontal lines are added to define cutoffs
        :param dictionary: (OrderedDict) dictionary of qc data for all tools
        :param tool: (str) allows access to tool specific config settings and of dictionary
        :param runtype: (str) required as provides one of the elements of the saved plot image name
        :param images_folder: (str) plot save location
        :return html_image_path: (str) path to the saved plot specific image
    """
    # close any previous plots to prevent previous data from being included on same axis
    plt.close()
    # build list of x axis labels
    # We don't know how many runs may be included so label the first as oldest and last as newest (use len of dictionary.keys())
    xlabels = []
    for i in range(1, len(dictionary[tool].keys()) + 1):
        if i == 1:
            xlabels.append(str(i) + "\noldest")
        elif i == len(dictionary[tool].keys()):
            xlabels.append(str(i) + "\nnewest")
        else:
            xlabels.append(str(i))
    # Add the data to the plot
    # dictionary[tool] is a dictionary, with the run name as key, and a list of values as the value
    plt.boxplot(dictionary[tool].values(), labels=xlabels)
    # so we can draw horizontal cutoffs capture the axis ranges
    xmin, xmax, ymin, ymax = plt.axis()
    # add horizontal lines using plt.hlines
    # the positioning and labels are defined in the config (labels aren't working at the moment for some reason)
    if config.tool_settings[tool]["upper_lim"]:
        plt.hlines(config.tool_settings[tool]["upper_lim"], xmin, xmax,
                   label=config.tool_settings[tool]["upper_lim_label"],
                   linestyles=config.tool_settings[tool]["upper_lim_linestyle"],
                   colors=config.tool_settings[tool]["upper_lim_linecolour"])
    if config.tool_settings[tool]["lower_lim"]:
        plt.hlines(config.tool_settings[tool]["lower_lim"], xmin, xmax,
                   label=config.tool_settings[tool]["lower_lim_label"],
                   linestyles=config.tool_settings[tool]["lower_lim_linestyle"],
                   colors=config.tool_settings[tool]["lower_lim_linecolour"])
    # only add legends to plots with bound lines specified in config file
    if (config.tool_settings[tool]["lower_lim_label"] is not False) or (
            config.tool_settings[tool]["upper_lim_label"] is not False):
        plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
    # add the x ticks
    plt.xticks()
    plt.ticklabel_format(axis='y', useOffset=False, style='plain')
    # set the path to save image using the config location, run type (WES, PANEL, ONC) and tool name.
    image_path = os.path.join(images_folder, runtype + "_" + tool + ".png")
    html_image_path = "images/" + runtype + "_" + tool + ".png"
    plt.savefig(image_path, bbox_inches="tight", dpi=200)
    # return the path to the save image
    return html_image_path


def stacked_bar(tool, dictionary, runtype, images_folder):
    """
    Creates a stacked bar chart from a dictionary input.
    :param tool: (str) allows access to tool specific config settings and of dictionary
    :param dictionary: (OrderedDict) dictionary of qc data for all tools

    :param runtype: (str) required as provides one of the elements of the saved plot image name
    :param images_folder:
    :return:
    """
    # close any previous plots to prevent previous data from being included on same axis
    plt.close()
    # build list of x axis labels
    # We don't know how many runs may be included so label the first as oldest and last as newest (use len of dictionary.keys())
    xlabels = []
    for i in range(1, len(dictionary[tool].keys()) + 1):
        if i == 1:
            xlabels.append(str(i) + "\noldest")
        elif i == len(dictionary[tool].keys()):
            xlabels.append(str(i) + "\nnewest")
        else:
            xlabels.append(str(i))
    # dictionary[tool] is a dictionary, with the run name as key, and a list of values as the value
    # convert dictionary to a pandas dataframe, count true and false values for each run
    # transform dataframe so row index is run names
    df = pd.DataFrame(dictionary[tool]).apply(pd.value_counts)
    # replace run names with x axis labels
    df.columns = xlabels
    # Add the data to the plot as bar chart
    df.T.plot.bar(rot=0)
    # add the x ticks
    plt.xticks()
    plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
    plt.ticklabel_format(axis='y', useOffset=False, style='plain')
    # set the path to save image using the config location, run type (WES, PANEL, ONC) and tool name.
    image_path = os.path.join(images_folder, runtype + "_" + tool + ".png")
    html_image_path = "images/" + runtype + "_" + tool + ".png"
    plt.savefig(image_path, bbox_inches="tight", dpi=200)
    # return the path to the save image
    return html_image_path


def sorted_runs(run_list, input_folder, runtype):
    """
    The runs should be plotted in date order, oldest to newest.
    The runs included in the analysis are saved in run specific folders, named with the runfolder name (002_YYMMDD_[*WES*,*NGS*,*ONC*])
    Extract the date of the run from the folder name and create an ordered list
        :param run_list: (list) List of run folders to be included in trend analysis
        :param input_folder: (str) path to multiqc data per run
        :param runtype: (str) runtypes specified in config, to filter available runs
        :return (list) list of most recent runfolder names, in date ascending order (oldest first)
    """
    dates = {}
    # for run in folder
    for run in run_list:
        # need to filter for only runs of this runtype, and only runs with non-empty runfolders
        # if run of interest, extract the date and add this as a key to the  dict
        # add run name as the value
        if runtype == "WES" and "WES" in run:
            if not len(os.listdir(input_folder + '/' + run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "PANEL" and "NGS" in run and "WES" not in run:
            if not len(os.listdir(input_folder + '/' + run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "SWIFT" and "ONC" in run:
            if not len(os.listdir(input_folder + '/' + run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "NEXTSEQ_LUIGI" and "NB552085" in run:
            if not len(os.listdir(input_folder + '/' + run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "NEXTSEQ_MARIO" and "NB551068" in run:
            if not len(os.listdir(input_folder + '/' + run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "MISEQ_ONC" and "M02353" in run:
            if not len(os.listdir(input_folder + '/' + run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "MISEQ_DNA" and "M02631" in run:
            if not len(os.listdir(input_folder + '/' + run)) == 0:
                dates[(int(run.split("_")[1]))] = run
        if runtype == "NOVASEQ_PIKACHU" and "A01229" in run:
            if not len(os.listdir(input_folder + '/' + run)) == 0:
                dates[(int(run.split("_")[1]))] = run

    # sort the list of dates, identify the full run name and append to sorted list
    sortedruns = []
    # if there are 2 runs on same day, both runs will be added for each date so use set()
    # sort the list of dictionary keys (dates) in ascending order (oldest first)
    for date in sorted(set(dates)):
        sortedruns.append(dates[date])
    # return the x most recent runs (x is defined in config)
    return sortedruns[-config.number_of_runs_to_include:]


def parse_multiqc_output(tool, input_folder, runtype):
    """
    This function is specified as the function to be used in the tool config
    Reads a tool specific output file by multiqc (tend to have a header line then one row per sample)
    Using the tool specific settings in the config file
    For each runfolder the find function finds the file
    Return columns function parses the file, returning relevant data
    Dictionary is built with run name as key and value as a list of data points.
        :param tool: (str) allows access to tool specific config settings and of dictionary
        :param input_folder: (str) path to multiqc data per run
        :param runtype: (str) runtypes specified in config, to filter available runs
        :return tool_dict (OrderedDict) dictionary with run name as the key and value is a list of data points
    """
    # get the name of the raw data file
    input_file_name = config.tool_settings[tool]["input_file"]
    tool_dict = OrderedDict({})

    # for each run find the file and pass it to return_columns, which generates a list
    # add this to the dictionary
    for run in sorted_runs(os.listdir(input_folder), input_folder, runtype):
        input_file = find(input_file_name, os.path.join(input_folder, run))
        # input_file = select_input_file(input_file_name, input_folder, run, tool)
        if input_file:
            tool_dict[run] = return_columns(input_file, tool)
    return tool_dict


def describe_run_names(tool, input_folder, runtype):
    """
    This function is specified as the function to be used in the tool config
    Populates a table describing the runs included in this analysis
    Creates sorted list of runs, and builds a dictionary with key as order and value as run name
        :param tool: (str) allows access to tool specific config settings and of dictionary
        :param input_folder: (str) path to multiqc data per run
        :param runtype: (str) runtypes specified in config, to filter available runs
        :return run_name_dictionary: (dict) dictionary with key as the order, and value the run name
    """
    # get date sorted list of runfolders
    sorted_run_list = sorted_runs(os.listdir(input_folder), input_folder, runtype)
    run_name_dictionary = {}
    # build dictionary, add oldest and newest to first and last
    for i in range(1, len(sorted_run_list) + 1):
        if i == 1:
            run_name_dictionary[str(i) + " oldest"] = sorted_run_list[i - 1]
        elif i == len(sorted_run_list):
            run_name_dictionary[str(i) + " newest"] = sorted_run_list[i - 1]
        else:
            run_name_dictionary[str(i)] = sorted_run_list[i - 1]
    # return the dictionary
    return run_name_dictionary


def find(name, path):
    """
    Use os.walk to recursively search through all files in a folder
    Return the path to identified file
        :param name: (str) filename from config file
        :param path: (str) path to the file containing all QC files for that run
        :return: (str) path to file of interest. Only returned if the file exists for that run.
    """
    for root, dirs, files in os.walk(path):
        for filename in files:
            if name in filename:
                return os.path.join(root, filename)
    print "no output named {} for run {}".format(name, path)
    return False


def return_column_index(input_file, tool):
    """
    Selects the column of interest based on the column heading provided in the config file.
        :param input_file: (str) name of raw data file (multiqc output file)
        :param tool: (str) allows access to tool specific config settings and of dictionary
        :return column_index: (int) index of the column of interest that contains the relevant data for plotting.
    """
    # create a list of headers split on tab
    header_line = [input_file.readline().strip('\n').split("\t")]
    # get index of column of interest
    column_index = header_line[0].index(config.tool_settings[tool]["column_of_interest"])
    return column_index


def return_columns(file_path, tool):
    """
    For a given file, open and for each line (excluding header if required) extract the column of interest as a float.
    If the tool is the cluster density plot, skips the first seven rows as these are headers.
    For all other plots, skips the first row as this is the header.
    Create and return a list of all measurements
        :param file_path: (str) file to parse
        :param tool: (str) tool name - allows access to tool specific config settings
        :return to_return: (list) a list of measurements from the column of interest
    """
    # list for sample specific measurements
    to_return = []
    # open file
    with open(file_path, 'r') as input_file:
        # select column index of interest
        column_index = return_column_index(input_file, tool)
        # enumerate the list of lines as loop through it so we can skip the header if needed
        for linecount, line in enumerate(input_file):
            # if the tool is the cluster density plot, skip the first 7 rows as these are headers
            if config.tool_settings[tool]["input_file"] == "illumina_lane_metrics":
                if config.tool_settings[tool]["header_present"] and 0 <= linecount <= 6:
                    pass
                else:
                    # ignore blank lines, split the line, pull out column of interest, divide by 1000, add to list
                    if not line.isspace():
                        measurement = float(line.split("\t")[column_index]) / 1000
                        to_return.append(measurement)
            # for all other tool types
            else:
                # skip header row
                if config.tool_settings[tool]["header_present"] and linecount == 0:
                    pass
                else:
                    # exclude negative control stats from the "properly_paired" and "pct_off_amplicon" plots
                    if (config.tool_settings[tool]["input_file"] in ["multiqc_picard_pcrmetrics.txt",
                                                                     "multiqc_samtools_flagstat.txt"]) and (
                            "NTCcon" in line):
                        pass
                    # for all other rows that aren't header rows, split line, pull out column of interest, add to list
                    elif config.tool_settings[tool]["conversion_to_percent"]:
                        measurement = float(line.split("\t")[column_index]) * 100
                        to_return.append(measurement)
                    elif config.tool_settings[tool]["plot_type"] == "stacked_bar":
                        measurement = line.split("\t")[column_index]
                        # do not include blank space
                        if measurement is not "":
                            to_return.append(measurement)
                    else:
                        measurement = float(line.split("\t")[column_index])
                        to_return.append(measurement)
    # return list
    return to_return


def git_tag():
    """
    Reads the script release version number directly from the repository
        :return: (str) returns version number of current script release
    """
    #  set the command which prints the git tags for the folder containing the script that is being executed.
    #  The tag looks like "v22-3-gccfd" so needs to be parsed.
    #  Use awk to create an array "a", splitting on "-". The print the first element of the array
    cmd = "git -C " + os.path.dirname(
        os.path.realpath(__file__)) + " describe --tags | awk '{split($0,a,\"-\"); print a[1]}'"
    #  use subprocess to execute command
    proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    #  return standard out, removing any new line characters
    return out.rstrip()


def check_for_update():
    """
    Look to see if the index.html, which contains the links to multiqc reports has been modified in the last hour
    If it has, return true, if not return false.
        :return: (bool) returns a Boolean value true or false
    """
    # see when the index.html file was last modified
    index_last_modified = datetime.datetime.utcfromtimestamp(os.path.getmtime(config.index_file))
    # if the date modified is more than the frequency the script is run (using now - timedelta) a multiqc report has been added and we need to run the script.
    if index_last_modified >= datetime.datetime.now() - datetime.timedelta(hours=config.run_frequency):
        return True
    else:
        # print "index not modified since script run last"
        return False


def main():
    args = arg_parse()
    # If the user runs the script during development
    if args.dev:
        for runtype in config.run_types:
            t = TrendAnalysis(input_folder=config.dev_input_folder, output_folder=config.dev_output_folder,
                              images_folder=config.dev_images_folder, runtype=runtype,
                              template_dir=config.dev_template_dir,
                              archive_folder=config.dev_archive_folder)
            t.call_tools()
            e = Emails(input_folder=config.dev_input_folder, runtype=runtype, wes_email=config.dev_recipient,
                       oncology_ops_email=config.dev_recipient, custom_panels_email=config.dev_recipient,
                       email_subject=config.dev_email_subject)
            e.call_tools()
        copyfile(src=config.index_file, dst=config.dev_index_file)

    # If the script is run in the production environment
    else:
        if check_for_update():
            for runtype in config.run_types:
                t = TrendAnalysis(input_folder=config.input_folder, output_folder=config.output_folder,
                                  images_folder=config.images_folder, runtype=runtype,
                                  template_dir=config.template_dir,
                                  archive_folder=config.archive_folder)
                t.call_tools()
                e = Emails(input_folder=config.input_folder, runtype=runtype, wes_email=config.wes_email,
                           oncology_ops_email=config.oncology_ops_email,
                           custom_panels_email=config.custom_panels_email, email_subject=config.email_subject)
                e.call_tools()


if __name__ == '__main__':
    main()
