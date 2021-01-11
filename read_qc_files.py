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
    Parses arguments supplied by the command line.
        :return: (Namespace object) parsed command line attributes

    Creates argument parser, defines command line arguments, then parses supplied command line arguments using the
    created argument parser.
    """
    parser = argparse.ArgumentParser()
    # defines command line arguments
    parser.add_argument('-d', '--dev', action='store_true', help="uses development output file locations (ensures live"
                                                 " reports aren't overwritten during development and testing)")
    return parser.parse_args()

class TrendReport(object):
    """
    A class to create a trend report.

    Attributes:
        dictionary        (OrderedDict) populated with qc data from multiqc outputs required for each plot
        plots_html        (list) list for which plot html is appended to, to be added to final generated trend report
        runtype           (str) a html trend report is generated for each runtype specified in config.py
        input_folder      (str) path to MultiQC data per run
        output_folder     (str) path to save location for html trend reports and archive_index.html
        images_folder     (str) path to viapath logo images and saved plots
        runtype           (str) run type from list of run_types defined in config
        template_dir      (str) path to html templates
        archive_folder    (str) path to archived html reports
   """

    def __init__(self, input_folder, output_folder, images_folder, runtype, template_dir, archive_folder):
        """
        The constructor for TrendReport class
        """
        self.dictionary = OrderedDict({})
        self.plots_html = []
        self.runtype = runtype
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.images_folder = images_folder
        self.template_dir = template_dir
        self.archive_folder = archive_folder

    def call_tools(self, methods):
        """
        Function to call the tools in the class.
            :param methods: (list) Members of the TrendReport class

        Loops through the list of tools in config.plot_order, and for each:
            If the tool is applicable to the runtype (specified in per tool config dictionary - tool_settings):
                Print tool and run type.
            From list of parsed available modules in the class, if module defined by function property in tool config:
                Call that object and use it to parse the data, returning the run as a key and list of values
                (eg if  config.tool_settings[tool]["function"] == parse_multiqc_output, parse_multiqc_output function
                called and dictionary returned)
                If the dictionary is populated (might not find the expected inputs), create plot or table,
                using function defined by plot_type in the config for that tool
                If a plot or table has been constructed for the tool, create an html module module and append this to
                self.plots_html (list of plots html for this tool)
        After looping through all tools, generate a report and add report to the archived reports page.
        """
        for tool in config.plot_order:
            if config.tool_settings[tool][self.runtype]:
                print tool, self.runtype
                for name, obj in methods:
                    if config.tool_settings[tool]["function"] in name:
                        self.dictionary[tool] = obj(tool)
                        if self.dictionary[tool]:
                            self.build_plot(tool)
                        if any(key in self.dictionary[tool] for key in ["table_text", "image_location"]):
                            html_plot_module = self.populate_html_template(tool)
                            self.plots_html.append(html_plot_module)
        self.generate_report()
        self.generate_archive_html()

    def build_plot(self, tool):
        """
        Determine plot type required for each tool (as defined in config), call tool to build the plot, and append
        plot location to dictionary.
            :param tool: (str) allows access to tool specific config settings and of dictionary
        """
        if config.tool_settings[tool]["plot_type"] == "box_plot":
            self.box_plot(tool)
            self.dictionary[tool]["image_location"] = self.return_image_paths(tool)[1]
        elif config.tool_settings[tool]["plot_type"] == "stacked_bar":
            self.stacked_bar(tool)
            self.dictionary[tool]["image_location"] = self.return_image_paths(tool)[1]
        elif config.tool_settings[tool]["plot_type"] == "table":
            # table function returns the table html
            self.dictionary[tool]["table_text"] = self.table(tool)
        return

    def box_plot(self, tool):
        """
        Builds a box plot and saves the plot image to location defined in config.
            :param tool:                (str) allows access to tool specific config settings and of dictionary
            :return html_image_path:    (str) path to the saved plot

        Closes previous plots preventing previous data inclusion.
        Plots data from the dictionary[tool] dictionary (run name is the key, contains list of values), using labels
        generated by self.x_labels
        Horizontal lines added to define the cutoffs if specified in config (position and labels defined in config)
        (labels not currently working for some reason).
        Legends only added to plots with bound lines specified in the config file.
        Generate the image path using return_image_paths function and save figure at this location
        """
        plt.close()
        plt.boxplot(self.dictionary[tool].values(), labels=self.x_labels(tool))
        xmin, xmax, ymin, ymax = plt.axis()
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
        if (config.tool_settings[tool]["lower_lim_label"] is not False) or (
                config.tool_settings[tool]["upper_lim_label"] is not False):
            plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.xticks()
        plt.ticklabel_format(axis='y', useOffset=False, style='plain')
        image_path, _ = self.return_image_paths(tool)
        plt.savefig(image_path, bbox_inches="tight", dpi=200)
        return

    def stacked_bar(self, tool):
        """
        Creates a stacked bar chart from a dictionary input.
            :param tool: (str) allows access to tool specific config settings and of dictionary

        Closes previous plots preventing previous data inclusion.
        Converts the dictionary[tool] dictionary (run name is the key, contains list of values) to a pandas dataframe,
        with counts of true and false values for each run (peddy_sex_check).
        Replaces the run names in the dataframe with new x axis labels generated by self.x_labels
        Plots this dataframe as a bar chart, adding legend
        Generate the image path using return_image_paths function and save figure at this location
        """
        plt.close()
        # .apply(pd.value_counts) counts the number of 'True' and 'False' results per sample
        df = pd.DataFrame(self.dictionary[tool]).apply(pd.value_counts)
        # replaces run names with x axis labels
        df.columns = self.x_labels(tool)
        # T transforms dataframe so row index is now run names
        df.T.plot.bar(rot=0)
        plt.xticks()
        plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.ticklabel_format(axis='y', useOffset=False, style='plain')
        image_path, _ = self.return_image_paths(tool)
        plt.savefig(image_path, bbox_inches="tight", dpi=200)
        return

    def x_labels(self, tool):
        """
        Builds a list of x axis labels, from oldest to newest (using len of dictionary.keys()).
            :param tool:        (str) allows access to tool specific config settings and of dictionary
            :return xlabels:    (list) list of x labels from oldest to newest
        """
        xlabels = []
        for i in range(1, len(self.dictionary[tool].keys()) + 1):
            if i == 1:
                xlabels.append(str(i) + "\noldest")
            elif i == len(self.dictionary[tool].keys()):
                xlabels.append(str(i) + "\nnewest")
            else:
                xlabels.append(str(i))
        return xlabels

    def return_image_paths(self,tool):
        """
        Returns image paths using values defined in the config: images_folder, runtype (e.g. WES), and tool name.
            :param tool:                (str) allows access to tool specific config settings and of dictionary
            :return html_image_path:    (str) relative image path for use in html
            :return image_path:         (str) path to the saved plot
        """
        image_path = os.path.join(self.images_folder, self.runtype + "_" + tool + ".png")
        html_image_path = "images/" + self.runtype + "_" + tool + ".png"
        return image_path, html_image_path

    def table(self, tool):
        """
        Builds a html table using the template in the config file and the run names included in this trend analysis.
            :param tool:        (str) Tool name which allows access to tool-specific config settings and of dictionary
            :return rows_html:  (str) table html string

        The order of samples in the dictionary is sorted (as order of dictionary keys is not maintained)
        For each sample in the dictionary, a html string is added to rows_html, with the placeholders filled
        These rows will make up the table (dictionary key is placed in column 1, and its value in column 2 of hte table)
        """
        rows_html = ""
        table_row_html = "<tr><td >{}</td><td>{}</td></tr>"
        for i in sorted(self.dictionary[tool]):
            rows_html += table_row_html.format(i, self.dictionary[tool][i])
        # close table body tag
        rows_html += "</tbody>"
        return rows_html

    def populate_html_template(self, tool):
        """
        Builds a tool-specific html module for a single plot using a template within the config file.
            :param tool:    (str) Tool that is being plotted. Allows tool config and data to be accessed
            :return:        (html string) Populated html template

        Depending on required output for the tool (plot or table):
            Load the html template from the config (plot or table template)
            Define the html content as either the table text or the image location
        Returns the populated template for a single plot (populated with plot title, plot content, plot text and html content).
        """
        if config.tool_settings[tool]["plot_type"] == "table":
            template = config.table_template
            html_content = self.dictionary[tool]["table_text"]
        elif config.tool_settings[tool]["plot_type"] in ["box_plot", "stacked_bar"]:
            template = config.plot_template
            # Deals with browser caching - appends a GET value (the UNIX timestamp) to the image URL
            # Makes the browser think the image is dynamic, so reloads it every time the modification date changes
            # Means the new image is used when a new plot is generated, rather than the cached image
            if self.dictionary[tool]["image_location"]:
                html_content = os.path.join(
                self.dictionary[tool]["image_location"] + '?" . filemtime(' + self.dictionary[tool][
                        "image_location"] + ') . "')
        return template.format(config.tool_settings[tool]["plot_title"], config.tool_settings[tool]["plot_text"],
                               html_content)

    def generate_report(self):
        """
        Inserts all plot specific html segments into the report template.

        Loads report html template as a python object
        Creates a new file at generated_report_path location and writes the html template to the file, filling the
        placeholders (upon html rendering) with the placeholder values specified in the place_holder_values dictionary
        Saves html file as pdf (with all images) for long term records using pdfkit package and wkhtmltopdf software
        """
        html_template_dir = Environment(loader=FileSystemLoader(self.template_dir))
        html_template = html_template_dir.get_template("internal_report_template.html")
        generated_report_path = os.path.join(self.output_folder, self.runtype + "_trend_report.html")
        # self.plots_html (list of per-plot html sections) is joined into a single string, spaced with newline
        place_holder_values = {"reports": config.body_template.format("\n".join(self.plots_html)),
                                "logo_path": config.logopath,
                                "timestamp": datetime.datetime.now().strftime('%d-%B-%Y %H:%M'),
                                "app_version": git_tag()}
        with open(generated_report_path, "wb") as html_file:
            html_file.write(html_template.render(place_holder_values))
        # specify pdfkit options to turn off standard out and also allow access to the images
        # pdfkit needs the path tp wkhtmltopdf binary file - defined in config
        pdfkit_options = {'enable-local-file-access': None, "quiet": ''}
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=config.wkhtmltopdf_path)
        pdfkit.from_file(generated_report_path, os.path.join(self.archive_folder, str(
                        datetime.datetime.now().strftime('%y%m%d_%H_%M')) + "_" + self.runtype + "_trend_report.pdf"),
                        configuration=pdfkit_config, options=pdfkit_options)

    def generate_archive_html(self):
        """
        Adds the created trend report as a link to the archive_index.html.

        This means the archived version is therefore accessible after the live report has been replaced on the webpage
        with more recent runs.
        """
        html_path = os.path.join(self.output_folder, "archive_index.html")
        archive_directory = os.listdir(self.archive_folder)
        with open(html_path, "wb") as html_file:
            html_file.write('<html><head align="center">ARCHIVED TREND ANALYSIS REPORTS</head><body><ul>')
            html_file.writelines(['<li><a href="archive/%s">%s</a></li>' % (f, f) for f in archive_directory])
            html_file.write('</ul></body></html>')

    def describe_run_names(self, tool):
        """
        Populates a table with run names in order from oldest to newest (specified as a function to be used in the tool
        config).
            :param tool:                    (str) Tool that is being plotted. Allows tool config and data to be accessed
            :return run_name_dictionary:    (dict) dictionary with key as the order, and value the run name

        A list of date-sorted tool-specific run names is acquired from the sorted_runs function
        Builds a dictionary using numbers as keys, and values from sorted_run_list as value.
        "Oldest" and "newest" are added to the keynames for the newest and oldest runs.
        """
        sorted_run_list = sorted_runs(os.listdir(self.input_folder), self.runtype)
        run_name_dictionary = {}
        for i in range(1, len(sorted_run_list) + 1):
            if i == 1:
                run_name_dictionary[str(i) + " oldest"] = sorted_run_list[i - 1]
            elif i == len(sorted_run_list):
                run_name_dictionary[str(i) + " newest"] = sorted_run_list[i - 1]
            else:
                run_name_dictionary[str(i)] = sorted_run_list[i - 1]
        return run_name_dictionary


    def parse_multiqc_output(self, tool):
        """
        Creates a dictionary containing the relevant MultiQC data from each run.
        (specified as a function to be used in the tool config)
            :param tool:        (str) allows access to tool specific config settings and of dictionary
            :return tool_dict:  (OrderedDict) dictionary with run name as the key and value is a list of data points
                                 from the column of interest.

        The name of the tool-specific MultiQC file is acquired from the config file (tend to have a header line then
        one row per sample).
        A list of date-sorted tool-specific runfolders is acquired from the sorted_runs function.
        For each runfolder:
            The find_file_path function finds the tool-specific MultiQC file
            return_columns parses the file, returning relevant data
            Dictionary is built with run name as key and value as a list of data points.
        """
        # get the name of the raw data file
        input_file_name = config.tool_settings[tool]["input_file"]
        tool_dict = OrderedDict({})
        sorted_run_list = sorted_runs(os.listdir(self.input_folder), self.runtype)
        # for each run find the file and pass it to return_columns, which generates a list
        # add this to the dictionary
        for run in sorted_run_list:
            input_file = find_file_path(input_file_name, os.path.join(self.input_folder, run))
            # input_file = select_input_file(input_file_name, input_folder, run, tool)
            if input_file:
                tool_dict[run] = self.return_columns(input_file, tool)
        return tool_dict

    def return_column_index(self, input_file, tool):
        """
        Selects the column index of interest based on the column heading provided in the config file.
            :param input_file:      (str) name of raw data file (multiqc output file)
            :param tool:            (str) allows access to tool specific config settings and of dictionary
            :return column_index:   (int) index of the column of interest that contains the relevant data for plotting.
        """
        header_line = [input_file.readline().strip('\n').split("\t")]
        column_index = header_line[0].index(config.tool_settings[tool]["column_of_interest"])
        return column_index

    def return_columns(self, file_path, tool):
        """
        For a given file, open and for each line (excluding header if required) extract the column of interest as a float.
        If the tool is the cluster density plot, skips the first seven rows as these are headers.
        For all other plots, skips the first row as this is the header.
        Create and return a list of all measurements
            :param file_path:   (str) file to parse
            :param tool:        (str) tool name - allows access to tool specific config settings
            :return to_return:  (list) a list of measurements from the column of interest
        """
        # list for sample specific measurements
        to_return = []
        # open file
        with open(file_path, 'r') as input_file:
            # select column index of interest
            column_index = self.return_column_index(input_file, tool)
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
                 email_subject, email_message, hyperlink):
        self.input_folder = input_folder
        self.runtype = runtype
        self.wes_email = wes_email
        self.oncology_ops_email = oncology_ops_email
        self.custom_panels_email = custom_panels_email
        self.email_subject = email_subject
        self.mokaguys_email = config.mokaguys_email
        self.logfile_path = os.path.join(self.input_folder + '/{}/email_logfile')
        self.email_file = "email_logfile"
        self.email_message = email_message
        self.hyperlink = hyperlink

    def call_tools(self):
        """
        Call methods required for email sending.
        """
        # create runlist for all runs of the runtype
        run_list = sorted_runs(os.listdir(self.input_folder), self.runtype)
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
            run_folder = os.path.join(self.input_folder + '/' + run)
            # if the run has previously been analysed (logfile present and 'Email sent' logged)
            if find_file_path(self.email_file, run_folder) and \
                    open(find_file_path(self.email_file, run_folder), "r").read():
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
        place_holder_values = {
            "run_list": "\n".join(new_runs),
            "hyperlink": self.hyperlink,
            "version": git_tag()}
        message_body = self.email_message.format(**place_holder_values)

        if self.runtype == "WES":
            recipients = [self.wes_email, self.mokaguys_email]
        if self.runtype == "PANEL":
            recipients = [self.custom_panels_email, self.mokaguys_email]
        if self.runtype == "SWIFT":
            recipients = [self.oncology_ops_email, self.mokaguys_email]

        # create message object, set priority, subject, recipients, sender and body
        m = Message()
        m["X-Priority"] = str("3")
        m["Subject"] = self.email_subject.format(place_holder_values["run_list"])
        m['To'] = ", ".join(recipients)
        m['From'] = config.moka_alerts_email
        m.set_payload(message_body)

        # server details
        server = smtplib.SMTP(host=config.host, port=config.port, timeout=10)
        server.set_debuglevel(False)  # verbosity turned off - set to true to get debug messages
        server.starttls()
        server.ehlo()
        server.login(config.user, config.pw)
        server.sendmail(config.moka_alerts_email, recipients, m.as_string())
        return

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


def sorted_runs(run_list, runtype):
    """
    The runs should be plotted in date order, oldest to newest.
    The runs included in the analysis are saved in run specific folders, named with the runfolder name (002_YYMMDD_[*WES*,*NGS*,*ONC*])
    Extract the date of the run from the folder name and create an ordered list
        :param run_list: (list) List of run folders to be included in trend analysis
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
            dates[(int(run.split("_")[1]))] = run
        if runtype == "PANEL" and "NGS" in run and "WES" not in run:
            dates[(int(run.split("_")[1]))] = run
        if runtype == "SWIFT" and "ONC" in run:
            dates[(int(run.split("_")[1]))] = run
        if runtype == "NEXTSEQ_LUIGI" and "NB552085" in run:
            dates[(int(run.split("_")[1]))] = run
        if runtype == "NEXTSEQ_MARIO" and "NB551068" in run:
            dates[(int(run.split("_")[1]))] = run
        if runtype == "MISEQ_ONC" and "M02353" in run:
            dates[(int(run.split("_")[1]))] = run
        if runtype == "MISEQ_DNA" and "M02631" in run:
            dates[(int(run.split("_")[1]))] = run
        if runtype == "NOVASEQ_PIKACHU" and "A01229" in run:
            dates[(int(run.split("_")[1]))] = run

    # sort the list of dates, identify the full run name and append to sorted list
    sortedruns = []
    # if there are 2 runs on same day, both runs will be added for each date so use set()
    # sort the list of dictionary keys (dates) in ascending order (oldest first)
    for date in sorted(set(dates)):
        sortedruns.append(dates[date])
    # return the x most recent runs (x is defined in config)
    return sortedruns[-config.number_of_runs_to_include:]


def find_file_path(name, path):
    """
    Use os.walk to recursively search through all files in a folder
    Return the path to identified file
        :param name: (str) filename
        :param path: (str) path to the folder containing all QC files for that run
        :return: (str) path to file of interest. Only returned if the file exists for that run.
    """
    for root, dirs, files in os.walk(path):
        for filename in files:
            if name in filename:
                return os.path.join(root, filename)
    print "no output named {} for run {}".format(name, path)
    return False


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
    # set variables from config file, depending on whether run is development or production
    if args.dev:
        # if script run in development mode
        input_folder = config.dev_input_folder
        output_folder = config.dev_output_folder
        images_folder = config.dev_images_folder
        template_dir = config.dev_template_dir
        archive_folder = config.dev_archive_folder
        wes_email = config.dev_recipient
        oncology_ops_email = config.dev_recipient
        custom_panels_email = config.dev_recipient
        email_subject = config.dev_email_subject
        email_message = config.email_message
        hyperlink = config.dev_reports_link
        # copies current index file over from live environment
        copyfile(src=config.index_file, dst=config.dev_index_file)

        # create instance of TrendReport class, retrieve methods of TrendReport class
        # then call member function of TrendReport instance
        for runtype in config.run_types:
            # create instance of TrendReport class
            t = TrendReport(input_folder, output_folder, images_folder, runtype, template_dir, archive_folder)
            # retrieve methods of the TrendReport class
            methods = inspect.getmembers(t, predicate=inspect.ismethod)
            t.call_tools(methods)
            # create instance of Emails class
            e = Emails(input_folder, runtype, wes_email, oncology_ops_email, custom_panels_email, email_subject,
                           email_message,
                           hyperlink)
            e.call_tools()
    else:
        input_folder = config.input_folder
        output_folder = config.output_folder
        images_folder = config.images_folder
        template_dir = config.template_dir
        archive_folder = config.archive_folder
        wes_email = config.wes_email
        oncology_ops_email = config.oncology_ops_email
        custom_panels_email = config.custom_panels_email
        email_subject = config.email_subject
        email_message = config.email_message
        hyperlink = config.reports_link

        # create instance of TrendReport class, retrieve methods of TrendReport class
        # then call member function of TrendReport instance
        if check_for_update():
            for runtype in config.run_types:
                # create instance of TrendReport class
                t = TrendReport(input_folder, output_folder, images_folder, runtype, template_dir, archive_folder)
                # retrieve methods of the TrendReport class
                methods = inspect.getmembers(t, predicate=inspect.ismethod)
                t.call_tools(methods)
                # create instance of Emails class
                e = Emails(input_folder, runtype, wes_email, oncology_ops_email, custom_panels_email, email_subject,
                           email_message,
                           hyperlink)
                e.call_tools()

if __name__ == '__main__':
    main()
