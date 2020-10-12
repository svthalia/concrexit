import threading
import subprocess


def PopenAndCall(onExit, *popenArgs, **popenKWArgs):
    """
    Runs a subprocess.Popen, and then calls the function onExit when the
    subprocess completes.

    Use it exactly the way you'd normally use subprocess.Popen, except include
    a callable to execute as the first argument. onExit is a callable object,
    and *popenArgs and **popenKWArgs are simply passed up to subprocess.Popen.
    """

    def runInThread(onExit, popenArgs, popenKWArgs):
        proc = subprocess.Popen(*popenArgs, **popenKWArgs)
        proc.wait()
        onExit()

    thread = threading.Thread(target=runInThread, args=(onExit, popenArgs, popenKWArgs))
    thread.start()

    return thread  # returns immediately after the thread starts
