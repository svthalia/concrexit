import subprocess
import threading


def PopenAndCall(onExit, *popenArgs, **popenKWArgs):
    """Run a subprocess.Popen, and then call the function onExit when the subprocess completes.

    Use it exactly the way you'd normally use subprocess.Popen, except include
    a callable to execute as the first argument. onExit is a callable object,
    and *popenArgs and **popenKWArgs are simply passed up to subprocess.Popen.
    """

    def runInThread(onExit, popenArgs, popenKWArgs):
        with subprocess.Popen(*popenArgs, **popenKWArgs) as proc:
            proc.wait()
        onExit()

    thread = threading.Thread(target=runInThread, args=(onExit, popenArgs, popenKWArgs))
    thread.start()

    return thread  # returns immediately after the thread starts
