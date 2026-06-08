#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
########################
import argparse, os, sys
p = os.getenv("pydiag_tools", os.path.dirname(os.path.realpath(__file__)))
if p not in sys.path: sys.path.insert(0, p)
import pydiag_tools as diag_tools

def create_index():
    parser = argparse.ArgumentParser( description = "Plot Ice Extent between Runs and Observations")
    parser.add_argument('-y', '--yaml', action = 'store', nargs = 1, \
        help="yaml file")
    args = parser.parse_args()
    config = diag_tools.utils.load_yaml(args.yaml[0])
    save_dir = config['save_dir']
    print(save_dir)
    ####################################
    # The name of the file we are creating
    output_file = save_dir + "/index.html"
    
    # Get all .html files in the current directory, excluding the index itself
    html_files = [f for f in os.listdir(save_dir) if f.endswith('.html') and f != output_file]
    html_files.sort()

    with open(output_file, "w") as f:
        f.write("<!DOCTYPE html>\n<html>\n<head>\n<title>Directory Index</title>\n")
        f.write("<style>body{font-family:sans-serif; padding:20px;} li{margin:8px 0;}</style>\n")
        f.write("</head>\n<body>\n")
        f.write(f"<h1>Files in {os.path.basename(os.getcwd())}</h1>\n<ul>\n")
        
        for file in html_files:
            f.write(f'  <li><a href="{file}">{file}</a></li>\n')
            
        f.write("</ul>\n</body>\n</html>")
    
    print(f"Successfully created {output_file} with {len(html_files)} links.")

if __name__ == "__main__":
    create_index()

