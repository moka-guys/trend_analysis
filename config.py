plot_order = ["run_names","q30_percent","picard_insertsize","on_target_vs_selected","target_bases_at_20X","contamination"]
tool_settings = {
    "run_names":{
        "function":"describe_run_names",
        "plot_type":"table",
        "plot_title":"Run names",
        "plot_text":"",
        "upper_lim_linestyle":"",
        "lower_lim_linestyle":"",
        "lower_lim_linecolour":"",
        "upper_lim_linecolour":"",
		"upper_lim": False,
		"upper_lim_label":False,
        "lower_lim": False,
		"lower_lim_label":False,
		"WES":True,
		"Panel":True,
		"ONC":True
    },
    "picard_insertsize":{
        "function":"parse_multiqc_output",
        "input_file":"multiqc_picard_insertSize.txt",
        "plot_type":"box_plot",
        "name_column":1,
        "column_of_interest":6,
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
		"Panel":False,
		"ONC":False
    },
    "q30_percent":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_bcl2fastq_bylane.txt",
        "name_column":1,
        "column_of_interest":-2,
        "header_present":True,
        "plot_title":"BCL2Fastq Q30 percentage",
        "plot_text":"Boxplots showing the percentage of bases >= Q30. Values within each boxplot are for each lane.\n This shows hoe well the base calling has performed on the sequencer",
        "upper_lim_linestyle":"",
        "lower_lim_linestyle":"",
        "lower_lim_linecolour":"",
        "upper_lim_linecolour":"",
        "upper_lim": False,
		"upper_lim_label":False,
        "lower_lim": False,
		"lower_lim_label":False,
		"WES":True,
		"Panel":False,
		"ONC":False
    },
    "target_bases_at_20X":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_picard_HsMetrics.txt",
        "name_column":1,
        "column_of_interest":33,
        "header_present":True,
        "plot_title":"target_bases_at_20X",
        "plot_text":"Boxplot showing the % of bases in the target regions which are covered at >= 20X.\nSamples below 90% are failed. Samples above 95% pass. Samples between 90-95% may be analysed with caution" ,
        "upper_lim_linestyle":"dashed",
        "lower_lim_linestyle":"solid",
        "lower_lim_linecolour":'r',
        "upper_lim_linecolour":'k',
        "upper_lim": 0.95,
        "upper_lim_label": "95% at 20X",
        "lower_lim": 0.90,
        "lower_lim_label": "90% at 20X",
		"WES":True,
		"Panel":False,
		"ONC":False
    },
    "on_target_vs_selected":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_picard_HsMetrics.txt",
        "name_column":0,
        "column_of_interest":8,
        "header_present":True,
        "plot_title":"on_target_vs_selected",
        "plot_text":"The % of on and near bait bases that are on as opposed to near (as defined by the BED file containing the capture regions." ,
        "upper_lim_linestyle":"",
        "lower_lim_linestyle":"",
        "lower_lim_linecolour":"",
        "upper_lim_linecolour":"",
		"upper_lim": False,
		"upper_lim_label":False,
        "lower_lim": False,
		"lower_lim_label":False,
		"WES":True,
		"Panel":False,
		"ONC":False
    },
    "contamination":{
        "function":"parse_multiqc_output",
        "plot_type":"box_plot",
        "input_file":"multiqc_verifybamid.txt",
        "name_column":0,
        "column_of_interest":11,
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
		"Panel":False,
		"ONC":False
    }
}

images_folder="/var/www/html/mokaguys/multiqc/trend_analysis/images/"
logopath=images_folder+"viapathlogo.png"
template_dir = 'html_template'
run_types = ["WES", "PANEL", "SWIFT"]
run_frequency = 2
index_file = "/var/www/html/mokaguys/multiqc/index.html"
input_folder = "/var/www/html/mokaguys/multiqc/trend_analysis/multiqc_data"
output_folder = "/var/www/html/mokaguys/multiqc/trend_analysis"

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

