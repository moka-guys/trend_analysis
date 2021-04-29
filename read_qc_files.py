from __future__ import division
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import os
import git
import shutil
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
import importlib
import tempfile
import numpy as np
import glob

def arg_parse():
    """
    Parses arguments supplied by the command line.
        :return: (Namespace object) parsed command line attributes

    Creates argument parser, defines command line arguments, then parses supplied command line arguments using the
    created argument parser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dev', action='store_true', help="uses development output file locations (ensures live"
                                                                 "reports aren't overwritten during development and "
                                                                 "testing)")
    return parser.parse_args()


def get_inputs(args):
    """
    Sets inputs using the config file and supplied command line arguments - production if no arguments supplied,
    development if --dev is supplied.
        :param args:        (Namespace object) parsed command line attributes
        :return inputs:     (OrderedDict) Dictionary with config setting name as key and setting as value

    Imports general config dictionary from config file, and then production or development dictionary dependent
    on whether the script is run in production or development mode.
    """
    inputs = config.general_config['general']
    if args.dev:
        inputs.update(config.general_config['development'])
        copyfile(src=config.general_config["production"]["index_file"], dst=inputs["index_file"])
    else:
        inputs.update(config.general_config['production'])
    return inputs


def get_panel_dict(github_repo, github_file, kit_list):
    """
    Returns a dictionary of vcp panel lists from the automated demultiplexing config file.
        :param github_repo:     (str) Https link to github repository
        :param github_file:     (str) Name of file of interest
        :param kit_list:        (str) List of names of capture kits
        :return panel_dict:     (OrderedDict) Dictionary with config setting name as key and setting as value

    Takes the cloned file from the github repository, searches each line for elements in the kit_list and extracts
    panel numbers from each into panel_dict
    """
    panel_dict = OrderedDict({})
    get_github_file(github_repo, github_file)
    with open(os.getcwd() + "/" + github_file, 'r') as github_file:
        for line in github_file:
            for panel_list in kit_list:
                if line.startswith("{}".format(panel_list)):
                    panel_dict[panel_list] = \
                        (line.replace("\"", "").split('[')[1].strip()).split(']')[0].strip().split(",")
    return panel_dict


def get_github_file(github_repo, github_file):
    """
    Clones a file from a github repository.
        :param github_repo:     (str) Https link to github repository
        :param github_file:     (str) Name of file of interest

    Creates a temporary dir, clones into that dir, copies the desired file from that dir, and removes the temporary
    dir.
    """
    t = tempfile.mkdtemp()
    git.Repo.clone_from(github_repo, t, branch='Production', depth=1)
    shutil.move(os.path.join(t, github_file), os.path.join(os.getcwd(), github_file))
    shutil.rmtree(t)


class TrendReport(object):
    """
    A class to create a trend report. A html trend report is generated for each runtype specified in config.py

    Attributes:
        dictionary        (OrderedDict) populated with qc data from multiqc outputs required for each plot
        plots_html        (list) list for which plot html is appended to, to be added to final generated trend report
        runtype           (str) run type from list of run_types defined in config
        panel_dict        (OrderedDict) populated with lists of panels that use each type of capture kit
        input_folder      (str) path to MultiQC data per run
        output_folder     (str) path to save location for html trend reports and archive_index.html
        images_folder     (str) path to viapath logo images and saved plots
        template_dir      (str) path to html templates
        archive_folder    (str) path to archived html reports
        logopath          (str) path to viapath logo
        plot_order        (str) Order of plots in report (top to bottom). Only plots in this list are included
        wkhtmltopdf_path  (str) Path to html conversion utility
   """

    def __init__(self, runtype, panel_dict, input_folder, output_folder, images_folder, template_dir, archive_folder,
                 logopath, plot_order, wkhtmltopdf_path):
        """
        The constructor for TrendReport class
        """
        self.dictionary = OrderedDict({})
        self.plots_html = []
        self.runtype = runtype
        self.panel_dict = panel_dict
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.images_folder = images_folder
        self.template_dir = template_dir
        self.archive_folder = archive_folder
        self.logopath = logopath
        self.plot_order = plot_order
        self.wkhtmltopdf_path = wkhtmltopdf_path

    def call_tools(self, methods):
        """
        Call methods in the class required for report generation.
            :param methods: (list) Members of the TrendReport class in a list of (name, value) pairs sorted by name

        Loop through list of tools in plot_order. For each:
            If tool applicable to runtype (specified in tool config dictionary):
                If method name in methods list is defined in function property in tool config:
                    Return method object (parse data), add to tool dictionary (key = run name, values = values) (eg if
                    config.tool_settings[tool]["function"] == parse_multiqc_output, call parse_multiqc_output and return
                    dictionary)
                    If dictionary populated (may not find expected input files for parsing), build plot for tool
                    If plot constructed, create html module and append to self.plots_html (list of plots html for tool)
        After looping through all tools, generate report and append to archived reports html
        """
        for tool in self.plot_order:
            if config.tool_settings[tool]["report_type"][self.runtype]:
                print('{} {}'.format(tool, self.runtype))
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
        Build plot required for tool. Call function to build plot (defined by plot_type in config for tool), append plot
        location to dictionary.
            :param tool: (str) Name of tool to be plotted (allows access to tool-specific config settings in
                               tool_settings dictionary)
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

    def box_plot(self, tool):
        """
        Build box plot from dictionary input. Save image to location defined in config.
            :param tool:                (str) Name of tool to be plotted (allows access to tool-specific config settings
                                              in tool_settings dictionary)

        Plot data from tool dictionary (key = run name, values = values), using labels generated by self.x_labels. Add
        horizontal lines to define cutoffs if specified in config, and labels to legends. Generate image path and save
        figure at this location.
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

    def stacked_bar(self, tool):
        """
        Build stacked bar chart from dictionary input. Save image to location defined in config.
            :param tool:    (str) Name of tool to be plotted (allows access to tool-specific config settings in
                                  tool_settings dictionary)

        Convert tool dictionary (key = run name, values = values) to pandas dataframe with counts of true and false
        values for each run. Plot as stacked bar chart (x labels generated by self.x_labels). Generate image path and
        save figure at this location.
        """
        plt.close()
        df = pd.DataFrame.from_dict(self.dictionary[tool],
                                    orient='index').apply(lambda x: pd.value_counts(x, normalize=True), axis=1).T
        df.columns = self.x_labels(tool)
        df.T.plot.bar(stacked=True)
        plt.xticks()
        plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.ticklabel_format(axis='y', useOffset=False, style='plain')
        image_path, _ = self.return_image_paths(tool)
        plt.savefig(image_path, bbox_inches="tight", dpi=200)

    def x_labels(self, tool):
        """
        Build list of x axis labels, from oldest to newest (using len of dictionary.keys()).
            :param tool:        (str) Name of tool to be plotted (allow access to tool-specific config settings in
                                      tool_settings dictionary)
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

    def return_image_paths(self, tool):
        """
        Return image paths using values defined in config: images_folder, runtype (e.g. WES), and tool name.
            :param tool:                (str) Name of tool to be plotted (allows access to tool-specific config settings
                                              in tool_settings dictionary)
            :return html_image_path:    (str) relative image path for use in html
            :return image_path:         (str) path to the saved plot
        """
        image_path = os.path.join(self.images_folder, self.runtype + "_" + tool + ".png")
        html_image_path = "images/" + self.runtype + "_" + tool + ".png"
        return image_path, html_image_path

    def table(self, tool):
        """
        Build html table using template in config file and run names in tool dictionary.
            :param tool:        (str) Name of tool to be plotted (allows access to tool-specific config settings in
                                      tool_settings dictionary)
            :return rows_html:  (str) table html string

        Sorts order of runs in dictionary (order of dictionary keys not maintained), and for each run a html
        string is added to rows_html and placeholders filled (dictionary key is placed in column 1, and its value in
        column 2 of the table row).
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
        Build tool-specific html module for single plot using template within config file.
            :param tool:    (str) Name of tool to be plotted (allows access to tool-specific config settings in
                                  tool_settings dictionary)
            :return:        (html string) Populated html template

        Load html template from config (plot or table template), define html content.
        If html content is an image, append a GET value (UNIX timestamp) to the image URL. Ensures a new image is used
        when plot is generated (bypasses browser caching), as forces browser to think image is dynamic (reloaded every
        time the modification date changes).
        Returns populated template for plot.
        """
        if config.tool_settings[tool]["plot_type"] == "table":
            template = config.table_template
            html_content = self.dictionary[tool]["table_text"]
        elif config.tool_settings[tool]["plot_type"] in ["box_plot", "stacked_bar"]:
            template = config.plot_template
            if self.dictionary[tool]["image_location"]:
                html_content = os.path.join(self.dictionary[tool]["image_location"] + '?" . filemtime(' +
                                            self.dictionary[tool]["image_location"] + ') . "')
        return template.format(config.tool_settings[tool]["plot_title"], config.tool_settings[tool]["plot_text"],
                               html_content)

    def generate_report(self):
        """
        Insert plot-specific html segments into report template.

        Load report html template as python object. Create new file at generated_report_path location and write html
        template to file, filling placeholders (upon html rendering) with placeholder values in place_holder_values
        dictionary. Save html file as pdf for long-term records using pdfkit package and wkhtmltopdf software
        """
        html_template_dir = Environment(loader=FileSystemLoader(self.template_dir))
        html_template = html_template_dir.get_template("internal_report_template.html")
        generated_report_path = os.path.join(self.output_folder, self.runtype + "_trend_report.html")
        place_holder_values = {"reports": config.body_template.format("\n".join(self.plots_html)),
                               "logo_path": self.logopath,
                               "timestamp": datetime.datetime.now().strftime('%d-%B-%Y %H:%M'),
                               "app_version": git_tag()}
        with open(generated_report_path, "wb") as html_file:
            html_file.write(html_template.render(place_holder_values))
        # specify pdfkit options to turn off standard out and also allow access to the images
        # pdfkit needs the path tp wkhtmltopdf binary file - defined in config
        pdfkit_options = {'enable-local-file-access': None, "quiet": ''}
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        pdfkit.from_file(generated_report_path, os.path.join(self.archive_folder, str(
                        datetime.datetime.now().strftime('%y%m%d_%H_%M')) + "_" + self.runtype + "_trend_report.pdf"),
                        configuration=pdfkit_config, options=pdfkit_options)

    def generate_archive_html(self):
        """
        Add created trend report as link to archive_index.html - archived version accessible after live report updated
        with more recent runs. Create list of all archived reports, sort by time last modified descending, cut
        filepaths down to filenames, add links to html.
        """
        html_path = os.path.join(self.output_folder, "archive_index.html")
        report_pdfs = []
        sorted_descending = []
        for report in os.listdir(self.archive_folder):
            report_pdfs.append(os.path.join(self.archive_folder, report))
        sorted_by_mtime_descending = sorted(report_pdfs, key=lambda t: -os.stat(t).st_mtime)
        for filepath in sorted_by_mtime_descending:
            sorted_descending.append(filepath.rsplit("/", 1)[-1])
        with open(html_path, "wb") as html_file:
            html_file.write('<html><head align="center">ARCHIVED TREND ANALYSIS REPORTS</head><body><ul>')
            html_file.writelines(['<li><a href="archive/%s">%s</a></li>' % (f, f) for f in sorted_descending])
            html_file.write('</ul></body></html>')

      #  sorted_by_mtime_descending = sorted(files, key=lambda t: -os.stat(t).st_mtime)

    def describe_run_names(self, tool):
        """
        Populate table with run names (sorted oldest to newest). Specified as function to be used in the tool config.
            :param tool:                    (str) Name of tool to be plotted (allows access to tool-specific config
                                                  settings in tool_settings dictionary)
            :return run_name_dictionary:    (dict) dictionary with key as the order, and value the run name

        Acquire date-sorted tool-specific run name list from sorted_runs, build dictionary using numbers as keys and
        values from sorted_run_list as values. "Oldest" and "newest" added to keynames for oldest/newest runs
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
        Create dictionary containing relevant per-run MultiQC data. Specified as function to be used in the tool config.
            :param tool:        (str) Name of tool to be plotted (allows access to tool-specific config settings in
                                      tool_settings dictionary)
            :return tool_dict:  (OrderedDict) Dictionary with run name as key and value as list of data from column of
                                              interest

        Name of tool-specific MultiQC file acquired from config file (generally header line then one row per sample).
        List of date-sorted tool-specific runfolders acquired from sorted_runs function.
        For each run, if from the correct sequencer for the plot, find the tool-specific MultiQC file. If this exists,
        return list of parsed relevant data as dictionary values. If MultiQC file does not exist, or run from the
        incorrect sequencer for the plot, return empty list as dictionary values.
        """
        input_file_name = config.tool_settings[tool]["input_file"]
        tool_dict = OrderedDict({})
        sorted_run_list = sorted_runs(os.listdir(self.input_folder), self.runtype)
        for run in sorted_run_list:
            if any(sequencer in run
                   for sequencer in config.tool_settings[tool]["report_type"][self.runtype].split(', ')):
                file_path = find_file_path(input_file_name, os.path.join(self.input_folder, run))
                if file_path:
                    tool_dict[run] = self.return_columns(file_path, tool)
                else:
                    tool_dict[run] = []
            else:
                tool_dict[run] = []
        return tool_dict

    def return_columns(self, file_path, tool):
        """
        Returns data from column of interest in file as a list.
            :param file_path:   (str) File to parse
            :param tool:        (str) Name of tool to be plotted (allows access to tool-specific config settings in
                                      tool_settings dictionary)
            :return to_return:  (list) Measurements from column of interest

        Open file, and return lines of interest as a list (lines contain data in the column of interest, and do not
        start with identifier_tuple elements (these are lines with no data)).
        For each line in this list, calculate the required measurement and return these as a list.
        """
        identifier_tuple = ("#", "Sample", "CLUSTER_DENSITY")
        to_return = []
        input_line_list = []
        with open(file_path, 'r') as input_file:
            column_index = self.return_column_index(input_file, tool)
            for line in input_file.readlines():
                if line.split("\t")[column_index] and not (line.isspace() or line.startswith(identifier_tuple)):
                    input_line_list.append(line)
            for line in input_line_list:
                measurement = self.calculate_measurement(input_line_list, line, column_index, tool)
                if measurement is not None:
                    to_return.append(measurement)
        return to_return

    def return_column_index(self, input_file, tool):
        """
        Return column index of column with heading matching column_of_interest in config file.
            :param input_file:      (file) Raw data file
            :param tool:            (str) Name of tool to be plotted (allows access to tool-specific config settings in
                                          tool_settings dictionary)
            :return column_index:   (int) Index of the column of interest
        """
        header_line = [input_file.readline().strip('\n').split("\t")]
        column_index = header_line[0].index(config.tool_settings[tool]["column_of_interest"])
        return column_index

    def calculate_measurement(self, input_line_list, line, column_index, tool):
        """
        Conducts required calculation on lines from input file.
            :param input_line_list: (str) list of all data-containing lines from multiqc input file
            :param line:            (str) one data-containing line from the input file
            :param column_index:    (int) index of column of interest containing relevant data for plotting
            :param tool:            (str) Name of tool to be plotted (allows access to tool-specific config settings in
                                          tool_settings dictionary)
            :return to_return:      (list) Measurements from column of interest

        Calculation differs by plot type (specified in config). Cluster density = /1000 to give cluster density.
        Contamination, and target bases plots = conversion to %. properly_paired and pct_off_amplicon = remove -ve
        controls. peddy_sex_check = exclude blank elements (not all lines contain sex check data).
        fastq_total_sequences = normalise by capture kit. All other plots no calculation required.
        """
        if config.tool_settings[tool]["calculation"] == "divide_by_1000":
            to_return = float(line.split("\t")[column_index]) / 1000
        elif config.tool_settings[tool]["calculation"] == "convert_to_percent":
            to_return = float(line.split("\t")[column_index]) * 100
        elif config.tool_settings[tool]["calculation"] == "remove_negative_controls":
            ntcon = ("NTCcon", "NTCCon")
            if any(string in line for string in ntcon):
                to_return = None
            else:
                to_return = float(line.split("\t")[column_index])
        elif config.tool_settings[tool]["calculation"] == "exclude_blank_elements":
            to_return = line.split("\t")[column_index]
        elif config.tool_settings[tool]["calculation"] == "normalise_by_capture_kit":
            # returns a list of True and false values per run
            to_return = self.normalise_by_kit(input_line_list, line, column_index)
        else:
            to_return = float(line.split("\t")[column_index])
        return to_return

    def normalise_by_kit(self, input_line_list, line, column_index):
        """
        Output True/False value for line dependent on whether value is within bounds.
            :param input_line_list: (str) list of all data-containing lines from multiqc input file
            :param line:            (str) one data-containing line from the input file
            :param column_index:    (int) index of column of interest containing relevant data for plotting
            :return to_return:      (boolean or NoneType) True or False values, or None

        If value of interest is within bounds, 'True' returned, else 'False' returned.
        WES runs: normalisation within capture kit not required so bounds calculated across all samples within run.
        Panel runs: normalisation required. For each capture kit type used by samples within run, upper/lower bounds
        calculated and samples within run compared to kit-specific bounds. For samples within run not using specified
        capture kit (panel number not in panel_dict list), those samples are discounted (return 'None').
        """
        upper_bound = lower_bound = None
        if "WES" in line:
            capture_kit = False
            upper_bound, lower_bound = self.calculate_bounds(input_line_list, capture_kit, 0.20, column_index)
            if lower_bound <= float(line.split("\t")[column_index]) <= upper_bound:
                to_return = True
            else:
                to_return = False
        else:
            for capture_kit in self.panel_dict:
                if any(pan_number in line for pan_number in self.panel_dict[capture_kit]):
                    upper_bound, lower_bound = self.calculate_bounds(input_line_list, capture_kit, 0.20, column_index)
                if None not in (upper_bound, lower_bound):
                    if lower_bound <= float(line.split("\t")[column_index]) <= upper_bound:
                        to_return = True
                    else:
                        to_return = False
                else:
                    to_return = None
        return to_return

    def calculate_bounds(self, input_line_list, capture_kit, proportion, column_index):
        """
        Calculate upper and lower bound for capture kit for input file
            :param input_line_list:             (str) list of all data-containing lines from multiqc input file
            :param capture_kit:                 (str) Name of capture kit
            :param proportion:                  (int) proportion value
            :param column_index:                (int) index of column of interest containing relevant data for plotting
            :return upper_bound, lower_bound:   (int or boolean) Upper and lower bound values, or True or False values.

        If capture kit supplied, append all values from samples using that kit to list, else append all values to list.
        If list not empty, calculates upper and lower bound and returns these. If list empty, return False.
        """
        values_list = []
        for line in input_line_list:
            if capture_kit:
                if any(pan_number in line.split("\t")[0] for pan_number in self.panel_dict[capture_kit]):
                    values_list.append(float(line.split("\t")[column_index]))
            else:
                values_list.append(float(line.split("\t")[column_index]))
        if values_list:
            average = sum(values_list) / len(values_list)
            upper_bound = average * (1.0+proportion)
            lower_bound = average * (1.0-proportion)
        else:
            upper_bound = lower_bound = False
        return upper_bound, lower_bound


class Emails(object):
    """
    A class to handle email sending and logs. Determines new runs, sends emails and creates logfiles

    Attributes:
        input_folder        (str) path to MultiQC data per run
        runtype             (str) run type from list of run_types defined in config
        wes_email           (str) recipient for completed WES trend analysis email alerts
        oncology_ops_email  (str) recipient for completed SWIFT trend analysis email alerts
        custom_panels_email (str) recipient for completed custom panels trend analysis email alerts
        mokaguys_email      (str) general bioinformatics emails - receives all sent out emails
        email_subject       (str) email subject, with placeholders for inserting per-run information
        email_message       (str) email body, with placeholders for inserting per-run information
        hyperlink           (str) link to MultiQC reports
    """

    def __init__(self, input_folder, runtype, wes_email, oncology_ops_email, custom_panels_email, mokaguys_email,
                 email_subject, email_message, hyperlink):
        self.input_folder = input_folder
        self.runtype = runtype
        self.wes_email = wes_email
        self.oncology_ops_email = oncology_ops_email
        self.custom_panels_email = custom_panels_email
        self.mokaguys_email = mokaguys_email
        self.email_subject = email_subject
        self.email_message = email_message
        self.hyperlink = hyperlink

    def call_tools(self):
        """
        Call methods in the class required for email sending.

        If runs of runtype are new, send trend report alert email to relevant team, and create logfile to record email
        sending.
        """
        run_list = sorted_runs(os.listdir(self.input_folder), self.runtype)
        new_runs = self.check_sent(run_list)
        if new_runs:
            self.send_email(new_runs)
            self.create_email_logfile(new_runs)

    def check_sent(self, run_list):
        """
        Check whether runs of runtype have previously been analysed (email logfile exists). Return list of new runs.
            :param run_list:    (list) Run folders to include in trend analysis
            :return new_runs:   (list) Runs not yet analysed

        Previously analysed runs contain logfile in runfolder, containing string with substring "email sent". If not
        previously analysed, append to new run list.
        """
        new_runs = []
        for run in run_list:
            run_folder = os.path.join(self.input_folder + '/' + run)
            email_logfile_path = find_file_path("email_logfile", run_folder)
            if email_logfile_path and ("email sent" in open(email_logfile_path, "r").read()):
                pass
            else:
                new_runs.append(run)
        return new_runs

    def send_email(self, new_runs):
        """
        Send email (using smtplib) per runtype for newly analysed runs to notify users of new trend report.
            :param new_runs:   (list) Runs not yet analysed

        Set recipients based on runtype. Create message object, set email priority, subject, recipients, sender, body.
        """
        place_holder_values = {"run_list": "\n".join(new_runs), "hyperlink": self.hyperlink, "version": git_tag()}
        message_body = self.email_message.format(**place_holder_values)

        if self.runtype == "WES":
            recipients = [self.wes_email, self.mokaguys_email]
        if self.runtype == "CUSTOM_PANELS":
            recipients = [self.custom_panels_email, self.mokaguys_email]
        if self.runtype == "SWIFT":
            recipients = [self.oncology_ops_email, self.mokaguys_email]

        if self.runtype in ["WES", "CUSTOM_PANELS", "SWIFT"]:
            m = Message()
            m["X-Priority"] = str("3")
            m["Subject"] = self.email_subject.format(self.runtype)
            m['To'] = ", ".join(recipients)
            m['From'] = config.general_config["general"]["sender"]
            m.set_payload(message_body)

            server = smtplib.SMTP(host=config.general_config["general"]["host"],
                                  port=config.general_config["general"]["port"], timeout=10)
            server.set_debuglevel(False)  # verbosity turned off - set to true to get debug messages
            server.starttls()
            server.ehlo()
            server.login(config.user, config.pw)
            server.sendmail(config.general_config["general"]["sender"], recipients, m.as_string())

    def create_email_logfile(self, new_runs):
        """
        Create logfile to record analysis of run/sending of notification email to relevant team.
            :param new_runs:   (list) Runs not yet analysed
        """
        for run in new_runs:
            logfile_path = os.path.join(self.input_folder + '/{}/email_logfile').format(run)
            with open(logfile_path, "w") as logfile_path:
                logfile_path.write(datetime.datetime.now().strftime(
                    '%d-%B-%Y %H:%M') + ": Run has been analysed and notification email sent")


def sorted_runs(run_list, runtype):
    """
    Filter runs of correct run type, order in date order (oldest to newest).
        :param run_list:    (list) Run folders to include in trend analysis
        :param runtype:     (str) run type from list of run_types defined in config
        :return             (list) x (defined in config) most recent runfolder names, ordered oldest to newest

    Take list of runfolders (e.g. 002_YYMMDD_[*WES*,*NGS*,*ONC*]), filter runs of correct runtype by substrings in run
    names, add to dictionary with name as value and date as key (cannot add date as key as dictionaries do not allow
    duplicate keys), sort in date order by value, return x most recent runs.
    """
    dates = {}
    for run in run_list:
        if runtype == "WES" and "WES" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "CUSTOM_PANELS" and "NGS" in run and "WES" not in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "SWIFT" and "ONC" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "NEXTSEQ_LUIGI" and "NB552085" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "NEXTSEQ_MARIO" and "NB551068" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "MISEQ_ONC" and "M02353" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "MISEQ_DNA" and "M02631" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "NOVASEQ_PIKACHU" and "A01229" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "TSO500" and "TSO500" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "SNP" and "SNP" in run:
            dates[run] = int(run.split("_")[1])
        if runtype == "ADX" and "ADX" in run:
            dates[run] = int(run.split("_")[1])

    sortedruns = []
    for date in sorted(dates, key=dates.get):
        sortedruns.append(date)
    return sortedruns[-config.general_config["general"]["number_of_runs_to_include"]:]


def find_file_path(name, path):
    """
    Recursively search for file (os.walk) through all files in folder and return path. If not present, print a message.
        :param name:    (str) filename
        :param path:    (str) path to the folder containing all QC files for that run
        :return:        (str or bool) path to file of interest if file exists, else False.
    """
    for root, dirs, files in os.walk(path):
        for filename in files:
            if name in filename:
                return os.path.join(root, filename)
    print("no output named {} for run {}".format(name, path))
    return False


def git_tag():
    """
    Return script release version number by reading directly from repository.
        :return: (str) returns version number of current script release

    Execute command via subprocess that prints git tags for git repository (e.g. v22-3-gccfd) and extracts version
    number (create array "a" using awk, split on "-" and print first element of array). Return standard out, removing
    newline characters
    """
    cmd = "git -C " + os.path.dirname(os.path.realpath(__file__)) + \
          " describe --tags | awk '{split($0,a,\"-\"); print a[1]}'"
    proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    return out.rstrip()


def check_for_update():
    """
    Determine whether index.html (contains links to multiqc report) has been modified in the last hour.
        :return: (bool) returns a Boolean value true or false

    Gets datetime that index.html was last modified. If date modified is more recent than frequency the script is run
    (now - timedelta), multiqc report has been added and function returns True, else returns False.
    """
    # see when the index.html file was last modified
    index_last_modified = datetime.datetime.utcfromtimestamp(os.path.getmtime(config.index_file))
    if index_last_modified >= datetime.datetime.now() - datetime.timedelta(hours=config.run_frequency):
        return True
    else:
        return False


def main():
    args = arg_parse()
    inputs = get_inputs(args)
    panel_dict = get_panel_dict(github_repo="https://github.com/moka-guys/automate_demultiplex",
                                github_file="automate_demultiplex_config.py",
                                kit_list=["vcp1_panel_list", "vcp2_panel_list", "vcp3_panel_list"])
    # If (run in dev mode), or (run in prod mode AND new run uploaded since script last run):
    # 1. Create instance of TrendReport class, retrieve methods of TrendReport class, then call call_tools (member
    # function of TrendReport instance) to generate the trend report
    # 2. Create instance of Emails class, then call call_tools (member function of Emails instance) to send emails
    if args.dev or check_for_update():
        for runtype in inputs["run_types"]:
            t = TrendReport(input_folder=inputs["input_folder"], output_folder=inputs["output_folder"],
                            images_folder=inputs["images_folder"], runtype=runtype, panel_dict=panel_dict,
                            template_dir=inputs["template_dir"], archive_folder=inputs["archive_folder"],
                            logopath=inputs["logopath"], plot_order=inputs["plot_order"],
                            wkhtmltopdf_path=inputs["wkhtmltopdf_path"])
            methods = inspect.getmembers(t, predicate=inspect.ismethod)
            t.call_tools(methods)
            e = Emails(input_folder=inputs["input_folder"], runtype=runtype, wes_email=inputs["wes_email"],
                       oncology_ops_email=inputs["oncology_ops_email"],
                       custom_panels_email=inputs["custom_panels_email"], mokaguys_email=inputs["mokaguys_email"],
                       email_subject=inputs["email_subject"], email_message=inputs["email_message"],
                       hyperlink=inputs["reports_hyperlink"])
            e.call_tools()


if __name__ == '__main__':
    main()
