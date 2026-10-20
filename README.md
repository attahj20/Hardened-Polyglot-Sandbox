# Hardened-Polyglot-Sandbox
This profile uses a whitelist strategy (default action is SCMP_ACT_ERRNO, which blocks everything), and explicitly allows only safe, fundamental system calls required for basic execution and compilation (like memory allocation, writing to standard output, and exiting).
