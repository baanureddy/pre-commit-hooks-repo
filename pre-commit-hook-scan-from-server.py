import subprocess
import json
import sys
import time

import http.client

server_url = "chief-vigorously-seagull.ngrok-free.app"

def get_staged_diff():
    result = subprocess.run(['git', 'diff', '--cached'], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

def send_diff_to_server(diff):
    server_host = server_url
    endpoint = '/process_diff'
    conn = http.client.HTTPSConnection(server_host)
    headers = {'Content-type': 'application/json'}
    body = json.dumps({'diff': diff})
    
    try:
        conn.request('POST', endpoint, body, headers)
        response = conn.getresponse()
        data = response.read().decode()
        conn.close()
        if response.status == 200:
            return json.loads(data)
        elif response.status in [502,503,400,404]:
            print(f"Server returned {response.status} {response.reason}. Proceeding with commit with warning.")
            return None  # Return None to indicate a warning
        else:
            print("Failed to send diff to server.")
            sys.exit(1)
    
    except Exception as e:
        print(f"Exception occurred while sending diff to server: {str(e)}")
        sys.exit(1)

def wait_for_server_response(job_id):
    server_host = server_url
    endpoint = f'/check_status?job_id={job_id}'
    conn = http.client.HTTPSConnection(server_host)

    while True:
        conn.request('GET', endpoint)
        response = conn.getresponse()
        data = response.read().decode()
        if response.status == 200:
            status_data = json.loads(data)
            status = status_data.get('status')
            if status == 'complete':
                conn.close()
                return status_data
            elif status == 'failed':
                print("Server failed to process the diff.")
                conn.close()
                sys.exit(1)
        else:
            print("Error checking status with server.")
            conn.close()
            sys.exit(1)

        time.sleep(5)


'''def main():
    diff = get_staged_diff()
    server_response = send_diff_to_server(diff)
    
    if server_response is None:
        # Server returned 502 Bad Gateway, proceed with warning
        print("Warning: Server returned 502 Bad Gateway. Proceeding with commit.")
        sys.exit(0)  # Proceed with the commit

    result = wait_for_server_response(server_response['job_id'])
    
    if result.get('allow_commit', False):
        print("Server approved the commit.")
        sys.exit(0)
    else:
        for t in result.get('trufflehog_output', []):
            print(f"Secret found {t['ExtraData'], {t['Redacted']}}")
        print("Server rejected the commit.")
        sys.exit(1)'''

def main():
    diff = get_staged_diff()
    server_response = send_diff_to_server(diff)
    
    if server_response is None:
        # Handle the case where the server returned 400 or 502
        print("Proceeding with commit despite server error.")
        sys.exit(0)
    
    result = wait_for_server_response(server_response['job_id'])
    if result.get('allow_commit', False):
        print("Server approved the commit.")
        sys.exit(0)
    else:
        for t in result.get('trufflehog_output', []):
            if t.get('SourceID', 0) == 0 and t.get('SourceName', '') == '':
                # Skip empty results
                continue
            print(f"Secret found:")
            print(f"  Source ID: {t.get('SourceID', 'N/A')}")
            print(f"  Source Type: {t.get('SourceType', 'N/A')}")
            print(f"  Source Name: {t.get('SourceName', 'N/A')}")
            print(f"  Detector Type: {t.get('DetectorType', 'N/A')}")
            print(f"  Detector Name: {t.get('DetectorName', 'N/A')}")
            print(f"  Decoder Name: {t.get('DecoderName', 'N/A')}")
            print(f"  Verified: {t.get('Verified', 'N/A')}")
            print(f"  Raw: {t.get('Raw', 'N/A')}")
            print(f"  Redacted: {t.get('Redacted', 'N/A')}")
            print(f"  Extra Data: {t.get('ExtraData', 'N/A')}")
            print(f"  Structured Data: {t.get('StructuredData', 'N/A')}")
        print("Server rejected the commit.")
        sys.exit(1)


if __name__ == "__main__":
    main()

