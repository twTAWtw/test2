import pytest


def test_expect():
    import pexpect
    from pexpect.exceptions import EOF, TIMEOUT

    prompt_pattern = r'\S+@\S+:\S+\$\s$'
    iosxr_prompt = r'\S+/\d/(RSP|RP)\d/CPU\d:\S+#$'

    p = pexpect.spawn('ssh vlab-vpn')
    p.expect([prompt_pattern.encode()])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('ssh -l vagrant 198.18.1.1\n'.encode())
    p.expect([r'(?i)password:'])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('vagrant\n'.encode())
    p.expect([iosxr_prompt.encode()])
    #print(p.before.decode('utf-8') + p.after.decode('utf-8'))
    p.send('terminal length 0\n')
    p.send('show platform\n'.encode())
    p.expect([iosxr_prompt.encode()])
    print(p.before.decode('utf-8'))
    p.send('show version\n'.encode())
    p.expect([iosxr_prompt.encode()])
    print(p.before.decode('utf-8'))
    p.send('show running-config\n'.encode())
    p.expect([iosxr_prompt.encode()])
    print(p.before.decode('utf-8'))
    p.send('show users\n'.encode())
    p.expect([iosxr_prompt.encode()])
    print(p.before.decode('utf-8'))
    p.close()

def test_sshpass():
    import os
    
    stream = os.popen('sshpass -p "vagrant" ssh -o ProxyCommand="ssh -W %h:%p -q vlab-vpn" -l vagrant 198.18.1.1 "show platform"')
    output = stream.read()
    print(output)
    stream = os.popen('sshpass -p "vagrant" ssh -o ProxyCommand="ssh -W %h:%p -q vlab-vpn" -l vagrant 198.18.1.1 "show version"')
    output = stream.read()
    print(output)
    stream = os.popen('sshpass -p "vagrant" ssh -o ProxyCommand="ssh -W %h:%p -q vlab-vpn" -l vagrant 198.18.1.1 "show running-config"')
    output = stream.read()
    print(output)
    stream = os.popen('sshpass -p "vagrant" ssh -o ProxyCommand="ssh -W %h:%p -q vlab-vpn" -l vagrant 198.18.1.1 "show users"')
    output = stream.read()
    print(output)
