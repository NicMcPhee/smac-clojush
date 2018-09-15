#!/usr/bin/python
import sys
import os
import signal
import string
from subprocess import Popen, PIPE
import subprocess
import re

# For black box function optimization, we can ignore the first 5 arguments.
# The remaining arguments specify parameters using this format: -name value

popsize = 0
parent_selection = '":lexicase"'
alt_prob = 0.2
uni_mut_prob = 0.2
uni_close_mut = 0.1
alt_mut = 0.5
alt_rate = 0.01
alignment_dev = 10
uni_mut_rate = 0.01

problem = sys.argv[1]

wallclock_limit = float(sys.argv[4])
seed = int(sys.argv[6])

for i in range(len(sys.argv)-1):
    if (sys.argv[i] == '-popsize'):
        popsize = int(sys.argv[i+1])
    elif (sys.argv[i] == '-selection'):
        parent_selection = sys.argv[i+1]
    elif(sys.argv[i] == '-alt_prob'):
        alt_prob = float(sys.argv[i+1])
    elif(sys.argv[i] == '-uni_mut_prob'):
        uni_mut_prob = float(sys.argv[i+1])
    elif(sys.argv[i] == '-uni_close_mut'):
        uni_close_mut = float(sys.argv[i+1])
    elif(sys.argv[i] == '-alt_mut'):
        alt_mut = float(sys.argv[i+1])
    elif(sys.argv[i] == '-alt_rate'):
        alt_rate = float(sys.argv[i+1])
    elif(sys.argv[i] == '-alignment_dev'):
        alignment_dev = int(sys.argv[i+1])
    elif(sys.argv[i] == '-uni_mut_rate'):
        uni_mut_rate = float(sys.argv[i+1])

gen_prob_total = alt_prob + uni_mut_prob + uni_close_mut + alt_mut
# If the probabilities all add up to 0 (i.e., they are all 0), then
# we return a "failed" score and exit.
if gen_prob_total == 0:
    score = 1
    print "Result for SMAC: SUCCESS, 0, 0, %d, 0" % score
    sys.exit()
else:
    alt_prob = alt_prob / gen_prob_total
    uni_mut_prob = uni_mut_prob / gen_prob_total
    uni_close_mut = uni_close_mut / gen_prob_total
    alt_mut = alt_mut / gen_prob_total

# The max evals used in @thelmuth's dissertation work.
max_evaluations = 1000 * 300
num_generations = int(max_evaluations/popsize)

arg_dict = {}
arg_dict[":max-generations"] = num_generations
arg_dict[":population-size"] = popsize
arg_dict[":parent-selection"] = parent_selection
arg_dict[":genetic-operator-probabilities"] = '\"{:alternation %f :uniform-mutation %f :uniform-close-mutation %f [:alternation :uniform-mutation] %f}\"' % (alt_prob, uni_mut_prob, uni_close_mut, alt_mut)
arg_dict[":alternation-rate"] = alt_rate
arg_dict[":alignment-deviation"] = alignment_dev
arg_dict[":uniform-mutation-rate"] = uni_mut_rate

uberjar = "clojush-standalone.jar"
runsolver_time_file = "/tmp/smac_runsolver_time_" + str(seed) + ".txt"
command = ["./runsolver", "-v", runsolver_time_file, "-C", str(wallclock_limit), "java", "-jar", uberjar, problem]
for key in arg_dict:
    command = command + [key, str(arg_dict[key])]

sys.stderr.write(str(command) + "\n")

io = Popen(' '.join(command), stdout=PIPE, shell=True)
(stdout_, stderr_) = io.communicate()

score = 1
lines = stdout_.splitlines()
for line in lines:
    m = re.search("SUCCESS", line)
    if m:
        score = 0

time = 1000000
with open(runsolver_time_file) as f:
    for line in f.read().splitlines():
        m = re.search("CPUTIME=(\\d+\\.\\d+)", line)
        if m:
            time = float(m.group(1))
if time > wallclock_limit:
    time = wallclock_limit

print "Result for SMAC: SUCCESS, %f, 0, %d, 0" % (time, score)
