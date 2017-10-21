# Yanlin Zhu
# zhuy11

# Kaijian Zhong
# zhongk


import sys


class Process(object):
    def __init__(self, info):
        self.proc_id = info[0]
        self.arr_t, self.burst_t, self.num_bursts, self.io_t = map(int,
                                                                   info[1:])
        self.state = 'READY'
        self.end_t = -1
        self.original_num_bursts = self.num_bursts
        self.remaining_t = self.burst_t
        self.burst = 0
        self.wait = 0
        self.ready_begin_t = self.arr_t

    def stat_update(self, stat):
        stat[0].append(self.burst)
        self.burst = 0
        stat[1].append(self.wait)
        self.wait = 0
        stat[2].append(t - self.ready_begin_t + t_cs / 2)


# return the string of the current items in queue
def print_queue(ready_q, process=None):
    print_q = ready_q.copy()
    if process is not None:
        print_q.remove(process)
    if not print_q:
        return '[Q <empty>]'
    str_q = '[Q'
    for process in print_q:
        str_q += ' ' + process.proc_id
    return str_q + ']'


def arrive(processes, ready_q, t, srt=False, running_p=None, stat=None):
    for process in processes:
        if process.arr_t == t:
            ready_q.append(process)
            if srt:
                ready_q.sort(key=lambda x: x.remaining_t)
                if running_p is not None and \
                                process.remaining_t < running_p.remaining_t \
                        and running_p.state == 'RUNNING' and process == ready_q[
                    0]:
                    print('time {}ms: Process {} arrived '
                          'and will preempt {} {}'.format(t, process.proc_id,
                                                          running_p.proc_id,
                                                          print_queue(ready_q,
                                                                      process)))
                    stat[4] += 1
                else:
                    print('time {}ms: Process {} arrived and added to '
                          'ready queue {}'.format(t, process.proc_id
                                                  , print_queue(ready_q)))
            else:
                print('time {}ms: Process {} arrived and added to '
                      'ready queue {}'.format(t, process.proc_id
                                              , print_queue(ready_q)))


def io_arrive(io_q, ready_q, t, srt=False, running_p=None, stat=None):
    return_v = False
    while len(io_q) and io_q[0].end_t == t:
        process = io_q[0]
        process.state = 'READY'
        process.ready_begin_t = t
        ready_q.append(process)
        if srt:
            ready_q.sort(key=lambda x: x.remaining_t)
            io_q.pop(0)
            if running_p is not None and process.remaining_t < running_p.remaining_t and running_p.state == 'RUNNING':
                print('time {}ms: Process {} completed I/O '
                      'and will preempt {} {}'.format(t, process.proc_id,
                                                      running_p.proc_id,
                                                      print_queue(ready_q,
                                                                  process)))
                stat[4] += 1
            else:
                print('time {}ms: Process {} completed I/O;'
                      ' added to ready queue {}'.format(t, process.proc_id
                                                        , print_queue(ready_q)))
                return_v = True
        else:
            io_q.pop(0)
            print('time {}ms: Process {} completed I/O;'
                  ' added to ready queue {}'.format(t, process.proc_id
                                                    , print_queue(ready_q)))
        return_v = True
    return return_v


def finish_process(io_q, ready_q, t, running_p, t_cs, srt=False):
    def s(x):
        return 's' if x != 1 else ''

    running_p.remaining_t = running_p.burst_t

    print('time {}ms: Process {} completed a CPU burst; {} burst{}'
          ' to go {}'.format(t, running_p.proc_id, running_p.num_bursts,
                             s(running_p.num_bursts),
                             print_queue(ready_q)))
    if running_p.io_t != 0:
        io_q.append(running_p)
        running_p.end_t = int(t + running_p.io_t + t_cs / 2)
        io_q.sort(key=lambda x: x.end_t)
        print('time {}ms: Process {} switching out of CPU; will block'
              ' on I/O until time '
              '{}ms {}'.format(t, running_p.proc_id, running_p.end_t
                               , print_queue(ready_q)))
        running_p.state = 'BLOCKED'
    else:
        running_p.ready_begin_t = t
        running_p.state = 'READY'
        ready_q.append(running_p)
        if srt:
            ready_q.sort(key=lambda x: x.remaining_t)


def write_stat(output, status):
    output.write('-- average CPU burst time: {:.2f} ms\n'
                 '-- average wait time: {:.2f} ms\n'
                 '-- average turnaround time: {:.2f} ms\n'
                 '-- total number of context switches: {:d}\n'
                 '-- total number of preemptions: {:d}\n'.format(
        sum(status[0]) / len(status[0]),
        sum(status[1]) / len(status[1]),
        sum(status[2]) / len(status[2]),
        status[3], status[4]))


def update(ready_q, running_p):
    if running_p is not None and running_p.state == 'RUNNING':
        running_p.burst += 1
    for process in ready_q:
        process.wait += 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write('ERROR: Invalid arguments\nUSAGE: ./a.out <input-file> <stats-output-file>')
        exit(1)
    file_name = sys.argv[1]
    with open(file_name, 'r') as f:
        text = f.read().split('\n')

    output_name = sys.argv[2]
    outfile = open(output_name, 'w')

    processes = []
    processes_SRT = []
    processes_RR = []
    for i in text:
        i.strip()
        if len(i) and i[0] != '#':
            if len(i.split('|')) != 5:
                sys.stderr.write('ERROR: Invalid input file format')
                exit(1)
            processes.append(Process(i.split('|')))
            processes_SRT.append(Process(i.split('|')))
            processes_RR.append(Process(i.split('|')))

    ready_queue = []
    io_queue = []
    cpu_free = True
    t = 0
    t_cs = 8
    start_t = -1
    end_t = -1
    running_p = None
    t_slice = 70

    # [0:cpu_burst, 1:wait_time, 2:turn_around_time
    # 3:context_switches, 4: preemption]
    stat = [[], [], [], 0, 0]

    outfile.write('Algorithm FCFS\n')
    print('time {}ms: Simulator started for FCFS {}'.format(t, print_queue(
        ready_queue)))
    while len(processes):
        if start_t == t and running_p.state != "RUNNING":
            print('time {}ms: Process {} started'
                  ' using the CPU {}'.format(t, running_p.proc_id
                                             , print_queue(ready_queue)))
            running_p.state = 'RUNNING'

        if running_p is not None \
                and running_p.remaining_t == 0:
            running_p.stat_update(stat)
            running_p.num_bursts -= 1
            if running_p.num_bursts == 0:
                print('time {}ms: Process {}'
                      ' terminated {}'.format(t, running_p.proc_id
                                              , print_queue(ready_queue)))
                processes.remove(running_p)
            else:
                finish_process(io_queue, ready_queue, t, running_p, t_cs)

            io_arrive(io_queue, ready_queue, t)
            end_t = t + int(t_cs / 2)
        else:
            if io_arrive(io_queue, ready_queue, t):
                continue

        arrive(processes, ready_queue, t)

        if cpu_free and len(ready_queue):
            running_p = ready_queue[0]
            ready_queue.pop(0)
            stat[3] += 1
            cpu_free = False
            start_t = t + int(t_cs / 2)

        if end_t == t:
            cpu_free = True
            running_p = None
            end_t = -1
            continue

        if running_p is not None and running_p.state == 'RUNNING':
            running_p.remaining_t -= 1
        update(ready_queue, running_p)
        t += 1

    t += int(t_cs / 2) - 1

    print('time {}ms: Simulator ended for FCFS\n'.format(t))
    write_stat(outfile, stat)

    # start running SRT
    del ready_queue[:]
    del io_queue[:]
    cpu_free = True
    t = 0
    start_t = -1
    end_t = -1
    running_p = None

    # [0:cpu_burst, 1:wait_time, 2:turn_around_time
    # 3:context_switches, 4: preemption]
    del stat[:]
    stat = [[], [], [], 0, 0]
    outfile.write('Algorithm SRT\n')
    print('time {}ms: Simulator started for SRT {}'.format(t, print_queue(
        ready_queue)))

    while len(processes_SRT):
        if start_t == t and running_p.state != "RUNNING":
            if running_p.remaining_t == running_p.burst_t:
                print('time {}ms: Process {} started'
                      ' using the CPU {}'.format(t, running_p.proc_id
                                                 , print_queue(ready_queue)))
            else:
                print('time {}ms: Process {} started'
                      ' using the CPU with {}ms remaining {}'
                      .format(t, running_p.proc_id, running_p.remaining_t,
                              print_queue(ready_queue)))
            running_p.state = 'RUNNING'

        if running_p is not None \
                and running_p.remaining_t == 0:
            running_p.num_bursts -= 1
            running_p.stat_update(stat)
            if running_p.num_bursts == 0:
                print('time {}ms: Process {}'
                      ' terminated {}'.format(t, running_p.proc_id
                                              , print_queue(ready_queue)))
                processes_SRT.remove(running_p)
                running_p.remaining_t = -1
            else:
                finish_process(io_queue, ready_queue, t, running_p, t_cs, True)

            io_arrive(io_queue, ready_queue, t, True, running_p, stat)
            end_t = t + int(t_cs / 2)
            continue
        else:
            if io_arrive(io_queue, ready_queue, t, True, running_p, stat):
                continue

        arrive(processes_SRT, ready_queue, t, True, running_p, stat)

        if running_p is None and len(ready_queue):
            running_p = ready_queue.pop(0)
            stat[3] += 1
            start_t = t + int(t_cs / 2)

        if running_p is not None and len(ready_queue) \
                and ready_queue[
                    0].remaining_t < running_p.remaining_t and running_p.state == 'RUNNING':
            running_p.wait -= t_cs
            ready_queue.append(running_p)
            running_p.state = 'READY'
            ready_queue.sort(key=lambda x: x.remaining_t)
            end_t = t + int(t_cs / 2)

        if end_t == t:
            running_p = None
            end_t = -1
            continue

        if running_p is not None and running_p.state == 'RUNNING':
            running_p.remaining_t -= 1
        update(ready_queue, running_p)
        t += 1

    t += int(t_cs / 2)

    print('time {}ms: Simulator ended for SRT\n'.format(t))
    write_stat(outfile, stat)

    # start running RR
    del ready_queue[:]
    del io_queue[:]
    cpu_free = True
    t = 0
    start_t = -1
    slice_start = -1
    end_t = -1
    running_p = None
    preemption = True
    slice_start = -1

    # [0:cpu_burst, 1:wait_time, 2:turn_around_time
    # 3:context_switches, 4: preemption]
    del stat[:]
    stat = [[], [], [], 0, 0]

    outfile.write('Algorithm RR\n')
    print('time {}ms: Simulator started for RR {}'.format(t, print_queue(
        ready_queue)))
    while len(processes_RR):
        if start_t == t and running_p.state != "RUNNING":
            if running_p.remaining_t == running_p.burst_t and running_p.state != 'BLOCKED':
                print('time {}ms: Process {} started'
                      ' using the CPU {}'.format(t, running_p.proc_id
                                                 , print_queue(ready_queue)))
            elif preemption and running_p.remaining_t > 0 and running_p.state != 'BLOCKED':
                print('time {}ms: Process {} started'
                      ' using the CPU with {}ms remaining {}'
                      .format(t, running_p.proc_id, running_p.remaining_t,
                              print_queue(ready_queue)))
            running_p.state = 'RUNNING'

        # preemption for RR
        if (
                            t - start_t == t_slice or t - slice_start == t_slice) and running_p is not None:
            slice_start = t
            if len(
                    ready_queue) and running_p.remaining_t > 0 and running_p.state != 'BLOCKED':
                preemption = True
                stat[4] += 1
                print('time {}ms: Time slice expired; process {} '
                      'preempted with {}ms to go {}'.format(t,
                                                            running_p.proc_id,
                                                            running_p.remaining_t,
                                                            print_queue(
                                                                ready_queue)))
                running_p.state = 'READY'
                ready_queue.append(running_p)
                cpu_free = True
                start_t = t + int(t_cs / 2)
            elif running_p.remaining_t > 0:
                preemption = False
                print('time {}ms: Time slice expired; '
                      'no preemption because ready queue is empty {}'.format(t,
                                                                             print_queue(
                                                                                 ready_queue)))

        if running_p is not None \
                and running_p.remaining_t == 0:
            running_p.num_bursts -= 1
            running_p.stat_update(stat)
            if running_p.num_bursts == 0:
                print('time {}ms: Process {}'
                      ' terminated {}'.format(t, running_p.proc_id
                                              , print_queue(ready_queue)))
                processes_RR.remove(running_p)
            else:
                finish_process(io_queue, ready_queue, t, running_p, t_cs)

            io_arrive(io_queue, ready_queue, t)
            end_t = t + int(t_cs / 2)
        else:
            if io_arrive(io_queue, ready_queue, t):
                continue

        arrive(processes_RR, ready_queue, t)

        if cpu_free and len(ready_queue):
            running_p = ready_queue[0]
            ready_queue.pop(0)
            stat[3] += 1
            cpu_free = False
            if start_t > t:
                start_t = start_t + int(t_cs / 2)
            else:
                start_t = t + int(t_cs / 2)
            slice_start = start_t

        if end_t == t:
            cpu_free = True
            running_p = None
            end_t = -1
            continue

        if running_p is not None and running_p.state == 'RUNNING':
            running_p.remaining_t -= 1
        update(ready_queue, running_p)
        t += 1

    t += int(t_cs / 2) - 1

    print('time {}ms: Simulator ended for RR'.format(t))
    write_stat(outfile, stat)
