# trend_analysis_v1.2
The main script in this repository is `read_qc_files.py`
This script is designed to run on the viapath genomics server and creates a trend analysis report for each test type and sequencer using data files output by multiqc.

## Requirements
* Python 2.7
* python packages as described in requirements.txt
* python-tk (v2.7.12-1~16.04)
* wkhtmltopdf (0.12.6-1.xenial_amd64) - When running headless this should be downloaded from github so the repo includes a patches version of QT (not included when instlaling from apt repositories)

## How does read_qc_files.py work?
###  Inputs
* A directory containing one directory per runfolder
* Tool specific settings (in the config file)

### Steps
#### Checking if new trend analysis is required
* The index.html file is updated whenever a new multiqc report is uploaded
* The date modified timestamp is assessed to see if it's within the last x hours (where x is the frequency the script is run - config.run_frequency)

#### Create run type specific trend analysis plot
* For each run type (defined in config.run_types)
* Loop through the ordered list of tools (arranging the order of plots in trend report) that are relevant to the run type
* The function used to parse the output (defined in the config file) is called. 
* This should return a dictionary, where the key is the runfolder and the value a list of measurements
* This data is then plotted using the plot type (defined in the config)
* Plots can have upper and lower thresholds defined, with customisable colours/linestyles
* Each plot has a title and a brief description
* The plot is returned in a html block

#### Create run type-specific trend analysis report
* The individual plots are inserted into the report html template
* The html page is saved to /var/www/html/mokaguys/multiqc/trend_analysis/{runtype}\_trend_report.html
* A PDF version of the webpage is also saved in /var/www/html/mokaguys/multiqc/trend_analysis/archive named with a time stamp for long term storage

#### Emails and logfiles
* For each run for each run type the script checks for the presence of an email logfile
* If email logfile is present and contains email sending log, no emails are sent
* If email logfile is not present, email is sent to the relevant address and a logfile is created and written to

### Runs included in the report
* The runs present on the server are filtered depending on run type and the name parsed to extract the date.
* The most recent x number of runs are included on the report (where x is defined by config.number_of_runs_to_include)

### Run/sequencer types
Runs are categorised by run type and sequencer by the script, which checks for the following identifiers in the run name:

| Run type | Run name |
| ----------|-----------|
| Custom Panels | Presence of "NGS" and "WES" |
| SWIFT | Presence of "NGS" and absence of "WES" |
| NextSeq (Luigi) | Presence of "NB552085" |
| NextSeq (Mario) | Presence of "NB551068" |
| MiSeq (Molecular Oncology) | Presence of "M02353" |
| MiSeq (DNA Lab) | Presence of "M02631" |
| NovaSeq (Pikachu) | Presence of "A01229" |

### index.html 
The index.html file contains links to the individual MultiQC reports, and to the WES, Custom Panels and SWIFT trend reports, and the archived reports. It also contains a link to a sequencers.html file which links to each sequencer-specific trend report. 

### Development mode
* The script can be run during development using the argument '--dev'
* This provides an alternative path for outputs to prevent live reports from being altered

### Testing mode
