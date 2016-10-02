# Setting up SMAC for Clojush

Configuration and scripts for using SMAC to optimize Clojush paramters

## Install SMAC

The SMAC website: http://www.cs.ubc.ca/labs/beta/Projects/SMAC/

It's worth noting that the SMAC 2 (the current version) is in Java, but apparently SMAC 3 will be in Python.

Download SMAC tar file from SMAC website:

```
curl http://www.cs.ubc.ca/labs/beta/Projects/SMAC/smac-v2.10.03-master-778.tar.gz -o smac.tgz
```

Extract the contents. SMAC is already compiled and the necessary `jar` files are in the `lib` directory. The Unix executable shell script `smac` starts everything off.

I linked the big long `smac...` directory to just `smac` so you can refer to `~nmcphee/smac` to get to this installation of SMAC.

## Install `runsolver`

`runsolver` (http://www.cril.univ-artois.fr/~roussel/runsolver/) is a C program that allows you to run a program with specified resource limits. This is how we limit individual Clojush runs to be no more than an hour.

`curl http://www.cril.univ-artois.fr/~roussel/runsolver/runsolver-3.3.5.tar.bz2 -o runsolver.bz2`

Extrac the contents. Go into the `src` directory and build with `make`.

I have `runsolver` in my home directory on fly, so

```
~nmcphee/runsolver/src/runsolver
```

will run `runsolver`.

## Set up SMAC configuration files

To run SMAC we need three configuration files:

* A `.pcs` file that specifies which parameters we want to let SMAC manipulate, and over what ranges.
* A `scenario` file that sets a number of SMAC variables such as how long to run SMAC.
* A Python file (or other script or program) that acts as the "go between" connecting SMAC and your system (Clojush in our case).

### PCS file

The PCS file specifies the parameters and ranges of values that SMAC will work with. An example would be:

```
popsize integer [1, 30000] [1000] log
selection categorical {:tournament, :lexicase} [:lexicase]
alt_prob [0, 1] [0.2]
uni_mut_prob [0, 1] [0.2]
uni_close_mut [0, 1] [0.1]
alt_mut [0, 1] [0.5]
alt_rate [0, 1] [0.01]
alignment_dev integer [0, 400] [10]
uni_mut_rate [0, 1] [0.1]
```

Each line contains:

* The parameter name, e.g., `popsize`
* An optional parameter type, e.g., `integer` or `categorical`. Parameters are assumed to be floating point values unless another type is specified.
* Possible values depending on parameter type:
  * A range of values in square brackets, e.g., `[1, 30000]`
  * A set of categorical values in curly braces, e.g., `{:tournament, :lexicase}`
* The default value in square brackets, e.g., `[1000]`
* An optional `log` specifier. If this is provided it causes "mutations" to be larger for large parameter values and smaller for small values. Without the `log` specifier, changes to values are uniform across the range.

The example above includes a number of parameters affecting the application of genetic operators, using the default values from @thelmuth's dissertation.

### Scenario file

The scenario file is used to specify SMAC-specific parameters. An example is:

```
pcs-file = clojush.pcs
runObj = QUALITY
cutoffTime = 3600
wallclock-limit = 604800
deterministic = 0
algo = ./run-clojush.py
use-instances = false

cli-log-all-calls = true
```

This tells SMAC that:

* The PCS file is `clojush.pcs`.
* The object of the runs is "QUALITY", with the other option being "RUNTIME". If it's set to "QUALITY" then SMAC tries to minimize the quality value returned by the go-between script; if it's set to "RUNTIME" then SMAC tries to minimize the runtime of your search algorithm. **NOTE** We used quality in the summer, 2016, runs, but it seems reasonable to try using runtime instead. If a run fails it will use the entire hour (or whatever) allocated to it, and successful runs will use less time. This would provide a gradient on the successful runs that would favor faster successes, which seems interesting and useful. To do this, however, would require modifying the "go-between" to collect and return to SMAC the runtime of the search process (e.g., Clojush run).
* The `cutoffTime` is one hour (3600 seconds), which means that any run that takes longer than an hour will receive a very large (i.e., very bad) quality value.
* The `wallclock-limit` is one week (604800 seconds), which is how long SMAC will explore the parameter space by trying new runs.
* `deterministic = 0` indicates that the underlying search algorithm (in our case Clojush) is _not_ deterministic, i.e., it may return different results from different runs with the same set of parameters. This tells SMAC that it needs to try the same parameters multiple times to get an idea of the distribution of behaviors. `deterministic = 1` would indicate that the algorithm is deterministic.
* `algo = ./run-clojush.py` specifies that the "go-between" script is `./run-clojush.py`. This script is the "glue" between SMAC and the underlying search algorithm (Clojush in our case) and is described more in the next section.
* `use-instances = false` says that we're running SMAC on a _single_ problem (or problem instance). If we wanted SMAC to optimize over a set of different problems, then we would set this to `true` and specify the problems in an `instance_file`.
* `cli-log-all-calls = true` just says that we want to log information on all the calls that are made. This is useful when analyzing the results after SMAC is finished.

### Python go-between script

This is the complicated part. Because SMAC doesn't know anything about your search algorithm (Clojush in our case), and your search algorithm doesn't know anything about SMAC, there needs to be some kind of "go-between" script that joins them up. This can be written in any programming language you like; the example provided with SMAC was in Python, and I just hacked that to generate the `run-clojush.py` script included in this repository.

SMAC will call the script specifying values of parmeters as command line arguments. If, for example, we want SMAC to run Clojush with a population size of 250 then it would include the command line arguments `-popsize 250` when it calls the go-between script. The script needs to collect those parameter values and pass them along to the search program. In the case Clojush this involves mapping them to Clojush command line parameters such as `:population-size 250`. (This is ugly and could made better by using more similar parameter names.)

The script then needs to construct the call to the search algorithm that uses all these parameters. At the moment this uses a uberjar created with `lein` to run Clojush, followed by all the necessary command line arguments specifying the parameter values.

This call, however, is preceded by `runsolver`, which is used to limit time the Clojush run will be allowed to execute before termination. This uses `runsolver`'s `-W` flag to specify the maximum amount of wallclock time the process will be allowed to use before `runsolver` kills it.

When the Clojush finishes (or is killed by `runsolver`) the script searches through the `stdout` of the process for the word `SUCCESS`, which would indicate that the Clojush run succeeded in evolving a program that passed all the training tests. The script then passes the score 0 back to SMAC if the run succeeded, and the score 1 if it didn't.

### Weird odds and ends

In the current script I limit the maximimum individual evaluations to 300,000 like in @thelmuth's dissertation runs that used population size of 1,000 and 300 generations. To keep the number of evaluations at or below that, I let SMAC modify the population size, and set the number of genrations to be `300,000/popsize`.

I set up SMAC to choose genetic operator probabilities in the range [0, 1]. In almost cases, however, these probabilities will not add up to 1 as required by Clojush. So I normalize them by adding them together and dividing each by the sum; this ensures that the new normalized values all add to 1.

At the moment we're using copies of the `scenario.txt` file for different problems, each of which passes a different problem as a command line argument to the `run-clojush.py` script. This seems kinda ugly, but we're not sure how to do it more cleanly.

Currently the `run-clojush.py` script assumes `runsolver` is in the same directory as it, or a link to `runsolver` is in that directory. If we installed `runsolver` more "properly" (e.g., in `/usr/local/bin`) we'd just need to make sure that was in the path and we wouldn't have to worry about it.

## RUN SMAC!

If all this is set up and working, you can run SMAC with something like:

```
./smac --scenario-file scenario-regression.txt
```

where this assumes the `smac` executable (or a link to it) is in the same directory as the scenario file. This will create a `smac-output` directory if one doesn't exist, and create a `scenario-regression` (or whatever, based on the name of your scenario file) directory in that. SMAC generates a lot of output files in that directory, as well as generating a lot of output to `stdout`. Since SMAC runs often need to go for hours or days, you probably want to either use a tool like `screen` or `tmux` to allow you to detach from the terminal; or redirect all the output to  file, run the process in the background, and use something like `nohup` to make sure that logging out doesn't kill your process.

## TO-DOs

- [ ] The Python script is a fairly ugly hack and ought to be refactored.
- [ ] I should write up something about using `fanova` to analyze the results.
- [ ] I should probably write up something about how to read the stuff in the output directories.
