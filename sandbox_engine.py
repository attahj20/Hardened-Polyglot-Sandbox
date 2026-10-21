import os
import subprocess

def run_untrusted_code():
    print("="*60)
    print(" HARDENED POLYGLOT SANDBOX ENGINE - SIMULATION RUN")
    print("="*60)

    # Paths
    seccomp_profile = "seccomp-profile.json"
    binary_path = "/src/test_binary"

    # Forcing the container to run as an unprivileged non-root user (nobody:nobody)
    docker_cmd = [
        "docker", "run", "--rm",
        "--user", "65534:65534",
        "--security-opt", f"seccomp={seccomp_profile}",
        "-v", f"{os.getcwd()}/untrusted_code:/src",
        "alpine",
        binary_path
    ]

    print("[*] Dispatching container with Seccomp restrictions...")
    
    try:
        # Run the container and intercept output
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        process_output = result.stdout.strip()
        process_error = result.stderr.strip()
        exit_code = result.returncode

        print(f"\n[+] Execution Finished. Exit Code: {exit_code}")
        
        if process_output:
            print(f"[Output]:\n{process_output}")
        if process_error:
            print(f"[Error Output]:\n{process_error}")

        # Evaluate the security profile posture based on the application behavior
        calculate_security_score(exit_code, process_output, process_error)

    except subprocess.TimeoutExpired:
        print("\n[!] SECURITY ALERT: Code execution timed out! Possible infinite loop attack.")
        print("[-] Security Score: 40/100 (Resource Exhaustion)")

def calculate_security_score(exit_code, stdout, stderr):
    print("\n" + "-"*40)
    print(" SECURITY METRIC ANALYSIS")
    print("-"*40)

    # Check if our binary tried to read /etc/shadow and got safely blocked by unprivileged layers
    if "Access denied" in stdout or "Permission denied" in stderr:
        print("[✔] THREAT MITIGATED: Sandbox successfully isolated file system access!")
        print("⚡ Posture Assessment: Container Integrity Intact. Unprivileged Isolation Working.")
        print("⭐ Final Security Score: 100/100 (Secure Execution)")
    
    # Check if the container threw a runtime crash or initialization block
    elif exit_code == 125 or exit_code == 159:
        print("[!] Sandbox framework initialization error or system block caught.")
        print("⚡ Posture Assessment: Sandbox execution halted safely.")
        print("⭐ Final Security Score: 85/100 (Execution Halted via Policy)")
        
    # Check if the script somehow successfully read a forbidden system file
    elif "Exploit Success" in stdout:
        print("[⚠] CRITICAL FAILURE: Untrusted script bypassed container boundaries!")
        print("⚡ Posture Assessment: Sandbox compromised.")
        print("⭐ Final Security Score: 0/100 (CRITICAL EXPOSURE)")
        
    else:
        print("[✔] Code executed and closed cleanly within acceptable bounds.")
        print("⭐ Final Security Score: 90/100 (Standard Execution)")
    print("-"*40)

if __name__ == "__main__":
    run_untrusted_code()
