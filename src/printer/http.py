import socket
import requests
import time

host = None


def sendRequest(request):
    # print('request: ' + host + request)
    global host
    if host is None:
        ip = socket.gethostbyname('3d.local')
        # ip = socket.gethostbyname('EPIT3D')
        print('printer ip:', ip)
        host = 'http://' + ip

    response = None
    i = 0
    while True:
        try:
            i += 1
            response = requests.get(
                host + request,
                timeout=1,
            )
        except requests.exceptions.Timeout:
            print('The request timed out')
            if i > 5:
                raise requests.exceptions.Timeout
        else:
            return response


def fileUpload():
    pass


def getObjectModel(entry):
    response = sendRequest(f'/rr_model?key={entry}')
    return response.json()['result']


def waitBusy():
    while True:
        time.sleep(0.5)
        response = sendRequest('/rr_model?key=state.status')
        print('response:', response.status_code, response.content)
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
