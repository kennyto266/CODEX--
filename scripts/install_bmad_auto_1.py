#!/usr/bin/env python3
"""Automated BMAD installation script"""

import subprocess
import time
import os

def run_bmad_install():
    """Run BMAD installation with automated responses"""

    # Start the installation process
    process = subprocess.Popen(
        ['node', 'BMAD-METHOD/tools/cli/bmad-cli.js', 'install'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    responses = [
        # Enter for default directory
        '\n',
        'Y\n',  # Confirm directory
        '1\n',  # Select modules (BMM)
        '\n',   # Accept default options
        'Y\n',  # Confirm installation
    ]

    response_idx = 0
    output_lines = []

    # Send responses when prompted
    while True:
        # Read output
        output = process.stdout.read(1)
        if output == '' and process.poll() is not None:
            break

        if output:
            output_lines.append(output)
            print(output, end='', flush=True)

            # Check if we're at a prompt
            if '?' in output and (output.endswith(' ') or output.endswith(':')):
                if response_idx < len(responses):
                    print(f"\n>>> Sending: {repr(responses[response_idx])}")
                    process.stdin.write(responses[response_idx])
                    process.stdin.flush()
                    response_idx += 1
                    time.sleep(0.1)

    # Wait for process to complete
    process.wait()
    return process.returncode

if __name__ == '__main__':
    print("Starting BMAD installation...")
    result = run_bmad_install()
    print(f"\nInstallation completed with return code: {result}")
