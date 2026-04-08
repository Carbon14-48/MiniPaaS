/*
 * reverse_shells.yara
 * Detects reverse shell payloads and shell spawn patterns.
 * These are used for post-exploitation remote access.
 */

rule bash_reverse_shell_classic {
    meta:
        author = "MiniPaaS Security Team"
        description = "Classic bash reverse shell with TCP redirection"
        severity = "CRITICAL"
        category = "reverse_shell"
    strings:
        $s1 = "bash -i" ascii
        $s2 = "&>/dev/tcp/" ascii
        $s3 = "/dev/tcp/" ascii
        $s4 = "0>&1" ascii
        $s5 = "1>&1" ascii
        $s6 = ">&1" ascii
    condition:
        $s1 and $s3
}

rule netcat_reverse_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "Netcat reverse shell patterns"
        severity = "CRITICAL"
        category = "reverse_shell"
    strings:
        $s1 = "nc -e" ascii
        $s2 = "nc -E" ascii
        $s3 = "nc -c" ascii
        $s4 = "/bin/nc" ascii
        $s5 = "nc.traditional" ascii
        $s6 = "nc.openbsd" ascii
        $s7 = "ncat" ascii
    condition:
        (1 of ($s1, $s2, $s3)) or (2 of ($s4, $s5, $s6, $s7))
}

rule python_reverse_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "Python-based reverse shell"
        severity = "CRITICAL"
        category = "reverse_shell"
    strings:
        $s1 = "socket" ascii
        $s2 = "subprocess" ascii
        $s3 = "pty.spawn" ascii
        $s4 = "os.dup2" ascii
        $s5 = "/bin/sh" ascii
        $s6 = "connect(" ascii
    condition:
        $s1 and $s2 and (2 of ($s3, $s4, $s5, $s6))
}

rule php_reverse_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "PHP reverse shell payload"
        severity = "CRITICAL"
        category = "reverse_shell"
    strings:
        $s1 = "fsockopen(" ascii
        $s2 = "pfsockopen(" ascii
        $s3 = "/bin/sh" ascii
        $s4 = "socket_create" ascii
        $s5 = "$fp = fsockopen" ascii
    condition:
        (1 of ($s1, $s2, $s4)) and ($s3 or $s5)
}

rule ruby_reverse_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "Ruby reverse shell payload"
        severity = "CRITICAL"
        category = "reverse_shell"
    strings:
        $s1 = "TCPSocket.open" ascii
        $s2 = "spawn" ascii
        $s3 = "/bin/sh" ascii
    condition:
        $s1 and $s2 and $s3
}

rule perl_reverse_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "Perl reverse shell payload"
        severity = "CRITICAL"
        category = "reverse_shell"
    strings:
        $s1 = "Socket" ascii
        $s2 = "fork" ascii
        $s3 = "exec" ascii
        $s4 = "inet_aton" ascii
        $s5 = "perl -e" ascii
    condition:
        (1 of ($s1, $s4)) and (1 of ($s2, $s3, $s5))
}

rule socat_reverse_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "Socat reverse shell"
        severity = "CRITICAL"
        category = "reverse_shell"
    strings:
        $s1 = "socat" ascii
        $s2 = "EXEC:" ascii
        $s3 = "TCP:" ascii
        $s4 = "fork" ascii
    condition:
        $s1 and (2 of ($s2, $s3, $s4))
}

rule telnet_reverse_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "Telnet-based reverse shell"
        severity = "HIGH"
        category = "reverse_shell"
    strings:
        $s1 = "telnet" ascii
        $s2 = "/dev/tcp" ascii
        $s3 = "TF=/tmp/f" ascii
        $s4 = "/bin/bash -i" ascii
    condition:
        $s1 and (1 of ($s2, $s3, $s4))
}

rule meterpreter_payload {
    meta:
        author = "MiniPaaS Security Team"
        description = "Metasploit Meterpreter payload indicators"
        severity = "CRITICAL"
        category = "reverse_shell"
    strings:
        $s1 = "meterpreter" nocase
        $s2 = "METERPRETER" ascii
        $s3 = "shell_reverse_tcp" ascii
        $s4 = "windows/meterpreter" ascii
        $s5 = "linux/x86/meterpreter" ascii
    condition:
        1 of them
}

rule interactive_shell_detection {
    meta:
        author = "MiniPaaS Security Team"
        description = "Non-interactive shell spawned in suspicious context"
        severity = "MEDIUM"
        category = "reverse_shell"
    strings:
        $s1 = "/dev/null" ascii
        $s2 = "2>&1" ascii
        $s3 = ">/dev/null" ascii
        $s4 = "nohup" ascii
        $s5 = "disown" ascii
    condition:
        2 of them
}
