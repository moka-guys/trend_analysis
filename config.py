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
# Separate development and production settings ensure that the live MultiQC reports are not
# inadvertently updated during development work.

# General ---------------------------------------------------------------------------------------
# run_frequency:               Frequency (hours) the script runs (via cron). Defines window within which index.html
#                              File must fall to trigger a new trend analysis
# number_of_runs_to_include:   The x most recent runs
# run_types:                   Panels and individual sequencers
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
# input_folder:                Path to directory containing individual run folders (these contain per-run mutliqc files)
# output_folder:               Path to save location for html trend reports and archive_index.html
# images_folder:               Path to viapath logo and plot save location
# template_dir:                Path to html templates
# archive_folder:              Path to archived html reports
# reports_hyperlink:           Link to the trend analysis homepage from which the MultiQC reports can be accessed.
# wes_email:                   Recipient for completed WES trend analysis email alerts
# oncology_ops_email:          Recipient for completed SWIFT trend analysis email alerts
# custom_panels_email:         Recipient for completed custom panels trend analysis email alerts
# recipient:                   Recipient for emails sent out when testing during development. The mokaguys email address
# email_subject:               Email subject, with placeholders for inserting per-run inforamtion

general_config = {"general": {"run_frequency": 2,
                              "number_of_runs_to_include": 5,
                              "run_types": ["WES", "PANEL", "SWIFT", "NEXTSEQ_MARIO", "NEXTSEQ_LUIGI", "MISEQ_ONC",
                                            "MISEQ_DNA", "NOVASEQ_PIKACHU"],
                              "wkhtmltopdf_path": "/usr/local/bin/wkhtmltopdf",
                              "plot_order": ["run_names", "q30_percent", "picard_insertsize", "on_target_vs_selected",
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
                                  "template_dir": "/usr/local/src/mokaguys/development_area/trend_analysis/html_template",
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

tool_settings = {
    "run_names": {
        "function": "describe_run_names",
        "plot_type": "table",
        "plot_title": "Run names",
        "plot_text": "These are the runs included on the below plots. Numbers are used to simplify the x axis labels "
                     "on the plots, so this table can be used to link the axis labels to run name. Outliers are "
                     "displayed as circles, median as orange line, IQR as box",
        "conversion_to_percent": False,
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
            "SWIFT": "M02631",
            "NEXTSEQ_LUIGI": "NB552085",
            "NEXTSEQ_MARIO": "NB551068",
            "MISEQ_ONC": "M02353",
            "MISEQ_DNA": "M02631",
            "NOVASEQ_PIKACHU": "A01229"
        },
        "sequencer": ""
    },
    "picard_insertsize": {
        "function": "parse_multiqc_output",
        "input_file": "multiqc_picard_insertSize.txt",
        "plot_type": "box_plot",
        "column_of_interest": "MEAN_INSERT_SIZE",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "Picard Insert Sizes",
        "plot_text": "Boxplots showing the range and spread of insert sizes. This will highlight DNA fragmentation. "
                     "Outliers are displayed as circles, median as orange line, IQR as box",
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
            "NOVASEQ_PIKACHU": False
        },
    },
    "q30_percent": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_bcl2fastq_bylane.txt",
        "column_of_interest": "percent_Q30",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "BCL2Fastq Q30 percentage",
        "plot_text": "Boxplots showing the percentage of bases >= Q30. Values within each boxplot are for each lane.\n "
                     "This shows how well the base calling has performed on the sequencer. Outliers are displayed as "
                     "circles, median as orange line, IQR as box",
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
            "NEXTSEQ_LUIGI": "NB552085",
            "NEXTSEQ_MARIO": "NB551068",
            "MISEQ_ONC": "M02353",
            "MISEQ_DNA": "M02631",
            "NOVASEQ_PIKACHU": "A01229"
        },
    },
    "target_bases_at_30X": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_picard_HsMetrics.txt",
        "column_of_interest": "PCT_TARGET_BASES_30X",
        "header_present": True,
        "conversion_to_percent": True,
        "plot_title": "target_bases_at_30X",
        "plot_text": "Boxplot showing the % of bases in the target regions which are covered at >= 30X. Outliers are "
                     "displayed as circles, median as orange line, IQR as box",
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
            "NOVASEQ_PIKACHU": False
        },
    },
    "target_bases_at_20X": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_picard_HsMetrics.txt",
        "column_of_interest": "PCT_TARGET_BASES_20X",
        "conversion_to_percent": True,
        "header_present": True,
        "plot_title": "Target Bases at 20X",
        "plot_text": "Boxplot showing the % of bases in the target regions which are covered at >= 20X.\nSamples below "
                     "90% are failed. Samples above 95% pass. Samples between 90-95% may be analysed with caution. "
                     "Outliers are displayed as circles, median as orange line, IQR as box",
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
            "NOVASEQ_PIKACHU": False
        },
    },
    "on_target_vs_selected": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_picard_HsMetrics.txt",
        "column_of_interest": "ON_BAIT_VS_SELECTED",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "On target vs selected",
        "plot_text": "The % of on and near bait bases that are on as opposed to near (as defined by the BED file "
                     "containing the capture regions). Outliers are displayed as circles, median as orange line, "
                     "IQR as box",
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
            "NOVASEQ_PIKACHU": False
        },
    },
    "contamination": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_verifybamid.txt",
        "column_of_interest": "FREEMIX",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "Contamination",
        "plot_text": "The contamination estimate as calculated by VerifyBAMID (FREEMIX). A sample is considered "
                     "contaminated when FREEMIX > 0.03. Outliers are displayed as circles, median as orange line, "
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
            "NOVASEQ_PIKACHU": False
        },
        "sequencer": ""
    },
    "cluster_density_MiSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "illumina_lane_metrics",
        "column_of_interest": "## htsjdk.samtools.metrics.StringHeader",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "MiSeq Lane cluster density",
        "plot_text": "MiSeq sequencing run per-lane cluster density. Cluster density in thousands (K) of clusters per "
                     "mm2 of flowcell area for each sequencing lane. Optimal density for MiSeq is 1200-1400 K/mm2. "
                     "Outliers are displayed as circles, median as orange line, IQR as box",
        "upper_lim_linestyle": "solid",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": 'b',
        "upper_lim_linecolour": 'r',
        "upper_lim": 1400,
        "upper_lim_label": "Upper optimal density bound",
        "lower_lim": 1200,
        "lower_lim_label": "Lower optimal density bound",
        "report_type": {
            "WES": False,
            "PANEL": False,
            "SWIFT": "M02631",
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False
        },
        "sequencer": ""
    },
    "cluster_density_NextSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "illumina_lane_metrics",
        "column_of_interest": "## htsjdk.samtools.metrics.StringHeader",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "NextSeq Lane cluster density",
        "plot_text": "NextSeq sequencing run per-lane cluster density. Cluster density in thousands (K) of clusters "
                     "per mm2 of flowcell area for each sequencing lane. Optimal density for NextSeq is 170-230 K/mm2. "
                     "Outliers are displayed as circles, median as orange line, IQR as box",
        "upper_lim_linestyle": "solid",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": 'b',
        "upper_lim_linecolour": 'r',
        "upper_lim": 230,
        "upper_lim_label": "Upper optimal density bound",
        "lower_lim": 170,
        "lower_lim_label": "Lower optimal density bound",
        "report_type": {
            "WES": "NB551068, NB552085",
            "PANEL": "NB551068, NB552085",
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False
        },
        "sequencer": ""
    },
    "cluster_density_NovaSeq": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "illumina_lane_metrics",
        "column_of_interest": "## htsjdk.samtools.metrics.StringHeader",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "NovaSeq Lane cluster density",
        "plot_text": "NovaSeq sequencing run per-lane cluster density. Cluster density in thousands (K) of clusters "
                     "per mm2 of flowcell area for each sequencing lane. Optimal density for NovaSeq is ___ - ___ "
                     "K/mm2. Outliers are displayed as circles, median as orange line, IQR as box",
        "upper_lim_linestyle": "solid",
        "lower_lim_linestyle": "solid",
        "lower_lim_linecolour": 'b',
        "upper_lim_linecolour": 'r',
        "upper_lim": False,
        "upper_lim_label": "Upper optimal density bound",
        "lower_lim": False,
        "lower_lim_label": "Lower optimal density bound",
        "report_type": {
            "WES": "A01229",
            "PANEL": False,
            "SWIFT": False,
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False
        },
        "sequencer": ""
    },
    "properly_paired": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_samtools_flagstat.txt",
        "column_of_interest": "properly paired_passed_pct",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "Properly Paired",
        "plot_text": "The percentage of QC-passed reads that were properly paired. Properly paired = both mates of a "
                     "read pair map to the same chromosome, oriented towards one another, with a sensible insert size. "
                     "Note, the negative control is NOT included in this plot. Outliers are displayed as circles, "
                     "median as orange line, IQR as box",
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
            "SWIFT": "M02631",
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False
        },
        "sequencer": ""
    },
    "pct_off_amplicon": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_picard_pcrmetrics.txt",
        "column_of_interest": "PCT_OFF_AMPLICON",
        "conversion_to_percent": False,
        "header_present": True,
        "plot_title": "Percentage of Off Amplicon Bases",
        "plot_text": "The percentage of aligned passing filter (PF) bases that mapped neither on or near an amplicon. "
                     "This is a measure of primer specificity. Note, the negative control is  NOT included in this "
                     "plot. Outliers are displayed as circles, median as orange line, IQR as box",
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
            "SWIFT": "M02631",
            "NEXTSEQ_LUIGI": False,
            "NEXTSEQ_MARIO": False,
            "MISEQ_ONC": False,
            "MISEQ_DNA": False,
            "NOVASEQ_PIKACHU": False
        },
        "sequencer": ""
    },
    "fastq_total_sequences": {
        "function": "parse_multiqc_output",
        "plot_type": "box_plot",
        "input_file": "multiqc_fastqc.txt",
        "column_of_interest": "Total Sequences",
        "header_present": True,
        "conversion_to_percent": False,
        "plot_title": "Fastq Total Sequences",
        "plot_text": "Boxplot showing the total number of sequences. Outliers are displayed as circles, median as "
                     "orange line, IQR as box",
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
            "NOVASEQ_PIKACHU": False
        },
    },
    "peddy_sex_check": {
        "function": "parse_multiqc_output",
        "plot_type": "stacked_bar",
        "input_file": "multiqc_peddy.txt",
        "column_of_interest": "error_sex_check",
        "header_present": True,
        "conversion_to_percent": False,
        "plot_title": "Correct Sex",
        "plot_text": "Number of sample names with incorrect sex per run. The output is 'True' if the sex encoded in "
                     "the sample name matches that predicted by peddy. It is 'False' if it does not match the "
                     "prediction. e.g. sample name sex 'unknown' and peddy prediction 'male' would be 'False'.",
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
            "NOVASEQ_PIKACHU": False
        }
    }
}

# ==== HTML Templates ===================================================================
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
