import pytest

import select
import re
from time import sleep, time
from pexpect.exceptions import EOF, TIMEOUT

def _expect(conn, list, timeout=-1):
    
    conn = conn
    re = None
    list = list[:]
    indices = range(len(list))

    for i in indices:
        if not hasattr(list[i], "search"):
            if not re: import re
            list[i] = re.compile(list[i])

    content = b''

    while True: 
        try: 
            txt = conn.read_nonblocking(conn.maxread, timeout)
            content += txt
            for i in indices:
                    m = list[i].search(content)
                    if m:
                        e = m.end()
                        text = content[:e]
                        return (i, m, text)

            if conn.delayafterread is not None:
                    sleep(conn.delayafterread)


        except TIMEOUT:   ## Remote-Shell EOF
            break 
        except EOF:       ## Local-Shell EOF
            break

    return (-1, None, content)

@pytest.mark.skip
def test_pexpect_nonblocking_method():
    import pexpect
    prompt_pattern = r'\S+@\S+:\S+\$\s$'

    prompt_pattern = r'\S+@\S+:\S+\$\s$'
    iosxr_prompt = r'\S+/\d/(RSP|RP)\d/CPU\d:\S+#$'

    p = pexpect.spawn('ssh vlab-vpn')
    (ridx, match, res) = _expect(p, [prompt_pattern.encode()])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('ssh -l vradmin 172.17.0.9\n'.encode())
    (ridx, match, res) = _expect(p, [r'(?i)password:'.encode()])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('cisco1234\n'.encode())
    (ridx, match, res) = _expect(p, [iosxr_prompt.encode()])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('terminal length 0\n'.encode())
    p.send('show bgp all all\n'.encode())
    (ridx, match, res) = _expect(p, [iosxr_prompt.encode()])
    print(res.decode('utf-8'))
    p.send('exit\n'.encode())
    p.close()


@pytest.mark.skip
def test_pexpect_expect_method():
    import pexpect
    from pexpect.exceptions import EOF, TIMEOUT

    prompt_pattern = r'\S+@\S+:\S+\$\s$'
    iosxr_prompt = r'\S+/\d/(RSP|RP)\d/CPU\d:\S+#$'

    p = pexpect.spawn('ssh vlab-vpn')
    p.expect([prompt_pattern.encode()])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('ssh -l vradmin 172.17.0.9\n'.encode())
    p.expect([r'(?i)password:'])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('cisco1234\n'.encode())
    p.expect([iosxr_prompt.encode()])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('terminal length 0\n'.encode())
    p.send('show bgp all all\n'.encode())
    p.expect([iosxr_prompt.encode()], timeout=1000)
    print(p.before.decode('utf-8'))
    p.send('exit\n'.encode())
    p.close()

@pytest.mark.skip
def test_sshpass_and_ssh():
    import os
    
    stream = os.popen('sshpass -p "cisco1234" ssh -o ProxyCommand="ssh -W %h:%p -q vlab-vpn" -l vradmin 172.17.0.9 "show bgp all all"')
    output = stream.read()
    print(output)


def read_until(match, conn, timeout=None):

    RETRY_OPEN = 3  # number of attempts to open TTY
    RETRY_BACKOFF = 2  # seconds to wait between retries
    MAX_BUFFER = 65535
    READ_PROMPT_DELAY = 10.0
    RECVSZ = 1024

    _ssh = conn
    rxb = ''.encode()
    timeout = time() + READ_PROMPT_DELAY
    
    while time() < timeout:
        sleep(0.1)
        rd, _, _ = select.select([_ssh], [], [], 0.1)
        sleep(0.05)
        if rd:
            rxb += _ssh.recv(MAX_BUFFER)
            if re.search(match, rxb):
                return rxb

            timeout = time() + READ_PROMPT_DELAY

def write(content, conn):
    """ write content + <ENTER> """
    _ssh = conn
    #logging.debug('Write: %s' % content)
    _ssh.sendall(f'{content}\n'.encode())

@pytest.mark.skip   
def test_paramiko():
    import paramiko
 
    IOSXR_PROMPT = r'\S+/\d/(RSP|RP)\d/CPU\d:\S+#$'

    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sock = paramiko.proxy.ProxyCommand('ssh -W 172.17.0.9:22 -q vlab-vpn')
    ssh_client.connect(hostname='172.17.0.9',
                       port=22,
                       username='vradmin',
                       password='cisco1234',
                       look_for_keys=False,
                       sock=sock
                       )
    ssh_shell = ssh_client.invoke_shell()
    output = read_until(IOSXR_PROMPT.encode(), ssh_shell)
    write('terminal length 0', ssh_shell)
    output = read_until(IOSXR_PROMPT.encode(), ssh_shell)
    write('show platform', ssh_shell)
    output = read_until(IOSXR_PROMPT.encode(), ssh_shell)
    print(output.decode('utf-8'))
    write('show version', ssh_shell)
    output = read_until(IOSXR_PROMPT.encode(), ssh_shell)
    print(output.decode('utf-8'))
    write('show running-config', ssh_shell)
    output = read_until(IOSXR_PROMPT.encode(), ssh_shell)
    print(output.decode('utf-8'))
    write('show users', ssh_shell)
    output = read_until(IOSXR_PROMPT.encode(), ssh_shell)
    print(output.decode('utf-8'))
    #ssh_shell.close()

#@pytest.mark.skip
def test_pyATS():
    from pyats.topology import loader
    from unicon import Connection
    proxy_conn = Connection(hostname='vlab',
                    start=['ssh vlab-vpn'],
                    os='linux',
                    log_stdout=False,
                    learn_hostname=True)

    ios_xr = Connection(hostname='cx-iosxr',
                    start=['ssh -o StrictHostKeyChecking=no 172.17.0.9'],
                    os='iosxr',
                    credentials={'default': {'username': 'vradmin', 'password': 'cisco1234'}},
                    log_stdout=False,
                    init_exec_commands=['terminal length 0'], 
                    init_config_commands=[],
                    proxy_connections=[proxy_conn])
    
    ios_xr.connect()
    print(ios_xr.execute('show bgp all all', timeout=2000, search_size=0))
    #ios_xr.disconnect()

@pytest.mark.skip
def test_netmiko():
    from netmiko import ConnectHandler

    device = { 'device_type' : 'cisco_xr',
               'host' : 'cx-iosxr',
               'username' : 'vradmin',
               'password' : 'cisco1234',
               'ssh_config_file' : '/home/toyos/.ssh/config'
             }
    net_connect = ConnectHandler(**device)
    output = net_connect.send_command("show platform")
    print(output)
    output = net_connect.send_command("show version")
    print(output)
    output = net_connect.send_command("show running-config")
    print(output)
    output = net_connect.send_command("show users")
    print(output)
    #net_connect.disconnect()
   
@pytest.mark.skip   
def test_napalm():
    from napalm import get_network_driver
    import json
    driver = get_network_driver('iosxr')
    device = driver(hostname='cx-iosxr',
                    username='vradmin',
                    password='cisco1234',
                    optional_args={'ssh_config_file' : '/home/toyos/.ssh/config'}
                   )
    device.open()
    output = device.cli(['show platform'])
    print(json.dumps(output, indent=2))
    output = device.cli(['show version'])
    print(json.dumps(output, indent=2))
    output = device.get_config()
    print(output['running'])
    output = device.cli(['show users'])
    print(json.dumps(output, indent=2))
    #device.close()
