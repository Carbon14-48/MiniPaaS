/*
 * webshells.yara
 * Detects web shells and server-side backdoor scripts.
 * Targets: PHP, JSP, ASP, Python backdoors.
 */

rule php_eval_base64_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "PHP webshell using eval(base64_decode()) obfuscation"
        severity = "CRITICAL"
        category = "webshell"
    strings:
        $s1 = "eval(base64_decode(" nocase
        $s2 = "eval(gzinflate(base64_decode(" nocase
        $s3 = "eval(base64_decode(gzinflate(" nocase
        $s4 = "str_rot13(base64_decode(" nocase
        $s5 = "assert(base64_decode(" nocase
        $s6 = "preg_replace.*/e.*base64" nocase
    condition:
        1 of them
}

rule php_system_exec_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "PHP backdoor using system/exec/shell_exec"
        severity = "CRITICAL"
        category = "webshell"
    strings:
        $s1 = "system(" nocase
        $s2 = "shell_exec(" nocase
        $s3 = "exec(" nocase
        $s4 = "passthru(" nocase
        $s5 = "popen(" nocase
        $s6 = "proc_open(" nocase
        $cmd = /\$\w+\s*=\s*\$_GET/ nocase
    condition:
        2 of them
}

rule c99_r57_webshell_family {
    meta:
        author = "MiniPaaS Security Team"
        description = "Detects c99, r57, and similar known PHP backdoor families"
        severity = "CRITICAL"
        category = "webshell"
    strings:
        $s1 = "c99shell" nocase
        $s2 = "r57shell" nocase
        $s3 = "wso" nocase
        $s4 = "webadmin" nocase
        $s5 = "PhpSpy" nocase
        $s6 = "b374k" nocase
    condition:
        1 of them
}

rule jsp_reverse_shell {
    meta:
        author = "MiniPaaS Security Team"
        description = "JSP backdoor with command execution"
        severity = "CRITICAL"
        category = "webshell"
    strings:
        $s1 = "Runtime.getRuntime().exec(" ascii
        $s2 = "Process p = Runtime" ascii
        $s3 = "jsp/backdoor" nocase
        $s4 = "cmd.exe" ascii
    condition:
        1 of them and $s1
}

rule python_flask_backdoor {
    meta:
        author = "MiniPaaS Security Team"
        description = "Python Flask application with debug backdoor"
        severity = "HIGH"
        category = "webshell"
    strings:
        $s1 = "app.run(debug=True" nocase
        $s2 = "debug=True" nocase
        $pin = "PIN" nocase
    condition:
        $s1 and $pin
}

rule python_webshell_eval {
    meta:
        author = "MiniPaaS Security Team"
        description = "Python webshell using eval/exec with user input"
        severity = "CRITICAL"
        category = "webshell"
    strings:
        $s1 = /eval\s*\(\s*request/ nocase
        $s2 = /exec\s*\(\s*request/ nocase
        $s3 = "subprocess.call" nocase
        $s4 = "os.system" nocase
        $s5 = /eval\s*\(\s*os\.popen/ nocase
    condition:
        1 of ($s1, $s2) and (2 of them)
}

rule asp_net_backdoor {
    meta:
        author = "MiniPaaS Security Team"
        description = "ASP.NET command execution backdoor"
        severity = "CRITICAL"
        category = "webshell"
    strings:
        $s1 = "Process.Start" ascii
        $s2 = "Request[" ascii
    condition:
        $s1 and $s2
}

rule encoded_command_obfuscation {
    meta:
        author = "MiniPaaS Security Team"
        description = "Obfuscated commands commonly used in webshells"
        severity = "HIGH"
        category = "webshell"
    strings:
        $s1 = /chr\s*\(\s*\d+\s*\)\s*\.\s*chr/ nocase
        $s2 = /\\\\x[0-9a-f]{2}/ ascii
        $s3 = "from_char_code" nocase
        $s4 = /base64_decode\s*\(/ nocase
    condition:
        1 of them
}
