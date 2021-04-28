import os

# ==== EMAIL CREDENTIALS LOCATION ===========================================================
# Root folder containing app directories and email credentials (2 levels up from this file)
# This sets the user and the password to be used in the script

document_root = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-2])
username_file_path = "{document_root}/.amazon_email_username".format(document_root=document_root)

with open(username_file_path, "r") as username_file:
    user = username_file.readline().rstrip()
pw_file = "{document_root}/.amazon_email_pw".format(document_root=document_root)
with open(pw_file, "r") as email_password_file:
    pw = email_password_file.readline().rstrip()

# ==== GENERAL CONFIG SETTINGS ================================================================

# Contains general, production and development config settings
# General settings are those that are applicable when running the script in production and development
# Production settings are those that are only used when the script is run in production
# Development settings are those that are only used when the script is run during development
# Separate development and production settings ensure that the live MultiQC reports are not inadvertently updated
# during development work.

# General ---------------------------------------------------------------------------------------
# run_frequency:               Frequency (hours) the script runs (via cron). Defines window within which index.html
#                              file must fall to trigger a new trend report to be generated
# number_of_runs_to_include:   The x most recent runs
# run_types:                   Run types and sequencer types
# wkhtmltopdf_path:            Path to html conversion utility
# plot_order:                  Order of plots in report (top to bottom). Only plots in this list are included
# logopath:                    Path to viapath logo
# mokaguys_email:              General bioinformatics email, which receives all sent out emails
# host:                        The host running the SMTP server
# port:                        Port, where SMTP server is listening
# sender:                      Address emails are sent from
# email_message:               Email body (for both dev and prod), with placeholders for inserting per-run information

# Production/development -------------------------------------------------------------------------
# index_file:                  Path to the index.html file (used for the main trend analysis homepage)
# input_folder:                Path to directory containing individual run folders (these contain per-run multiqc files)
# output_folder:               Path to save location for html trend reports and archive_index.html
# images_folder:               Path to viapath logo and plot save location
# template_dir:                Path to html templates
# archive_folder:              Path to archived html reports
# reports_hyperlink:           Link to the trend analysis homepage from which the MultiQC reports can be accessed.
# wes_email:                   Recipient for completed WES trend analysis email alerts
# oncology_ops_email:          Recipient for completed SWIFT trend analysis email alerts
# custom_panels_email:         Recipient for completed custom panels trend analysis email alerts
# email_subject:               Email subject, with placeholders for inserting per-run inforamtion

general_config = {"general": {"run_frequency": 2,
                              "number_of_runs_to_include": 5,
                              "run_types": ["WES", "PANEL", "SWIFT", "NEXTSEQ_MARIO", "NEXTSEQ_LUIGI", "MISEQ_ONC",
                                            "MISEQ_DNA", "NOVASEQ_PIKACHU"],
                              "wkhtmltopdf_path": "/usr/local/bin/wkhtmltopdf",
                              "plot_order": ["run_names", "q30_percent_MiSeq", "q30_percent_NextSeq",
                                             "q30_percent_NovaSeq", "picard_insertsize", "on_target_vs_selected",
                                             "target_bases_at_20X", "target_bases_at_30X", "cluster_density_MiSeq",
                                             "cluster_density_NextSeq", "cluster_density_NovaSeq", "contamination",
                                             "properly_paired", "pct_off_amplicon", "fastq_total_sequences",
                                             "peddy_sex_check"],
                              "logopath": "images/viapathlogo.png",
                              "mokaguys_email": "gst-tr.mokaguys@nhs.net",
                              "host": "email-smtp.eu-west-1.amazonaws.com",
                              "port": 587,
                              "sender": "moka.alerts@gstt.nhs.uk",
                              "email_message": """
                                                The MultiQC report is available for: 
                                                {run_list}       

                                                Trend analysis report has been updated to include these runs. 
                                                Available at {hyperlink}.

                                                Sent using trend_analysis {version} 
                                                """
                              },
                  "production": {"index_file": "/var/www/html/mokaguys/multiqc/index.html",
                                 "input_folder": "/var/www/html/mokaguys/multiqc/trend_analysis/multiqc_data",
                                 "output_folder": "/var/www/html/mokaguys/multiqc/trend_analysis",
                                 "images_folder": "/var/www/html/mokaguys/multiqc/trend_analysis/images/",
                                 "template_dir": "/usr/local/src/mokaguys/apps/trend_analysis/html_template",
                                 "archive_folder": "/var/www/html/mokaguys/multiqc/trend_analysis/archive",
                                 "reports_hyperlink": "https://genomics.viapath.co.uk/mokaguys/multiqc/",
                                 "wes_email": "WES@viapath.co.uk",
                                 "oncology_ops_email": "m.neat@nhs.net",
                                 "custom_panels_email": "DNAdutyScientist@viapath.co.uk, dnadutytechlead@viapath.co.uk",
                                 "email_subject": "MOKAPIPE ALERT : Finished pipeline for {} - MultiQC report "
                                                  "available and trend analysis updated"
                                 },
                  "development": {"index_file": "/var/www/html/mokaguys/dev/multiqc/index.html",
                                  "input_folder": "/var/www/html/mokaguys/dev/multiqc/trend_analysis/test_multiqc_data",
                                  "output_folder": "/var/www/html/mokaguys/dev/multiqc/trend_analysis",
                                  "images_folder": "/var/www/html/mokaguys/dev/multiqc/trend_analysis/images/",
                                  "template_dir":
                                      "/usr/local/src/mokaguys/development_area/trend_analysis/html_template",
                                  "archive_folder": "/var/www/html/mokaguys/dev/multiqc/trend_analysis/archive",
                                  "reports_hyperlink": "https://genomics.viapath.co.uk/mokaguys/dev/multiqc/",
                                  "wes_email": "gst-tr.mokaguys@nhs.net",
                                  "oncology_ops_email": "gst-tr.mokaguys@nhs.net",
                                  "custom_panels_email": "gst-tr.mokaguys@nhs.net",
                                  "email_subject": "TREND ANALYSIS TEST: Finished pipeline for {} - MultiQC report "
                                                   "available and trend analysis updated"
                                  }
                  }

# ==== TOOL-SPECIFIC SETTINGS ================================================================

# Contains config settings per plot (see plot_order list for full list of plots). Each plot is a dictionary key

# function:                 Specifies the function in read_qc_files.py to be applied for the tool
# plot_type:                Names the plot type for recognition by read_qc_files.py
# plot_title:               Plot title text
# plot_text:                Plot legend text
# calculation:              Specifies the type of calculation to be conducted on the parsed data before plotting
# upper_lim_linestyle:      Linestyle for upper bound/limit line
# lower_lim_linestyle:      Linestyle for lower bound/limit line
# lower_lim_linecolour:     Line colour for lower bound/limit line
# upper_lim_linecolour:     Line colour for upper bound/limit line
# upper_lim:                Value for upper limit line
# upper_lim_label:          Label text for upper limit line
# lower_lim:                Value for lower limit line
# lower_lim_label:          Label text for lower limit line
# report_type:              Sub-dictionary containing the report types and sequencer identifiers for filtering
#                           Sub dictionary values are False if plot is not required for this report type.
#   WES:                    Sequencer options are: "NB551068, NB552085, A01229"
#   PANEL:                  Sequencer options are: "NB551068, NB552085"
#   SWIFT:                  Sequencer options are: "M02631, M02353"
#   NEXTSEQ_LUIGI:          Sequencer options are: "NB552085"
#   NEXTSEQ_MARIO:          Sequencer options are: "NB551068"
#   MISEQ_ONC:              Sequencer options are: "M02353"
#   MISEQ_DNA:              Sequencer options are: "M02631"
#   NOVASEQ_PIKACHU:        Sequencer options are: "A01229"
#   TSO500:                 Sequencer options are: "NB551068, NB552085, A01229"
#   ADX:                    Sequencer options are: "M02631"
#   SNP:                    Sequencer options are: "M02631"

tool_settings = {
    "run_names": {
        "function": "describe_run_names",
        "plot_type": "table",
        "plot_title": "Run Names",
        "plot_text": "These are the runs included on the below plots. Numbers are used to simplify the x axis labels "
                     "on the plots, so this table can be used to link the axis labels to run name",
        "calculation": False,
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "",
        "lower_lim_linecolour": "",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": "NB551068, NB552085, A01229",
            "PANEL": "NB551068, NB552085",
            "SWIFT":  "M02631, M02353",
            "NEXTSEQ_LUIGI": "NB552085",
            "NEXTSEQ_MARIO": "NB551068",
            "MISEQ_ONC": "M02353",
            "MISEQ_DNA": "M02631",
            "NOVASEQ_PIKACHU": "A01229",
            "TSO500": "NB551068, NB552085, A01229",
            "ADX": "M02631",
            "SNP": "M02631"
        },
    },
    "picard_insertsize": {
        "function": "parse_multiqc_output",
        "input_file": "multiqc_picard_insertSize.txt",
        "plot_type": "box_plot",
        "column_of_interest": "MEAN_INSERT_SIZE",
        "calculation": False,
        "plot_title": "Picard Insert Sizes",
        "plot_text": "Boxplots showing the range and spread of insert sizes. This will highlight DNA fragmentation. "
                     "Boxes display the inter-quartile range (25th-75th percentile). Whiskers are 1.5 * IQR beyond "
                     "the boxes. Outliers are displayed as circles, and are data beyond the whiskers. Median is "
                     "displayed as an orange line",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": "r",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": 150,
        "lower_lim_label": "Minimum insert size cut-off",
        "report_type": {
            "WES": "NB551068, NB552085, A01229",
            "PANEL": "NB551068, NB552085",
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "q30_percent_MiSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_bcl2fastq_bylane.txt",
        "column_of_interest": "percent_Q30",
        "calculation": False,
        "plot_title": "BCL2Fastq Q30 Percentage MiSeq",
        "plot_text": "Boxplots showing the percentage of bases >= Q30. Values within each boxplot are for each lane. "
                     "This shows how well the base calling has performed on the sequencer. Boxes display the inter-"
                     "quartile range (25th-75th percentile). Whiskers are 1.5 * IQR beyond the boxes. Outliers are "
                     "displayed as circles, and are data beyond the whiskers. Median is displayed as an orange line",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "",
        "lower_lim_linecolour": "",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": False,
            "PANEL": False,
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": "M02353",
            "MISEQ_DNA": "M02631",
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "q30_percent_NextSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_bcl2fastq_bylane.txt",
        "column_of_interest": "percent_Q30",
        "calculation": False,
        "plot_title": "BCL2Fastq Q30 Percentage NextSeq",
        "plot_text": "Boxplots showing the percentage of bases >= Q30. Values within each boxplot are for each lane. "
                     "This shows how well the base calling has performed on the sequencer. Boxes display the inter-"
                     "quartile range (25th-75th percentile). Whiskers are 1.5 * IQR beyond the boxes. Outliers are "
                     "displayed as circles, and are data beyond the whiskers. Median is displayed as an orange line",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": "r",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": 75,
        "lower_lim_label": "Minimum cut-off",
        "report_type": {
            "WES": False,
            "PANEL": False,
            "SWIFT": False,
            "NEXTSEQ_LUIGI": "NB552085",
            "NEXTSEQ_MARIO": "NB551068",
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "q30_percent_NovaSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_bcl2fastq_bylane.txt",
        "column_of_interest": "percent_Q30",
        "calculation": False,
        "plot_title": "BCL2Fastq Q30 percentage NovaSeq",
        "plot_text": "Boxplots showing the percentage of bases >= Q30. Values within each boxplot are for each lane. "
                     "This shows how well the base calling has performed on the sequencer. Boxes display the inter-"
                     "quartile range (25th-75th percentile). Whiskers are 1.5 * IQR beyond the boxes. Outliers are "
                     "displayed as circles, and are data beyond the whiskers. Median is displayed as an orange line",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": "r",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": 85,
        "lower_lim_label": "Minimum cut-off",
        "report_type": {
            "WES": False,
            "PANEL": False,
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": "A01229",
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "target_bases_at_30X": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_picard_HsMetrics.txt",
        "column_of_interest": "PCT_TARGET_BASES_30X",
        "calculation": "convert_to_percent",
        "plot_title": "Target Bases at 30X",
        "plot_text": "Boxplot showing the % of bases in the target regions which are covered at >= 30X. Boxes display"
                     " the inter-quartile range (25th-75th percentile). Whiskers are 1.5 * IQR beyond the boxes. "
                     "Outliers are displayed as circles, and are data beyond the whiskers. Median is displayed as an "
                     "orange line",
        "upper_lim_linestyle": "dashed",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": 'r',
        "upper_lim_linecolour": 'k',
        "upper_lim": 95,
        "upper_lim_label": "95% at 30X",
        "lower_lim": 90,
        "lower_lim_label": "90% at 30X",
        "report_type": {
            "WES": False,
            "PANEL": "NB551068, NB552085",
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "target_bases_at_20X": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_picard_HsMetrics.txt",
        "column_of_interest": "PCT_TARGET_BASES_20X",
        "calculation": "convert_to_percent",
        "plot_title": "Target Bases at 20X",
        "plot_text": "Boxplot showing the % of bases in the target regions which are covered at >= 20X. Samples "
                     "below 90% are failed. Samples above 95% pass. Samples between 90-95% may be analysed with "
                     "caution. Boxes display the inter-quartile range (25th-75th percentile). Whiskers are 1.5 * IQR "
                     " the boxes. Outliers are displayed as circles, and are data beyond the whiskers. Median is "
                     "displayed as an orange line",
        "upper_lim_linestyle": "dashed",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": 'r',
        "upper_lim_linecolour": 'k',
        "upper_lim": 95,
        "upper_lim_label": "95% at 20X",
        "lower_lim": 90,
        "lower_lim_label": "90% at 20X",
        "report_type": {
            "WES": "NB551068, NB552085, A01229",
            "PANEL": False,
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "on_target_vs_selected": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_picard_HsMetrics.txt",
        "column_of_interest": "ON_BAIT_VS_SELECTED",
        "calculation": False,
        "plot_title": "On Target vs Selected",
        "plot_text": "The % of on and near bait bases that are on as opposed to near (as defined by the BED file "
                     "containing the capture regions). Boxes display the inter-quartile range (25th-75th percentile)."
                     " Whiskers are 1.5 * IQR beyond the boxes. Outliers are displayed as circles, and are data "
                     "beyond the whiskers. Median is displayed as an orange line",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "",
        "lower_lim_linecolour": "",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": "NB551068, NB552085, A01229",
            "PANEL": "NB551068, NB552085",
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "contamination": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_verifybamid.txt",
        "column_of_interest": "FREEMIX",
        "calculation": False,
        "plot_title": "Contamination",
        "plot_text": "The contamination estimate as calculated by VerifyBAMID (FREEMIX). A sample is considered "
                     "contaminated when FREEMIX > 0.03%. Outliers are displayed as circles, median as orange line, "
                     "IQR as box",
        "lower_lim_linestyle": "",
        "upper_lim_linestyle": "solid",
        "lower_lim_linecolour": "",
        "upper_lim_linecolour": 'r',
        "upper_lim": 0.03,
        "upper_lim_label": "Contamination threshold",
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": "NB551068, NB552085, A01229",
            "PANEL": False,
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "cluster_density_MiSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "illumina_lane_metrics",
        "column_of_interest": "## htsjdk.samtools.metrics.StringHeader",
        "calculation": "divide_by_1000",
        "plot_title": "MiSeq Lane Cluster Density",
        "plot_text": "MiSeq sequencing run per-lane cluster density. Cluster density in thousands (K) of clusters "
                     "per mm2 of flowcell area for each sequencing lane. Optimal density for MiSeq has not been "
                     "specified. Boxes display the inter-quartile range (25th-75th percentile). Whiskers are 1.5 * "
                     "IQR beyond the boxes. Outliers are displayed as circles, and are data beyond the whiskers. "
                     "Median is displayed as an orange line",
        "upper_lim_linestyle": "solid",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": 'b',
        "upper_lim_linecolour": 'r',
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": False,
            "PANEL": False,
            "SWIFT": "M02631, M02353",
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": "M02631",
            "SNP": False
        },
    },
    "cluster_density_NextSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "illumina_lane_metrics",
        "column_of_interest": "## htsjdk.samtools.metrics.StringHeader",
        "calculation": "divide_by_1000",
        "plot_title": "NextSeq Lane Cluster Density",
        "plot_text": "NextSeq sequencing run per-lane cluster density. Cluster density in thousands (K) of clusters "
                     "per mm2 of flowcell area for each sequencing lane. 290 K/mm2 is the upper cluster density "
                     "cut-off above which Q30 data should be examined. Boxes display the inter-quartile range "
                     "(25th-75th percentile). Whiskers are 1.5 * IQR beyond the boxes. Outliers are displayed as "
                     "circles, and are data beyond the whiskers. Median is displayed as an orange line",
        "upper_lim_linestyle": "solid",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": 'b',
        "upper_lim_linecolour": 'r',
        "upper_lim": 290,
        "upper_lim_label": "Upper optimal density bound",
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": "NB551068, NB552085",
            "PANEL": "NB551068, NB552085",
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": "NB551068, NB552085",
            "ADX": False,
            "SNP": False
        },
    },
    "cluster_density_NovaSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "illumina_lane_metrics",
        "column_of_interest": "## htsjdk.samtools.metrics.StringHeader",
        "calculation": "divide_by_1000",
        "plot_title": "NovaSeq Lane Cluster Density",
        "plot_text": "NovaSeq sequencing run per-lane cluster density. Cluster density in thousands (K) of clusters "
                     "per mm2 of flowcell area for each sequencing lane. There is currently no cluster density "
                     "cut-off for the NovaSeq. Boxes display the inter-quartile range (25th-75th percentile). "
                     "Whiskers are 1.5 * IQR beyond the boxes. Outliers are displayed as circles, and are data "
                     "beyond the whiskers. Median is displayed as an orange line",
        "upper_lim_linestyle": "solid",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": 'b',
        "upper_lim_linecolour": 'r',
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": "A01229",
            "PANEL": False,
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": "A01229",
            "ADX": False,
            "SNP": False
        },
    },
    "properly_paired": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_samtools_flagstat.txt",
        "column_of_interest": "properly paired_passed_pct",
        "calculation": "remove_negative_controls",
        "plot_title": "Properly Paired",
        "plot_text": "The percentage of QC-passed reads that were properly paired. Properly paired = both mates of a "
                     "read pair map to the same chromosome, oriented towards one another, with a sensible insert "
                     "size. Note, the negative control is NOT included in this plot. Boxes display the inter-"
                     "quartile range (25th-75th percentile). Whiskers are 1.5 * IQR beyond the boxes. Outliers are "
                     "displayed as circles, and are data beyond the whiskers. Median is displayed as an orange line",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "",
        "lower_lim_linecolour": "",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": False,
            "PANEL": False,
            "SWIFT":  "M02631, M02353",
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "pct_off_amplicon": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_picard_pcrmetrics.txt",
        "column_of_interest": "PCT_OFF_AMPLICON",
        "calculation": "remove_negative_controls",
        "plot_title": "Percentage of Off Amplicon Bases",
        "plot_text": "The percentage of aligned passing filter (PF) bases that mapped neither on or near an "
                     "amplicon. This is a measure of primer specificity. Note, the negative control is  NOT included "
                     "in this plot. Boxes display the inter-quartile range (25th-75th percentile). Whiskers are 1.5 "
                     "* IQR beyond the boxes. Outliers are displayed as circles, and are data beyond the whiskers. "
                     "Median is displayed as an orange line",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "",
        "lower_lim_linecolour": "",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": False,
            "PANEL": False,
            "SWIFT":  "M02631, M02353",
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "fastq_total_sequences": {
        "function": "parse_multiqc_output",
        "plot_type": "stacked_bar",
        "input_file": "multiqc_fastqc.txt",
        "column_of_interest": "Total Sequences",
        "calculation": "normalise_by_capture_kit",
        "plot_title": "Fastq Total Sequences",
        "plot_text": "Boxplot showing the proportion of samples in the run with total sequence number that falls "
                     "within 20% of the average for that run (for Custom Panels runs this is normalised by capture "
                     "kit). 'True' represents samples that fall within 20% of the average, 'False' represents samples "
                     "that do not",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "",
        "lower_lim_linecolour": "",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": "NB551068, NB552085, A01229",
            "PANEL": "NB551068, NB552085",
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        },
    },
    "peddy_sex_check": {
        "function": "parse_multiqc_output",
        "plot_type": "stacked_bar",
        "input_file": "multiqc_peddy.txt",
        "column_of_interest": "error_sex_check",
        "calculation": "exclude_blank_elements",
        "plot_title": "Correct Sex",
        "plot_text": "Proportion of sample names with incorrect sex per run. The output is 'True' if the sex encoded "
                     "in the sample name matches that predicted by peddy. It is 'False' if it does not match the "
                     "prediction. e.g. sample name sex 'unknown' and peddy prediction 'male' would be 'False'",
        "upper_lim_linestyle": "",
        "lower_lim_linestyle": "",
        "lower_lim_linecolour": "",
        "upper_lim_linecolour": "",
        "upper_lim": False,
        "upper_lim_label": False,
        "lower_lim": False,
        "lower_lim_label": False,
        "report_type": {
            "WES": "NB551068, NB552085, A01229",
            "PANEL": False,
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False,
            "TSO500": False,
            "ADX": False,
            "SNP": False
        }
    }
}

# ==== HTML Templates ===================================================================
# Templates used by read_qc_files.py to build tool-specific html modules, and generate individual trend reports.

# body_template     Template used to create the individual trend reports
# plot_template     Template used to create html blocks for each QC plot.
# table_template    Template used to create a html tables for each QC report.

body_template = '<div class="body" align="left">{}<br /></div>'

plot_template = \
    '<h2>{}</h2> \
    <div align="left"><br /><br /><br />{}.</div> \
    <div><img src="{}" alt="plotimage"></div> \
    <div class="clear">&nbsp;</div> \
    <hr width="90%" size="4" color="black">'

table_template = \
    '<h2>{}</h2> \
    <div align="left"><br /><br /><br />{}.</div> \
    <div> \
        <table border="1" width="60%" cellpadding="3" cellspacing="0">\n \
        \t<thead>\n \
        \t<tr style="text-align: centre;" bgcolor="#A8A8A8">\n \
        \t\t<th>Run Number</th>\n \
        \t\t<th>Run Name</th>\n \
        \t</tr>\n \
        </thead>\n \
        <tbody>\n{}\n</tbody>\n \
        </table> \
    </div> \
    <div class="clear">&nbsp;</div> \
    <hr width="90%" size="4" color="black">'
