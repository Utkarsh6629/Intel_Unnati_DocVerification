# Intel_Unnati_DocVerification
Problem Statement: Business Contract Validation- To classify content within the Contract Clauses & to determine deviations from Template & highlight them.

# How To Run
```
Step 1: Install Ollama from https://ollama.com/download
step 2: On command prompt run "ollama run dolphin-llama3".
        this will download the model and store it in cache
        (needs to be done only once and will take some time)
step 3: after this is done close the command prompt window and
        on a new terminal run "ollama serve".(this starts the ollama server)
        that is listening to port localhost:11434.
step 4: Install the prerequisites by running "pip install -r requirements.txt"
step 5: run the Python code and go to http://127.0.0.1:5000/ on your browser.
```
# Possible errors
```
1. Ollama error: Error: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address (protocol/network address/port) is normally permitted.

Here just check your processes and stop ollama and try again.
```
