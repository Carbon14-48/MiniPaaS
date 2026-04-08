/*
 * rootkits.yara
 * Detects rootkit artifacts, persistence mechanisms, and suspicious cron/systemd activity.
 * Rootkits use these techniques to maintain persistent access after initial compromise.
 */

rule cronjob_suspicious {
    meta:
        author = "MiniPaaS Security Team"
        description = "Suspicious cron job patterns"
        severity = "HIGH"
        category = "rootkit"
    strings:
        $s1 = "/etc/cron" ascii
        $s2 = "/var/spool/cron" ascii
        $s3 = "crontab -r" ascii
        $s4 = "crontab -l" ascii
        $wget = "wget" ascii
        $curl = "curl" ascii
        $sh = ".sh" ascii
    condition:
        (1 of ($s1, $s2)) and (1 of ($wget, $curl)) and $sh
}

rule systemd_service_injection {
    meta:
        author = "MiniPaaS Security Team"
        description = "Systemd service file creation for persistence"
        severity = "HIGH"
        category = "rootkit"
    strings:
        $s1 = "[Unit]" ascii
        $s2 = "[Service]" ascii
        $s3 = "Type=oneshot" ascii
        $s4 = "RemainAfterExit=yes" ascii
        $exec = "ExecStart=" ascii
        $http = "http" ascii
    condition:
        (3 of ($s1, $s2)) and $exec and $http
}

rule ssh_authorized_keys_injection {
    meta:
        author = "MiniPaaS Security Team"
        description = "SSH authorized_keys manipulation for persistent access"
        severity = "CRITICAL"
        category = "rootkit"
    strings:
        $s1 = "/root/.ssh/authorized_keys" ascii
        $s2 = "~/.ssh/authorized_keys" ascii
        $s3 = "ssh-rsa AAAA" ascii
        $s4 = "ssh-ed25519 AAAA" ascii
        $s5 = "ssh-dss AAAA" ascii
    condition:
        (1 of ($s1, $s2)) and (1 of ($s3, $s4, $s5))
}

rule ld_preload_rootkit {
    meta:
        author = "MiniPaaS Security Team"
        description = "LD_PRELOAD manipulation for hooking"
        severity = "HIGH"
        category = "rootkit"
    strings:
        $s1 = "LD_PRELOAD" ascii
        $s2 = "/etc/ld.so.preload" ascii
        $s3 = "ld.so.preload" ascii
        $s4 = ".so" ascii
    condition:
        (1 of ($s1, $s2, $s3)) and $s4
}

rule etc_passwd_modification {
    meta:
        author = "MiniPaaS Security Team"
        description = "/etc/passwd or /etc/shadow manipulation"
        severity = "CRITICAL"
        category = "rootkit"
    strings:
        $s1 = "/etc/passwd" ascii
        $s2 = "/etc/shadow" ascii
        $s3 = "root:" ascii
        $mod = "chmod" ascii
    condition:
        (1 of ($s1, $s2)) and ($s3 or $mod)
}

rule initd_rc_local_injection {
    meta:
        author = "MiniPaaS Security Team"
        description = "Init system script injection for persistence"
        severity = "HIGH"
        category = "rootkit"
    strings:
        $s1 = "/etc/init.d" ascii
        $s2 = "/etc/rc.local" ascii
        $s3 = "/etc/rc" ascii
        $s4 = "update-rc.d" ascii
        $net = "wget" ascii
        $shell = ".sh" ascii
    condition:
        (1 of ($s1, $s2, $s3)) and (1 of ($net, $shell))
}

rule suspicious_suid_binaries {
    meta:
        author = "MiniPaaS Security Team"
        description = "SUID binary installation for privilege escalation"
        severity = "HIGH"
        category = "rootkit"
    strings:
        $s1 = "chmod 4755" ascii
        $s2 = "chmod u+s" ascii
        $s3 = "chmod +s" ascii
        $s4 = "suid" ascii
        $s5 = "chown root:" ascii
    condition:
        1 of ($s1, $s2) and (1 of ($s4, $s5))
}

rule suspicious_environment_vars {
    meta:
        author = "MiniPaaS Security Team"
        description = "Suspicious environment variable manipulation"
        severity = "MEDIUM"
        category = "rootkit"
    strings:
        $s1 = "LD_PRELOAD" ascii
        $s2 = "LD_LIBRARY_PATH" ascii
        $s3 = "PATH=/tmp" ascii
        $s4 = "PATH=/var/tmp" ascii
        $s5 = "HISTFILE=/dev/null" ascii
        $s6 = "HISTSIZE=0" ascii
    condition:
        2 of them
}

rule hide_processes {
    meta:
        author = "MiniPaaS Security Team"
        description = "Process hiding techniques"
        severity = "HIGH"
        category = "rootkit"
    strings:
        $s1 = "/proc/" ascii
        $s2 = "/proc/self/status" ascii
        $s3 = "TracerPid" ascii
        $s4 = "Status:" ascii
    condition:
        2 of them
}

rule wireguard_vpn_persistence {
    meta:
        author = "MiniPaaS Security Team"
        description = "WireGuard or VPN installation for persistent access"
        severity = "HIGH"
        category = "rootkit"
    strings:
        $s1 = "[Interface]" ascii
        $s2 = "PrivateKey" ascii
        $s3 = "[Peer]" ascii
        $s4 = "wg0" ascii
        $s5 = "wg-quick" ascii
    condition:
        3 of them
}
