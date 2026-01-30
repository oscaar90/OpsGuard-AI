import subprocess
import sys

def run_connectivity_check(target_host):
    """
    Utility to verify latency against internal services.
    Sanitized implementation avoiding shell injection.
    """
    # FIX: Usar lista de argumentos evita la shell del sistema.
    # El sistema operativo pasa 'target_host' como argumento, no como comando.
    command = ["ping", "-c", "1", target_host]
    
    try:
        # shell=False es el default, pero lo omitimos explícitamente por claridad
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error checking {target_host}: {e.stderr}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python net_diag.py <hostname>")
        sys.exit(1)
    
    print(run_connectivity_check(sys.argv[1]))