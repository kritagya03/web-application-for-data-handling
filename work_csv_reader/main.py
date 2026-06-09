#DATA HANDLING WEB APPLICATION SOURCE CODE. The python environment used to run the code is
#not of importance. I have used venv to test and built this project. If any imports
#have not been accepted, simply pip install it in the terminal. This code must be uploaded
#to a server, where it will run. This is so users of the application have easy access to it
from flask import Flask, request, session
from markupsafe import escape
import numpy as np
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import csv
import os
import tempfile
import time
from datetime import datetime
import threading
from scipy.signal import find_peaks


#EXTRACT DATA: A function which extracts data from a file, which is seperated by the given delimiter. Note that the file must
#not be a csv file, even though it is interpreted as one. It can be any file as long as it is delimiter seperated properly
#and a plain text file format, as i discuss in the README
def extract_data(csvfile, delim):
    header = []
    data = []
    messages = []

    csvfile.seek(0)
    csvreader = csv.reader(csvfile, delimiter=delim)
    header = next(csvreader)
    for datapoint in csvreader:
        values = []

        for value in datapoint:
            try:        #Try to interpret the value in datapoint as a number or date-time, ...
                if ":" in str(value): 
                    try:        #Try to explicitly convert the value to date-time (faster), ...
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    except:     #... If not possible, try implicitly (slower)
                        dt = pd.to_datetime(value)

                    values.append(dt)
                    
                else:    
                    value_as_float = float(value)
                    values.append(value_as_float)

            except:     #... If not possible, this value will be overlooked in plotting due to being labled "ignore"
                values.append("ignore")
                if len(messages)<11: 
                    messages.append(f"Was unable to turn cell ({len(data) + 1} down, {len(values)} right) to a number. This value will be ignored in plotting. Cell value: {value}")
                elif len(messages)==11:
                    messages.append("More cells will be ignored in plotting. These 10 above are examples of which values")

        data.append(values)
                
    messages.append(f"File is done being read \n")

    return header, data, messages


#GENERATE DROPDOWN OPTIONS: A function which generates a dropdown list of the list of values in headers
def generate_dropdown_options(headers):
    options = ""
    for header in headers:
        options += f"""<option value="{str(escape(header))}">{str(escape(header))}</option>"""
    return options


#GENERATE DROPDOWN: Where GENERATE DROPDOWN OPTIONS generates the dropdown list, this function specifically generates
#the dropdown list on the second page of the application. This is dependant on the number of graphs the user wishes for, as
#is clear with the for-loop
def generate_dropdowns(num_graphs, headers):
    options=""
    for i in range(num_graphs):
        options += f"""Graph nr. {i+1} <br>
                        <label for= "x-axis{i}"> Choose your x-axis:</label>
                        <select id="x-axis{i}" name="x-axis{i}"> <!-- First dropdown list -->
                            {generate_dropdown_options(headers)}
                        </select>

                        <br>

                        <label for="y-axis{i}">Choose your y-axis:</label>
                        <select id="y-axis{i}" name="y-axis{i}"> <!-- Second dropdown list -->
                            {generate_dropdown_options(headers)}
                        </select>

                        <br><br>"""
    return options


#BINARY CONVERSION: A function which ensures that values over 32767 in the data file get minimized by 65536, as
#any values over 32767 must indicate that it was ignored that a 16-bit value contained a sign bit at the begining 
def binary_conversion(values):
    for i in range(len(values)):
        if values[i] > 32767:
            values[i] -= 65536


#PLOT SPIKES: A funcion / algorithm which computes from where to where in the plot there is a change in the y-axis which is
#larger than the given threshold. The function returns the x- and y-values which, when plotted, will reveal these spikes of
#data which are larger than the threshold. The range of each spike and where this spike exists between is also calulated
def plot_spikes(threshold, x_values, y_values, x_axis_name):
    x_values = np.array(x_values)
    y_values = np.array(y_values)

    upper_peaks, _ = find_peaks(y_values)
    lower_peaks, _ = find_peaks(-y_values)
    all_peaks = np.append(upper_peaks, lower_peaks)
    all_peaks = sorted(np.append(np.append([0], all_peaks), [len(y_values)-1]))
    all_y_values_peaks = y_values[all_peaks]
    
    soc_peaks=[]
    peak_index = 0
    first_round = True
    while peak_index < len(all_peaks):
        
        if first_round:
            next_index = peak_index + 1
            current_peak_index = peak_index
            soc_peaks.append(all_peaks[current_peak_index])
            while next_index < len(all_peaks) and abs(all_y_values_peaks[next_index] - all_y_values_peaks[current_peak_index]) < threshold:
                next_index+=1
                peak_index+=1
        
            first_round = False
            peak_index += 1
            continue

        soc_peaks.append(all_peaks[peak_index])

        if peak_index < len(all_y_values_peaks)-1:
            if abs(all_y_values_peaks[peak_index]-all_y_values_peaks[peak_index+1])<threshold:
                next_index = peak_index+2
                current_peak_index = peak_index
                peak_index += 1
                if all_y_values_peaks[current_peak_index+1] > all_y_values_peaks[current_peak_index]:
                    while(next_index < len(all_y_values_peaks) and 0 <= (all_y_values_peaks[next_index]-all_y_values_peaks[current_peak_index]) < threshold):
                        peak_index+=1
                        next_index+=1
                else:
                    while(next_index <= len(all_y_values_peaks)-1 and 0 <= (all_y_values_peaks[current_peak_index]-all_y_values_peaks[next_index]) < threshold):
                        peak_index+=1
                        next_index+=1


        peak_index += 1
    
    soc_peaks = np.array(soc_peaks)
    soc_y_values_peaks = y_values[soc_peaks]

    upper_peaks, _ = find_peaks(soc_y_values_peaks)
    lower_peaks, _ = find_peaks(-soc_y_values_peaks)
    all_peaks = np.append(upper_peaks,lower_peaks)
    all_peaks = sorted(np.append(np.append([0], all_peaks), [len(soc_peaks)-1]))

    messages = f"In total there are <b>{len(all_peaks) - 1} spikes</b> in the data that are over the set threshold {threshold}: <br><br>"
    for i in range(len(all_peaks)):
        if i != len(all_peaks) - 1:
            peak_index_1 = all_peaks[i]
            peak_index_2 = all_peaks[i + 1]
            messages += f"From {x_axis_name}'s {x_values[soc_peaks[peak_index_1]]} to {x_values[soc_peaks[peak_index_2]]} ---- Range of {abs(soc_y_values_peaks[peak_index_2] - soc_y_values_peaks[peak_index_1])}"
            messages += "<br><br>"

    return x_values[soc_peaks[all_peaks]], soc_y_values_peaks[all_peaks], messages


#ENSURE A STATIC DIRECTORY IS MADE
static_dir = os.path.join(os.getcwd(), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)


#ENSURE THAT THE STATIC DIRECTORY IS EMPTY: When the code is ran, the only file that should be
#in static is README.pdf. The other files must be residue from the privous time the code was ran. As i
#discuss more under BACKROUND FILE REMOVAL right below, this expects the code to be continously running
files = os.listdir(static_dir)
if files:
    for filename in files:
        if filename == "README.pdf":
            continue
        
        file_path = os.path.join(static_dir, filename)
        os.remove(file_path)


#--- WEBSITE ---

app = Flask(__name__)
app.secret_key = "secretkey"


#BACKROUND FILE REMOVAL: Where temp_files_time keeps track of all the temporary files created, and when they were created. If the file
#is older than 1 hour, it will soon be deleted. It is important to realize that this expects the code to be continously running, which
#should not be a problem, as servers which host web applications have it continously running, so it can reached at any time. It
#should also be noted that having files be deleted at a rate too fast could lead to the file being unreachable when attempted to be deleted.
#This is because it can be in the middle of processing (like generating the graphs...) when atempted to be deleted. This should lead to issues 
#with deletion of all files. Simply quit and re-run the code
file_expiry_time = 3600 #1 hour
temp_files_time = {}
def cleanup_old_files():
    while True:
        current_time = time.time()
        for file_name, creation_time in list(temp_files_time.items()):
            file_path = os.path.join(os.getcwd(), "static", file_name)
            if current_time - creation_time > file_expiry_time:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    del temp_files_time[file_name]
        time.sleep(5400) #1.5 hours

cleanup_thread = threading.Thread(target=cleanup_old_files)
cleanup_thread.daemon = True
cleanup_thread.start()


#THE FIRST PAGE: This is the first page that is presented to the user (route:/). Once a delimiter
#and number of graphs is submitted, this page reloads to show what has been chosen as the delimiter and 
#number of graphs. When a file is uploaded, THE SECOND PAGE enters 
#Explaining variables:
###text - A string where it is written all the text that is presented to to the user, 
#below where the file is chosen and uploaded. That includes a hyperlink to the README
###delimiter_text - A string of the information the user submits in the delimiter text box. if
#no delimiter is submitted, the delimiter will further be a comma (that is what the delimiter
#session becomes). If a delimiter is submitted, the submited will be the delimiter and delimiter_text
#will be updated so the user can understand what currently is the delimiter
###graphs_text - The same as delimiter_text, where the default number of graphs is one
@app.route("/")
def index():
    text = """<br><br><br> Upload your .csv formatted file here to be analysed and graphed for you :). <br><br><br>
    <b>INSTRUCTIONS - READ BEFORE USE:</b> <br><br>  
    <a href="/static/README.pdf" target="_blank">PDF of README</a>"""

    delimiter_text = str(escape(request.args.get("delimiter","")))
    if delimiter_text:
        session["delimiter"] = delimiter_text.strip()
        delimiter_text = "Your chosen delimiter: " + session.get("delimiter")
    else:
        session["delimiter"] = ","

    graphs_text = str(escape(request.args.get("num_graphs","")))
    if graphs_text:
        session["num_graphs"] = graphs_text
        graphs_text = "Your chosen number of graphs: " + session.get("num_graphs")
    else:
        session["num_graphs"] = "1"

    return  (f"""
            <form action="" method="get">
             
                Delimiter: <input type="text" name="delimiter">

                <br><br>

                <label for="num_graphs">Number of Graphs:</label>
                <select id="num_graphs" name="num_graphs"> <!-- First dropdown list -->
                    {generate_dropdown_options([1,2,3,4,5,6,7,8,9,10])}
                </select>
             
                <br><br>
                
                <input type="submit" value="Submit">
             
            </form>
             """
        + delimiter_text + "<br><br>" + graphs_text + "<br><br><br><br>" +
             """
            <form action="/upload" method="post" enctype="multipart/form-data" onsubmit="disableUploadButton()">
                <input type="file" name="file">
                <input type="submit" value="Upload" id="uploadButton">
            </form>

            <script>
                function disableUploadButton() {
                    document.getElementById('uploadButton').disabled = true;
                }
            </script>
             """
        + text)


#THE SECOND PAGE: This is the second page of the website (route:/upload). When a file is detected,
#a temporary file is made, which stores the information of the file. Data is then extracted from the
#temporary file, which is used to make dropdown lists of the headers and report if any problems occured
#during the reading of the file. Once the headers on the dropdown lists are picked and submitted , THE
#THID PAGE enters. If any problems occur during this process, the except block will
#be entered and the temporary file will be deleted if it exists
#Explaining variables:
###subrid / temp_file_path - Absolute paths to the static directory and temporary file, respectively
###result - A collection of all the messages made when extracting the data. This can be problems that 
#occurred during the extraction, and information that the file is done being read
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    delimiter= session.get("delimiter", ",")
    num_graphs = session.get("num_graphs", "1")

    if file is None or file.filename == "":
        return "No file was selected. Go back and try again"
    
    if file:
        try:
            csv_content = file.stream.read().decode("utf-8-sig")

            subdir = os.path.join(os.getcwd(), "static")
            temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", newline="", dir=subdir)
            
            #Storing the temporary file along with when it was made in the dictionary
            temp_files_time[str(temp_file.name)] = time.time()
            session["temp_file_name"] = temp_file.name
            
            temp_file.write(csv_content)
            temp_file.close()

            temp_file_path = os.path.join(subdir, os.path.basename(temp_file.name))
            with open(temp_file_path) as csv_data:
                headers, data, messages = extract_data(csv_data, delimiter)

            result = ""
            result += "<br><br>".join(messages)
            result += "<br><br>" + ""

            return (result + "<br><br>" +
            f""" 
            <form action="/plot" method="post" onsubmit="disableSubmitButton()">

                {generate_dropdowns(int(num_graphs), headers)}

                <input type="submit" value="Submit" id="submitButton">
                <br><br>

                <b>PLEASE</b> be patient <br><br>
    
            </form>

            <script>
                function disableSubmitButton() {{
                    document.getElementById('submitButton').disabled = true;
                }}
            </script>
            """)
        
        except Exception as e:
            if "temp_file" in locals(): 
                temp_file_path=os.path.join(os.getcwd(), "static",os.path.basename(temp_file.name))
                if not temp_file.closed:
                    temp_file.close()
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            return f"File is unreadable. <br> Make sure to read the instructions on the front page. Try again <br> ERROR : {e}"
    else:
        return f"File is unreadable. <br> Make sure to read the instructions on the front page. Try again"


#THE THIRD PAGE: This is the third page of the website (route:/plot). Depending on the number of graphs and
#which headers were chosen in THE SECOND PAGE, plots are made accordingly. If the user wishes to analyze the
#state of change of one of the graphs, THE FOURTH PAGE enters. If any problems occur during this process, the except 
#block will be entered and the temporary file will be deleted if it is found
#Explaining variables:
###plot_html - As stated, how many graphs is made is dependant on the number of graphs. When each graph is done being made in the
#end of the for-loop of this function, they are appended into plot_html in a way that html understands how to present on a web page. At
#the end of each loop, the question to analyze the state of change of that plot is also appended
###x_axis_name / y_axis_name - The headers that were chosen as the x-axis and y-axis in THE SECOND PAGE, where the names change depending
#on which graph is being plotted in this round of the for-loop 
###x_valus / y_values - A list of the values in the column of the chosen header, where if a value in either columns (x_values OR y_values)
#is supposed to be ignored, both lists will not include that data point to ensure correct dimensions
@app.route("/plot", methods=["POST"])
def plot_file():  
    try:
        delimiter= session.get("delimiter", ",")
        num_graphs = session.get("num_graphs", "1")
        temp_file_name = session.get("temp_file_name")

        subdir = os.path.join(os.getcwd(), "static")
        temp_file_path = os.path.join(subdir, os.path.basename(temp_file_name))
        with open(temp_file_path) as temp_file:
            headers, data, messages = extract_data(temp_file, delimiter)


        plot_html=""
        for i in range(int(num_graphs)):

            x_axis_name = str(escape(request.form.get(f"x-axis{i}")))
            y_axis_name = str(escape(request.form.get(f"y-axis{i}")))

            session[f"x-axis{i}"] = x_axis_name
            session[f"y-axis{i}"] = y_axis_name

            x_index = headers.index(x_axis_name)
            y_index = headers.index(y_axis_name)
            x_values = [p[x_index] for p in data if (p[x_index] != "ignore" and p[y_index] != "ignore")] 
            y_values = [p[y_index] for p in data if (p[y_index] != "ignore" and p[x_index] != "ignore")] 

            if any(isinstance(element, datetime) for element in x_values):
                binary_conversion(y_values)
                fig = px.line(x=x_values, y=y_values)
            else:
                binary_conversion(x_values)
                binary_conversion(y_values)
                fig = px.line(x=x_values, y=y_values)

            # Customization options
            fig.update_traces(line=dict(color="#1f77b4"))  
            fig.update_layout(
                width=1400, height=700,  
                plot_bgcolor='whitesmoke',
                font_color='black',
                title={
                'text': f'{y_axis_name} on {x_axis_name}',
                'font': {
                    'size': 30, 
                    'color': 'black'
                    }
                },
                xaxis=dict(
                    title = x_axis_name,
                    showgrid=True,
                    gridcolor='lightgrey', 
                    zerolinecolor = 'black',
                    linecolor='black',
                    linewidth=2,
                    mirror = True,
                    zeroline=False
                    ),
                yaxis=dict(
                    title = y_axis_name,
                    showgrid=True, 
                    gridcolor='lightgrey',
                    zerolinecolor = 'black',
                    linecolor='black',
                    linewidth=2,
                    mirror = True,
                    zeroline=False
                    ),
                )

            plot_html += pio.to_html(fig, full_html=False) + "<br>"
            plot_html += f"""Do you wish to analyze the <b>spikes in the data</b>?

                            <form action="/soc" method="post" onsubmit = "disableAllSubmitButtons()">
                                Threshold: <input type="text" name="threshold{i}">
                                <input type="submit" value="Submit">
                            </form>

                            <br><br><br>"""

        return f"""
                <b>NOTICE</b> that in the top right corner of each graph you have tools to zoom and adjust the graph to your preference

                <br><br><br>

                <div>{plot_html}</div>

                <script>
                    function disableAllSubmitButtons() {{
                        var buttons = document.querySelectorAll('input[type="submit"]');
                        buttons.forEach(function(button) {{
                            button.disabled = true;
                        }});
                    }}
                </script>
                """
    
    except Exception as e:
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return f"File could not be read <br>Make sure to read the instructions on the front page. Try again <br> ERROR: {e}"


#THE FOURTH PAGE: This is the fourth page of the website (route:/soc). A plot of the chosen graph and the spikes larger than the user's threshold 
#found in the data are presented. In addition, text is provided to the user of how many spikes there are, and where they are found. Notice that how the graph
#is plotted is different here than in THE THIRD PAGE. This is becuase two plots had to be plotted on the same graph. If any problems occur 
#during this process, the except block will be entered and the temporary file will be deleted if it is found
#Explaining variables:
###x_spikes / y_spikes - Two lists of peaks which, when plotted together, make the spikes on the graph that are larger than the threshold
###message - Contains all the text of how many spikes there are and where in the graph they can be found
@app.route("/soc", methods=["POST"])
def soc():
    try:
        delimiter= session.get("delimiter", ",")
        num_graphs = session.get("num_graphs", "1")
        temp_file_name = session.get("temp_file_name")

        threshold = 0
        iteration = 0
        for i in range(int(num_graphs)):
            threshold = str(escape(request.form.get(f"threshold{i}")))

            if threshold == "None":
                continue
            
            try:
                threshold=float(threshold)
            except:
                return "Not able to turn threshold into a number"

            iteration = i
            break

        x_axis_name = session.get(f"x-axis{iteration}", "")
        y_axis_name = session.get(f"y-axis{iteration}", "")

        subdir = os.path.join(os.getcwd(), "static")
        temp_file_path = os.path.join(subdir, os.path.basename(temp_file_name))
        with open(temp_file_path) as temp_file:
            headers, data, messages = extract_data(temp_file, delimiter)

        os.remove(temp_file_path)

        x_index = headers.index(x_axis_name)
        y_index = headers.index(y_axis_name)
        x_values = [p[x_index] for p in data if (p[x_index] != "ignore" and p[y_index] != "ignore")] 
        y_values = [p[y_index] for p in data if (p[y_index] != "ignore" and p[x_index] != "ignore")]

        if any(isinstance(element, datetime) for element in x_values):
            binary_conversion(y_values)
            line_trace = go.Scatter(x=x_values, y=y_values, mode='lines', name=y_axis_name, line=dict(color="#1f77b4"))
        else:
            binary_conversion(x_values)
            binary_conversion(y_values)
            line_trace = go.Scatter(x=x_values, y=y_values, mode='lines', name=y_axis_name, line=dict(color="#1f77b4"))

        # Customization options
        layout = go.Layout(
            width=1400, height=700,
            plot_bgcolor='whitesmoke',
            font_color="black",
            title={
                'text': f'{y_axis_name} on {x_axis_name}',
                'font': {
                    'size': 30,
                    'color': 'black'
                }
            },
            xaxis=dict(
                title = x_axis_name,
                showgrid=True,
                gridcolor='lightgrey',
                zerolinecolor='black',
                linecolor='black',
                linewidth=2,
                mirror=True,
                zeroline=False
            ),
            yaxis=dict(
                title = y_axis_name,
                showgrid=True,
                gridcolor='lightgrey',
                zerolinecolor='black',
                linecolor='black',
                linewidth=2,
                mirror=True,
                zeroline=False
            ),
        )

        x_spikes, y_spikes, message = plot_spikes(threshold, x_values, y_values, x_axis_name)
        scatter_trace = go.Scatter(
            x=x_spikes,
            y=y_spikes,
            mode='lines+markers',
            name='Spikes in Data',
            line=dict(color='red', dash='dash'),
            marker=dict(symbol='x-thin-open', color ='black', size=8)
        )


        fig = go.Figure(data=[line_trace, scatter_trace], layout=layout)
        plot_html = pio.to_html(fig, full_html=False)

        return f"""
                    <b>NOTICE</b> that in the top right corner of each graph you have tools to zoom and adjust the graph to your preference

                    <br><br><br>

                    <div>{plot_html}</div>

                    <br><br>

                    {message}
                    """
    
    except Exception as e:
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return f"File could not be read <br>Make sure to read the instructions on the front page. Try again <br> ERROR: {e}"



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=80, debug=True)