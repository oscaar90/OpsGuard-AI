import subprocess
import sys

def run_connectivity_check(target_host):
    """
    Utility to verify latency against internal services.
    Currently used by the ops-dashboard.
    """
    # VULNERABILIDAD: Inyección de comandos directa
    command = f"ping -c 1 {target_host}"
    
    try:
        # El LLM debe detectar: Input no sanitizado + shell=True
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Error checking {target_host}: {e.output}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python net_diag.py <hostname>")
        sys.exit(1)
    
    print(run_connectivity_check(sys.argv[1]))# Trigger CI/CD execution check
