import socket
import requests
import time

host = None
session = None
settings = None


def setSettings(s):
    global settings
    settings = s


def httpDefaultSettings():
    return dict(
        hostname='epit.local',
        requests_interval=0.05,
    )


def startSession():
    global session
    session = requests.Session()


def sendRequest(request, requestType='GET', data=None):
    # print('request: ' + host + request)
    global host, session, settings
    if host is None:
        hostname = settings.http.hostname
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            fault = f"Device not found on the network by hostname: {hostname}"
            raise Exception(fault)
        print('printer ip:', ip)
        host = 'http://' + ip

    if session is None:
        startSession()

    response = None
    i = 0
    while True:
        try:
            i += 1
            if requestType == 'POST':
                response = session.post(
                    host + request,
                    data=data,
                    timeout=1,
                    headers={'Content-Length': str(len(data))},
                )
            else:
                response = session.get(
                    host + request,
                    timeout=1,
                )
        except requests.exceptions.Timeout:
            print('The request timed out')
            if i > 5:
                raise requests.exceptions.Timeout
        else:
            return response


def fileDownload(filename):
    response = sendRequest(f'/rr_download?name={filename}')
    if response.status_code != requests.codes['ok']:
        raise Exception(f'Failed to download file: {filename}')
    return response.content


def fileUpload(filename, b):
    response = sendRequest(
        f'/rr_upload?name={filename}',
        requestType='POST',
        data=b,
    )
    if response.json()['err'] > 0:
        raise Exception(f'Failed to upload file: {filename}')


def getObjectModel(entry):
    response = sendRequest(f'/rr_model?key={entry}')
    return response.json()['result']


def waitBusy():
    global settings
    while True:
        time.sleep(settings.http.requests_interval)
        response = sendRequest('/rr_model?key=state.status')
        status = response.json()['result']

        if status == 'idle':
            return


def getPos(axis):
    response = sendRequest(f'/rr_model?key=move.axes[{axis}].userPosition')
    return response.json()['result']


def getHomed(axis):
    response = sendRequest(f'/rr_model?key=move.axes[{axis}].homed')
    return response.json()['result']


def execGcode(gcode):
    try:
        response = sendRequest('/rr_reply')

        response = sendRequest(f'/rr_gcode?gcode={gcode}')
        print(
            'response1:',
            response.status_code,
            response.json(),
            response.json()['buff']
        )

        waitBusy()

        response = sendRequest('/rr_reply')
        print('response2:', response.status_code, response.content)
    except requests.exceptions.Timeout:
        print('The request timed out')
        raise Exception('The request timed out')

    return response.content.decode("utf-8").strip()
