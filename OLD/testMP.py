import time
from Queue import Empty
from multiprocessing import Queue, Process


def receiver(q):
    while 1:
        try:
            message = q.get_nowait()
            print 'receiver got', message
        except Empty:
            print 'nothing to receive, sleeping'
            time.sleep(5)


def sender(q):
    while 1:
        message = 'some message'
        q.put('some message')
        print 'sender sent', message
        time.sleep(3)

some_queue = Queue()

process_a = Process(
    target=receiver,
    args=(some_queue,)
)

process_b = Process(
    target=sender,
    args=(some_queue,)
)

process_a.start()
process_b.start()

print 'ctrl + c to exit'
try:
    while 1:
        time.sleep(1)
        print("*"*100)
except KeyboardInterrupt:
    pass

process_a.terminate()
process_b.terminate()

process_a.join()
process_b.join()
