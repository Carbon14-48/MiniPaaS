/*
 * container_escape.yara
 * Detects artifacts and techniques associated with container escape attempts.
 * These patterns indicate privilege escalation or escape from container isolation.
 */

rule docker_socket_escape {
    meta:
        author = "MiniPaaS Security Team"
        description = "Access to Docker socket for container escape"
        severity = "CRITICAL"
        category = "container_escape"
    strings:
        $s1 = "/var/run/docker.sock" ascii fullword
        $s2 = "docker.sock" ascii fullword
        $s3 = "docker://" ascii
        $s4 = "docker ps" ascii
        $s5 = "docker run" ascii
        $s6 = "docker exec" ascii
    condition:
        1 of them
}

rule nsenter_escape {
    meta:
        author = "MiniPaaS Security Team"
        description = "nsenter command for namespace escape"
        severity = "CRITICAL"
        category = "container_escape"
    strings:
        $s1 = "nsenter" ascii
        $s2 = "--target" ascii
        $s3 = "--mount" ascii
        $s4 = "--pid" ascii
    condition:
        $s1 and (1 of ($s2, $s3, $s4))
}

rule unshare_escape {
    meta:
        author = "MiniPaaS Security Team"
        description = "unshare command for creating new namespaces"
        severity = "HIGH"
        category = "container_escape"
    strings:
        $s1 = "unshare" ascii fullword
        $s2 = "--mount" ascii
        $s3 = "--pid" ascii
        $s4 = "--user" ascii
        $s5 = "--map-root-user" ascii
    condition:
        $s1 and (1 of ($s2, $s3, $s4, $s5))
}

rule cgroup_escape {
    meta:
        author = "MiniPaaS Security Team"
        description = "Cgroups-based container escape attempt"
        severity = "CRITICAL"
        category = "container_escape"
    strings:
        $s1 = "/proc/self/mountinfo" ascii
        $s2 = "cgroup" ascii
        $s3 = "release_agent" ascii
        $s4 = "notify_on_release" ascii
        $s5 = "/sys/fs/cgroup" ascii
    condition:
        3 of them
}

rule procfs_host_access {
    meta:
        author = "MiniPaaS Security Team"
        description = "Direct access to host /proc filesystem"
        severity = "HIGH"
        category = "container_escape"
    strings:
        $s1 = "/host/proc" ascii
        $s2 = "/host/sys" ascii
        $s3 = "/proc/1/root" ascii
        $s4 = "chroot" ascii
        $s5 = "/mnt/host" ascii
    condition:
        1 of them
}

rule capability_escalation {
    meta:
        author = "MiniPaaS Security Team"
        description = "Linux capability escalation attempt"
        severity = "CRITICAL"
        category = "container_escape"
    strings:
        $s1 = "CAP_SYS_ADMIN" ascii
        $s2 = "CAP_SYS_MODULE" ascii
        $s3 = "CAP_NET_RAW" ascii
        $s4 = "CAP_SYS_RAWIO" ascii
        $s5 = "setcap" ascii
        $s6 = "getpcaps" ascii
    condition:
        1 of them
}

rule mount_host_filesystem {
    meta:
        author = "MiniPaaS Security Team"
        description = "Attempt to mount host filesystem"
        severity = "CRITICAL"
        category = "container_escape"
    strings:
        $s1 = "mount --bind" ascii
        $s2 = "mount -o bind" ascii
        $s3 = "/host" ascii
        $s4 = "--privileged" ascii
        $s5 = "mount -t proc" ascii
        $s6 = "pivot_root" ascii
    condition:
        ($s1 or $s2 or $s3) and (1 of ($s4, $s5, $s6))
}

rule overlayfs_escape {
    meta:
        author = "MiniPaaS Security Team"
        description = "OverlayFS escape technique"
        severity = "HIGH"
        category = "container_escape"
    strings:
        $s1 = "overlayfs" ascii
        $s2 = "upperdir" ascii
        $s3 = "lowerdir" ascii
        $s4 = "/proc/1/exe" ascii
    condition:
        2 of them and $s4
}

rule sysbox_escape_artifacts {
    meta:
        author = "MiniPaaS Security Team"
        description = "Sysbox container runtime escape artifacts"
        severity = "HIGH"
        category = "container_escape"
    strings:
        $s1 = "sysbox" ascii
        $s2 = "/var/lib/sysbox" ascii
        $s3 = "SYSBOX" ascii
    condition:
        1 of them
}

rule proc_pid_exe_tampering {
    meta:
        author = "MiniPaaS Security Team"
        description = "Tampering with /proc/PID/exe symlink"
        severity = "CRITICAL"
        category = "container_escape"
    strings:
        $s1 = "/proc/self/exe" ascii
        $s2 = "/proc/1/exe" ascii
        $s3 = "readlink" ascii
        $s4 = "symlink" ascii
    condition:
        (1 of ($s1, $s2)) and (1 of ($s3, $s4))
}
