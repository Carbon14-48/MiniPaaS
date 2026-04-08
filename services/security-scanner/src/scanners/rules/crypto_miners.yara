/*
 * crypto_miners.yara
 * Detects cryptocurrency mining software and related artifacts in Docker images.
 * Targets: XMRig, cpuminer, nanominer, and other known miners.
 */

rule xmrig_binary {
    meta:
        author = "MiniPaaS Security Team"
        description = "Detects XMRig cryptocurrency miner"
        severity = "CRITICAL"
        category = "crypto_miner"
    strings:
        $s1 = "xmrig" nocase
        $s2 = "XMRig" ascii
        $s3 = "/xmrig/" ascii
        $s4 = "cryptonight" nocase
        $s5 = "stratum+tcp://" ascii
        $s6 = "nicehash" nocase
    condition:
        3 of them
}

rule xmrig_config_pattern {
    meta:
        author = "MiniPaaS Security Team"
        description = "XMRig configuration file with mining pool"
        severity = "CRITICAL"
        category = "crypto_miner"
    strings:
        $url1 = "stratum" ascii
        $url2 = ".nicehash.com" ascii
        $url3 = ".miningpoolhub.com" ascii
        $pool1 = "pool.supportxmr.com" ascii
        $pool2 = "cryptonight" ascii
        $wallet = / wallets* \{ /
    condition:
        2 of ($url*) and 1 of ($pool*)
}

rule cpuminer_binary {
    meta:
        author = "MiniPaaS Security Team"
        description = "Detects cpuminer (pooler) cryptocurrency miner"
        severity = "CRITICAL"
        category = "crypto_miner"
    strings:
        $s1 = "cpuminer" nocase
        $s2 = "pooler-cpuminer" ascii
        $s3 = "minerd" ascii
        $s4 = "-a sha256d" ascii
    condition:
        2 of them
}

rule crypto_miner_process {
    meta:
        author = "MiniPaaS Security Team"
        description = "Process name or path associated with crypto mining"
        severity = "HIGH"
        category = "crypto_miner"
    strings:
        $p1 = "/usr/bin/minerd" ascii
        $p2 = "/usr/local/bin/minerd" ascii
        $p3 = "/tmp/minerd" ascii
        $p4 = "/var/tmp/minerd" ascii
        $p5 = ".xmrig" ascii fullword
        $p6 = "cgminer" nocase
        $p7 = "bfgminer" nocase
    condition:
        any of them
}

rule cryptowallet_address_pattern {
    meta:
        author = "MiniPaaS Security Team"
        description = "Hardcoded cryptocurrency wallet addresses in files"
        severity = "MEDIUM"
        category = "crypto_miner"
    strings:
        // Bitcoin
        $btc1 = /[13][a-km-zA-HJ-NP-Z1-9]{25,34}/ fullword
        // Ethereum
        $eth1 = /0x[a-fA-F0-9]{40}/ fullword
        // Monero (longer, starts with 4)
        $xmr1 = /4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}/ fullword
    condition:
        any of them
}

rule stratum_protocol_strings {
    meta:
        author = "MiniPaaS Security Team"
        description = "Stratum mining protocol artifacts"
        severity = "HIGH"
        category = "crypto_miner"
    strings:
        $s1 = "mining.subscribe" ascii
        $s2 = "mining.authorize" ascii
        $s3 = "mining.submit" ascii
        $s4 = "stratum" ascii
        $s5 = "jsonrpc" ascii
    condition:
        3 of them
}

rule nanominer_binary {
    meta:
        author = "MiniPaaS Security Team"
        description = "Detects NanoMiner cryptocurrency miner"
        severity = "CRITICAL"
        category = "crypto_miner"
    strings:
        $s1 = "nanominer" nocase
        $s2 = "nicehashminer" nocase
        $s3 = "ethminer" nocase
        $s4 = "phoenixminer" nocase
    condition:
        1 of them
}
