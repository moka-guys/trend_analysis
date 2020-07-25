# source environment (may not be needed in a nexus app)
source ~/dx-toolkit/environment
# Get the apikey - need to be logged in to cat this.
# if running localy read from file
API_KEY=$(dx cat project-FQqXfYQ0Z0gqx7XG9Z2b4K43:mokaguys_nexus_auth_key)

#define input variables
run_group=WES
num_runs=5

# set up the dx find projects command for each input (WES,PANEL or ONC)
if [[ "$run_group" == "WES" ]]; then
    find_project_cmd="dx find projects --level ADMINISTER --name "002_*WES*" --auth-token $API_KEY"
fi 
if [[ "$run_group" == "ONC" ]]; then
    find_project_cmd="dx find projects --level ADMINISTER --name "002_*ONC*" --auth-token $API_KEY"
fi
if [[ "$run_group" == "PANEL" ]]; then
    find_project_cmd="dx find projects --level ADMINISTER --name "002_*NGS*" --auth-token $API_KEY | grep -v WES"
fi    

# execute dx find project command and loop through
for line in `$find_project_cmd`; do
    # looping through will split on empty space - we only want the line containing the project-id
    if [[ "$line" == project* ]]; then  
        project_id=$line
        # using project-id run dx describe to return the date created
        # pass output of dx describe --json into jq to extract date created field
        # the date created is provided in form of an epoch, eg num of milliseconds since a fixed point
        project_created_epoch=$(dx describe $project_id --json --auth-token $API_KEY | jq .created)
        # also capture project name, but remove leading and trailing quotations
        project_name=$(sed -e 's/^"//' -e 's/"$//' <<< $(dx describe $project_id --json --auth-token $API_KEY | jq .name))
        # write epoch and the project id to file
        echo $project_id $project_created_epoch $project_name >> ~/project_list.txt
    fi
done
#cat ~/project_list.txt

# sort the project list file on the epoch column in descending numerical order (newest first)
# filter list using head
# use cut to return just the project id (first column)
IFS=$'\n'
for line in `sort -k 2nr ~/project_list.txt | head -n $num_runs`; do
    project_name=$(echo $line | cut -f3 -d" ")
    project_id=$(echo $line | cut -f1 -d" ")
    mkdir -p QC_files/$project_name && cd QC_files/$project_name
    # use project id to download contents of QC folder
    # as some files do not have run specific names we can overwrite them (unlikely to be used)
    dx download $project_id:/QC --no-progress -f --recursive --auth-token $API_KEY 
    cd ../..
done
