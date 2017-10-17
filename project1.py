import sys


class Process(object):
    def __init__(self, info):
        self.proc_id = info[0]
        self.arr_t, self.burst_t, self.num_bursts, self.io_t = map(int,
                                                                   info[1:])
        self.state = 'READY'
        self.end_t = -1


def arrive(processes, ready_q, t):
    for process in processes:
        if process.arr_t == t:
            ready_q.append(process)
            print('time {}ms: Process {} arrived and added to '
                  'ready queue'.format(t, process.proc_id))


def io_arrive(io_q, ready_q, t):
    while len(io_q) and io_q[0].end_t == t:
        process = io_q[0]
        process.state = 'READY'
        ready_q.append(process)
        io_q.pop(0)
        print('time {}ms: Process {} completed I/O;'
              ' added to ready queue'.format(t, process.proc_id))


def finish_process(io_q, ready_q, t, running_p, t_cs):
    print('time {}ms: Process {} completed a CPU burst; {} bursts'
          ' to go'.format(t, running_p.proc_id, running_p.num_bursts))
    if running_p.io_t != 0:
        io_q.append(running_p)
        running_p.end_t = int(t + running_p.io_t + t_cs / 2)
        io_q.sort(key=lambda x: x.end_t)
        print('time {}ms: Process {} switching out of CPU; will block'
              ' on I/O until time '
              '{}ms'.format(t, running_p.proc_id, running_p.end_t))
        running_p.state = 'BLOCKED'
    else:
        running_p.state = 'READY'
        ready_q.append(running_p)


file_name = sys.argv[1]
with open(file_name, 'r') as f:
    text = f.read().split('\n')

processes = []
for i in text:
    i.strip()
    if len(i) and i[0] != '#':
        processes.append(Process(i.split('|')))

ready_queue = []
io_queue = []
cpu_free = True
t = 0
t_cs = 8
start_t = -1
end_t = -1
running_p = None

print('time {}ms: Simulator started for FCFS'.format(t))
while len(processes):
    arrive(processes, ready_queue, t)

    io_arrive(io_queue, ready_queue, t)

    if cpu_free and len(ready_queue):
        t += int(t_cs / 2)
        cpu_free = False
        running_p = ready_queue[0]
        ready_queue.pop(0)
        print('time {}ms: Process {} started'
              ' using the CPU'.format(t, running_p.proc_id))
        running_p.state = 'RUNNING'
        running_p.remaining_t = running_p.burst_t
        start_t = -1

    if running_p is not None \
            and running_p.remaining_t == 0:
        running_p.num_bursts -= 1
        if running_p.num_bursts == 0:
            print('time {}ms: Process {}'
                  ' terminated'.format(t, running_p.proc_id))
            processes.remove(running_p)
        else:
            finish_process(io_queue, ready_queue, t, running_p, t_cs)

        t += int(t_cs / 2)
        cpu_free = True
        running_p = None
        end_t = -1
        continue

    if running_p is not None:
        running_p.remaining_t -= 1
    t += 1

print('time {}ms: Simulator ended for FCFS'.format(t + int(t_cs / 2)))