import multiprocessing

bind = "0.0.0.0:8000"
loglevel = "info"
capture_output = True
timeout = 240

workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
