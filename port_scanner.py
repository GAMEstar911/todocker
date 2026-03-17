import socket
import sys
import argparse
from datetime import datetime

def scan_port(target_host, port):
    """
    Attempts to connect to a specific port on the target host.
    Returns True if the port is open, False otherwise.
    """
    try:
        # Create a new socket using IPv4 and TCP
        # AF_INET specifies the address family (IPv4)
        # SOCK_STREAM specifies the connection type (TCP)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Set a timeout for the connection attempt. If the port is filtered or
        # the server is slow, we don't want to wait forever.
        socket.setdefaulttimeout(1)

        # Attempt to connect to the target host and port
        result = sock.connect_ex((target_host, port))

        # If the result is 0, the connection was successful, meaning the port is open.
        if result == 0:
            return True
        else:
            return False
    except socket.error as e:
        # Handle potential errors like host not found
        print(f"Socket error: {e}")
        return False
    finally:
        # Always close the socket to free up resources
        sock.close()

def main():
    """
    Main function to parse arguments and run the port scan.
    """
    # --- Argument Parsing ---
    # This sets up the command-line interface for our tool.
    parser = argparse.ArgumentParser(description="A simple TCP port scanner.")
    parser.add_argument("target", help="The target host to scan (e.g., google.com or 8.8.8.8).")
    parser.add_argument("--ports", default="1-1024", help="Port range to scan (e.g., 80-100 or 22,80,443). Defaults to 1-1024.")
    args = parser.parse_args()

    target_host = args.target
    port_range_str = args.ports

    # --- Banner and Setup ---
    print("-" * 60)
    print(f"Scanning target: {target_host}")
    print(f"Time started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    try:
        # Resolve the target hostname to an IP address
        target_ip = socket.gethostbyname(target_host)
        print(f"Target IP: {target_ip}\n")
    except socket.gaierror:
        print(f"Error: Hostname '{target_host}' could not be resolved.")
        sys.exit()

    # --- Port Parsing and Scanning ---
    # This logic handles parsing the --ports argument.
    ports_to_scan = []
    if '-' in port_range_str:
        start, end = map(int, port_range_str.split('-'))
        ports_to_scan = range(start, end + 1)
    else:
        ports_to_scan = [int(p) for p in port_range_str.split(',')]

    open_ports = []
    for port in ports_to_scan:
        print(f"Scanning port {port}...", end='\r')
        if scan_port(target_ip, port):
            # Add padding with spaces to clear the rest of the line
            print(f"Port {port}: \033[92mOpen\033[0m" + " " * 20)
            open_ports.append(port)

    print("\n" + "-" * 60)
    print("Scan complete.")
    if open_ports:
        print(f"Open ports found: {', '.join(map(str, open_ports))}")
    else:
        print("No open ports found in the specified range.")
    print("-" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting... Scan interrupted by user.")
        sys.exit()