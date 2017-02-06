#!/usr/bin/python

import logging
import multiprocessing.dummy
import multiprocessing
import re
from subprocess import call, Popen, PIPE

log = logging.getLogger(__name__)

'''
multi is the module to call subprocess in minion host

Ping is a simple test to check if point to point nodes are connected

CLI Example:
.. code-block:: bash
sudo salt 'node' multi.ping_cmd <hostname>|<ip>
'''

def _all(func, hosts):
    '''
    Internal function that allow function to perform in all hosts
    '''
    all_instances = []
    # threads should likely scale with cores or interfaces
    cpus = multiprocessing.cpu_count()
    threads = 4 * cpus
    log.debug('multi._all cpus count={},  thread count={}'.format(cpus, threads))
    pool = multiprocessing.dummy.Pool(threads)
    for instance in pool.map(func, hosts):
        all_instances.append(instance)
    
    return all_instances


def ping_cmd(host):
    '''
    Ping a host with 1 package and return the result

    CLI Example:
    .. code-block:: bash
    sudo salt 'node' multi.ping_cmd <hostname>|<ip>
    '''
    cmd = [ "/usr/bin/ping", "-c1", "-q", "-W1", host ]
    log.debug('ping_cmd hostname={}'.format(host))

    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    proc.wait()
    return host, proc.returncode, proc.stdout.read(), proc.stderr.read()
    
def _summarize(results):
    '''
    Scan the results and summarize
    '''
    success = []
    failed = []
    errored = []
    avg = []
    for result in results:
        host, rc, out, err = result
        if rc == 0:
            success.append(host)
            rtt = re.match(r'.*rtt min/avg/max/mdev = \d+\.?\d+/(\d+\.?\d+)/', out, re.DOTALL)
            if rtt:
               avg.append({'avg':float(rtt.group(1)), 'host':host})
        if rc == 1:
            failed.append(host)
        if rc == 2:
            errored.append(host)

    log.debug('multi._summarize average={}'.format(avg))

    if avg:
        avg_sum = sum(i.get('avg') for i in avg) / len(avg)
    else:
        avg_sum = 0 
    
    msg = {}
    msg['succeeded'] = len(success)
    if failed:
        msg['failed'] = " ".join(failed)
    if errored:
        msg['errored'] = " ".join(errored)
    msg['avg'] = avg_sum
    return msg

def ping(*hosts):
    '''
    Ping a list of host with 1 package and return the result
    will be summarize by an internal function

    CLI Example:
    .. code-block:: bash
    sudo salt 'node' multi.ping <hostname>|<ip> <hostname>|<ip>....
    '''
    log.debug('ping hostlist={}'.format(list(hosts)))
    results = _all(ping_cmd, list(hosts))
    return _summarize(results)
