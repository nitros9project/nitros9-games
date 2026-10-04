* Private control state. The caller supplies 8192 bytes of workspace in X:
* 2048 three-byte dictionary entries, followed by a 2048-byte string stack.
lzwbase             rmb       2
lzwwork             rmb       2
lzwnext             rmb       2
lzwthreshold        rmb       2
lzwprevious         rmb       2
lzwcurrent          rmb       2
lzwchain            rmb       2
lzwtop              rmb       2
lzwcode             rmb       2
lzwweight           rmb       2
lzwexpected         rmb       2
lzwproduced         rmb       2
lzwwidth            rmb       1
lzwbyte             rmb       1
lzwbits             rmb       1
lzwcount            rmb       1
lzwhasprevious      rmb       1
lzwfirst            rmb       1
lzwpreviousfirst    rmb       1
lzwerror            rmb       1
