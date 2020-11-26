# how frequenctly (in hours) the script will run (via cron) - this value defines the window which the index.html file date modified must fall within to trigger a new trend analysis
run_frequency = 2
number_of_runs_to_include = 5

# production folder paths
index_file = "/var/www/html/mokaguys/multiqc/index.html"
input_folder = "/var/www/html/mokaguys/multiqc/trend_analysis/multiqc_data"
output_folder = "/var/www/html/mokaguys/multiqc/trend_analysis"
images_folder = "/var/www/html/mokaguys/multiqc/trend_analysis/images/"
logopath = "images/viapathlogo.png"
template_dir = 'html_template'
archive_folder = "/var/www/html/mokaguys/multiqc/trend_analysis/archive"

# development folder paths
dev_input_folder = "/var/www/html/mokaguys/dev/multiqc/trend_analysis/test_multiqc_data"
dev_output_folder = "/var/www/html/mokaguys/dev/multiqc/trend_analysis"
dev_images_folder = "/var/www/html/mokaguys/dev/multiqc/trend_analysis/images/"
dev_index_file = "/var/www/html/mokaguys/dev/multiqc/index.html"
dev_archive_folder = "/var/www/html/mokaguys/dev/multiqc/trend_analysis/archive"

# pdf creation
wkhtmltopdf_path = "/usr/local/bin/wkhtmltopdf"

run_types = ["WES", "PANEL", "SWIFT", "NEXTSEQ_MARIO", "NEXTSEQ_LUIGI", "MISEQ_ONC", "MISEQ_DNA", "NOVASEQ_PIKACHU"]
#run_types = panels and individual sequencers

# This defines the order plots appear in the report (top to bottom) - Only plots in this list will be included on the report
plot_order = ["run_names","q30_percent","picard_insertsize","on_target_vs_selected","target_bases_at_20X","target_bases_at_30X","cluster_density_MiSeq","cluster_density_NextSeq","contamination"]

# tool specific settings
tool_settings = {
    "run_names":{
        "function":"describe_run_names",
        "plot_type":"table",
        "plot_title":"Run names",
        "plot_text":"These are the runs included on the below plots. Numbers are used to simplify the x axis labels on the plots, so this table can be used to link the axis labels to run name",
        "conversion_to_percent":False,
        "upper_lim_linestyle":"",
        "lower_lim_linestyle":"",
        "lower_lim_linecolour":"",
        "upper_lim_linecolour":"",
	    "upper_lim": False,
	    "upper_lim_label":False,
        "lower_lim": False,
	    "lower_lim_label":False,
        "WES":True,
	    "PANEL":True,
	    "SWIFT":True,
        "NEXTSEQ_LUIGI":True,
        "NEXTSEQ_MARIO":True,
        "MISEQ_ONC":True,
        "MISEQ_DNA":True,
        "NOVASEQ_PIKACHU":True
    },
    "picard_insertsize":{
        "function":"parse_multiqc_output",
        "input_file":"multiqc_picard_insertSize.txt",
        "plot_type":"box_plot",
        "name_column":1,
        "column_of_interest":6,
        "conversion_to_percent":False,
        "header_present":True,
        "plot_title":"Picard Insert Sizes",
        "plot_text":"Boxplots showing the range and spread of insert sizes. This will highlight DNA fragmentation",
        "upper_lim_linestyle":"",
        "lower_lim_linestyle":"",
        "lower_lim_linecolour":"",
        "upper_lim_linecolour":"",
	    "upper_lim": False,
	    "upper_lim_label":False,
        "lower_lim": False,
	    "lower_lim_label":False,
        "WES":True,
	    "PANEL":True,
	    "SWIFT":False,
        "NEXTSEQ_LUIGI": False,
        "NEXTSEQ_MARIO": False,
        "MISEQ_ONC": False,
        "MISEQ_DNA": False,
        "NOVASEQ_PIKACHU": False
    },
    "q30_percent":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_bcl2fastq_bylane.txt",
        "name_column":1,
        "column_of_interest":-2,
        "conversion_to_percent":False,
        "header_present":True,
        "plot_title":"BCL2Fastq Q30 percentage",
        "plot_text":"Boxplots showing the percentage of bases >= Q30. Values within each boxplot are for each lane.\n This shows how well the base calling has performed on the sequencer",
        "upper_lim_linestyle":"",
        "lower_lim_linestyle":"",
        "lower_lim_linecolour":"",
        "upper_lim_linecolour":"",
        "upper_lim": False,
	    "upper_lim_label":False,
        "lower_lim": False,
	    "lower_lim_label":False,
        "WES":False,
	    "PANEL":False,
        "SWIFT":False,
        "NEXTSEQ_LUIGI": True,
        "NEXTSEQ_MARIO": True,
        "MISEQ_ONC": True,
        "MISEQ_DNA": True,
        "NOVASEQ_PIKACHU": True
    },
    "target_bases_at_30X":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_picard_HsMetrics.txt",
        "name_column":1,
        "column_of_interest":10,
        "header_present":True,
	    "conversion_to_percent":True,
        "plot_title":"target_bases_at_30X",
        "plot_text":"Boxplot showing the % of bases in the target regions which are covered at >= 30X.",
        "upper_lim_linestyle":"dashed",
        "lower_lim_linestyle":"solid",
        "lower_lim_linecolour":'r',
        "upper_lim_linecolour":'k',
        "upper_lim": False,
        "upper_lim_label": "95% at 30X",
        "lower_lim": False,
        "lower_lim_label": "90% at 30X",
        "WES":False,
        "PANEL":True,
        "SWIFT":False,
        "NEXTSEQ_LUIGI": False,
        "NEXTSEQ_MARIO": False,
        "MISEQ_ONC": False,
        "MISEQ_DNA": False,
        "NOVASEQ_PIKACHU": False
    },
    "target_bases_at_20X":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_picard_HsMetrics.txt",
        "name_column":1,
        "column_of_interest":33,
        "conversion_to_percent":True,
        "header_present":True,
        "plot_title":"Target Bases at 20X",
        "plot_text":"Boxplot showing the % of bases in the target regions which are covered at >= 20X.\nSamples below 90% are failed. Samples above 95% pass. Samples between 90-95% may be analysed with caution" ,
        "upper_lim_linestyle":"dashed",
        "lower_lim_linestyle":"solid",
        "lower_lim_linecolour":'r',
        "upper_lim_linecolour":'k',
        "upper_lim": 95,
        "upper_lim_label": "95% at 20X",
        "lower_lim": 90,
        "lower_lim_label": "90% at 20X",
        "WES":True,
	    "PANEL":False,
	    "SWIFT":False,
        "NEXTSEQ_LUIGI": False,
        "NEXTSEQ_MARIO": False,
        "MISEQ_ONC": False,
        "MISEQ_DNA": False,
        "NOVASEQ_PIKACHU": False
    },
    "on_target_vs_selected":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_picard_HsMetrics.txt",
        "name_column":0,
        "column_of_interest":8,
        "conversion_to_percent":False,
        "header_present":True,
        "plot_title":"On targetvs selected",
        "plot_text":"The % of on and near bait bases that are on as opposed to near (as defined by the BED file containing the capture regions)." ,
        "upper_lim_linestyle":"",
        "lower_lim_linestyle":"",
        "lower_lim_linecolour":"",
        "upper_lim_linecolour":"",
	    "upper_lim": False,
	    "upper_lim_label":False,
        "lower_lim": False,
	    "lower_lim_label":False,
        "WES":True,
	    "PANEL":True,
	    "SWIFT":False,
        "NEXTSEQ_LUIGI": False,
        "NEXTSEQ_MARIO": False,
        "MISEQ_ONC": False,
        "MISEQ_DNA": False,
        "NOVASEQ_PIKACHU": False
    },
    "contamination":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_verifybamid.txt",
        "name_column":0,
        "column_of_interest":11,
        "conversion_to_percent":False,
        "header_present":True,
        "plot_title":"Contamination",
        "plot_text":"The contamination estimate as calculated by VerifyBAMID (FREEMIX). A sample is considered contaminated when FREEMIX > 0.03",
        "lower_lim_linestyle":"",
        "upper_lim_linestyle":"solid",
        "lower_lim_linecolour":"",
        "upper_lim_linecolour":'r',
	    "upper_lim": 0.03,
	    "upper_lim_label":False,
        "lower_lim": False,
	    "lower_lim_label":False,
	    "WES":True,
	    "PANEL":False,
	    "SWIFT":False,
        "NEXTSEQ_LUIGI": False,
        "NEXTSEQ_MARIO": False,
        "MISEQ_ONC": False,
        "MISEQ_DNA": False,
        "NOVASEQ_PIKACHU": False
    },
    "cluster_density_MiSeq":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"illumina_lane_metrics",
        "name_column":0,
        "column_of_interest":0,
        "conversion_to_percent":False,
        "header_present":True,
        "plot_title":"MiSeq Lane cluster density",
        "plot_text":"MiSeq sequencing run per-lane cluster density. Cluster density in thousands (K) of clusters per mm2 of flowcell area for each sequencing lane. Optimal density for MiSeq is 1200-1400 K/mm2.",
        "upper_lim_linestyle":"solid",
        "lower_lim_linestyle":"solid",
        "lower_lim_linecolour":'r',
        "upper_lim_linecolour":'r',
	    "upper_lim": 1400,
	    "upper_lim_label":False,
        "lower_lim": 1200,
	    "lower_lim_label":False,
        "WES":False,
	    "PANEL":False,
	    "SWIFT":True,
        "NEXTSEQ_LUIGI":False,
        "NEXTSEQ_MARIO":False,
        "MISEQ_ONC":False,
        "MISEQ_DNA":False,
        "NOVASEQ_PIKACHU":False
    },
    "cluster_density_NextSeq":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"illumina_lane_metrics",
        "name_column":0,
        "column_of_interest":0,
        "conversion_to_percent":False,
        "header_present":True,
        "plot_title":"NextSeq Lane cluster density",
        "plot_text":"NextSeq sequencing run per-lane cluster density. Cluster density in thousands (K) of clusters per mm2 of flowcell area for each sequencing lane. Optimal density for NextSeq is 170-230 K/mm2.",
        "upper_lim_linestyle":"solid",
        "lower_lim_linestyle":"solid",
        "lower_lim_linecolour":'r',
        "upper_lim_linecolour":'r',
	    "upper_lim": 230,
	    "upper_lim_label":False,
        "lower_lim": 170,
	    "lower_lim_label":False,
        "WES":True,
	    "PANEL":True,
	    "SWIFT":False,
        "NEXTSEQ_LUIGI":False,
        "NEXTSEQ_MARIO":False,
        "MISEQ_ONC":False,
        "MISEQ_DNA":False,
        "NOVASEQ_PIKACHU":False
    }
}


# HTMLtemplates
body_template = '<div class="body" align="left">{}<br /></div>'

plot_template= \
        '<h2>{}</h2> \
        <div align="left"><br /><br /><br />{}.</div> \
		<div><img src="{}" alt="plotimage"></div> \
        <div class="clear">&nbsp;</div> \
	    <hr width="90%" size="4" color="black">'

table_template= \
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

